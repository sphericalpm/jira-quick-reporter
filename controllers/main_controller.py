from PyQt5.QtWidgets import QMessageBox
from jira import JIRAError

from main_window import MainWindow
from controllers.timelog_controller import TimeLogController
from controllers.workflow_controller import WorkflowController


DEFAULT_ISSUES_COUNT = 50


class MainController:
    def __init__(self, jira_client):
        self.jira_client = jira_client
        self.issues_count = 0

    def show(self):
        self.view = MainWindow(self)
        self.refresh_issue_list()
        self.view.show()

    def get_issue_list(self):
        issues_list = []
        issues = self.jira_client.get_issues(self.issues_count)
        current_issues_count = len(issues)
        self.issues_count += current_issues_count
        if current_issues_count < DEFAULT_ISSUES_COUNT:
            self.view.load_more_issues_btn.hide()
        else:
            self.view.load_more_issues_btn.show()

        # create list of issues
        for issue in issues:
            workflow = self.jira_client.client.transitions(issue)
            possible_workflow = {status['name']: status['id'] for status in workflow}
            issues_dict = dict(
                title=issue.fields.summary,
                key=issue.key,
                link=issue.permalink(),
                issue_obj=issue,
                workflow=possible_workflow
            )

            # if the task was logged
            if issue.fields.timetracking.raw:
                timetracking = issue.fields.timetracking
                issues_dict.update({
                    'estimated': getattr(timetracking, 'originalEstimate', '0m'),
                    'logged': getattr(timetracking, 'timeSpent', '0m'),
                    'remaining': getattr(timetracking, 'remainingEstimate', '0m'),
                })
            else:
                issues_dict.update({
                    'estimated': '0m',
                    'logged': '0m',
                    'remaining': '0m',
                })
            issues_list.append(issues_dict)
        return issues_list

    def refresh_issue_list(self, load_more=False):
        if not load_more:
            self.issues_count = 0
        issues_list = self.get_issue_list()
        self.view.show_issues_list(issues_list, load_more)

    def open_timelog_window(self, issue_key):
        time_log_controller = TimeLogController(
            self.jira_client,
            issue_key,
            self
        )
        time_log_controller.show()

    def change_workflow(self, workflow, issue_obj, status):
        status_id = workflow.get(status)

        if status_id and not status == 'Put on hold' and not status == 'Complete':
            self.workflow_controller = WorkflowController(self.jira_client, issue_obj, status, self)
            self.workflow_controller.show()
            return

        elif status == 'Put on hold':
            try:
                self.jira_client.client.transition_issue(
                        issue_obj,
                        transition=status_id
                    )
            except JIRAError as e:
                QMessageBox.about(self.view, 'Error', e.text)

        elif not status_id:  # selected already applied workflow
            pass

        self.refresh_issue_list()

    def get_possible_workflows(self, issue):
        current_workflow = issue['issue_obj'].fields.status
        possible_workflows = list(issue['workflow'].keys())

        if current_workflow.name != 'Backlog':  # when it's 'Backlog' status,
            # JIRA API provides possibility to change it to 'Return to backlog'.
            # Cause it's the same that we already have we won't show it one more time
            possible_workflows.insert(0, current_workflow.name)  # insert because of
            # setCurrentIndex() can have only positive value

        return possible_workflows
