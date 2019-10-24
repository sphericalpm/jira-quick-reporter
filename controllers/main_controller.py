import os

from PyQt5.QtWidgets import QMessageBox, QApplication
from PyQt5.QtCore import Qt
from jira import JIRAError

from config import LOG_TIME, DEFAULT_ISSUES_COUNT
from main_window import MainWindow

from controllers.workflow_controller import (
    WorkflowController,
    CompleteWorkflowController
)
from controllers.mixins import TimeLogMixin
from pomodoro_window import PomodoroWindow
from time_log_window import TimeLogWindow


class MainController(TimeLogMixin):
    def __init__(self, jira_client):
        self.jira_client = jira_client
        self.issues_count = 0
        self.pomodoro_view = None
        self.time_log_view = None

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

    def change_workflow(self, workflow, issue_obj, status):
        status_id = workflow.get(status)
        existing_estimate = self.jira_client.get_remaining_estimate(issue_obj)
        original_estimate = self.jira_client.get_original_estimate(issue_obj)
        assignee = issue_obj.fields.assignee.emailAddress

        if status_id:
            if status == 'Put on hold' or status == 'Select for development':
                # we do not need to open workflow window with detail information
                try:
                    QApplication.setOverrideCursor(Qt.WaitCursor)
                    self.jira_client.client.transition_issue(
                            issue_obj,
                            transition=status_id
                        )
                except JIRAError as e:
                    QMessageBox.about(self.view, 'Error', e.text)

                self.view.tray_icon.showMessage(
                    'Saving...',
                    'Please wait',
                    msecs=2000
                )
                QApplication.restoreOverrideCursor()
                self.refresh_issue_list()

            elif status == 'Complete' or status == 'Declare done':
                # open complete workflow window
                self.complete_workflow_controller = CompleteWorkflowController(
                    self.jira_client,
                    issue_obj,
                    status,
                    assignee,
                    self
                )
                self.complete_workflow_controller.show()
                self.complete_workflow_controller.view.set_existing_estimate(
                    existing_estimate,
                )

            else:
                self.workflow_controller = WorkflowController(
                    self.jira_client,
                    issue_obj,
                    status_id,
                    existing_estimate,
                    original_estimate,
                    assignee,
                    self
                )
                self.workflow_controller.show()

    def get_possible_workflows(self, issue):
        current_workflow = issue['issue_obj'].fields.status
        possible_workflows = list(issue['workflow'].keys())

        if current_workflow.name != 'Backlog':  # when it's 'Backlog' status,
            # JIRA API provides possibility to change it to 'Return to backlog'.
            # Cause it's the same that we already have we won't show it one more time
            possible_workflows.insert(0, current_workflow.name)  # insert because of
            # setCurrentIndex() can have only positive value

        return possible_workflows

    def open_pomodoro_window(self, issue_key, issue_title):
        if self.pomodoro_view:
            if self.pomodoro_view.issue_key == issue_key:
                self.pomodoro_view.show()
            else:
                QMessageBox.warning(None, 'Warning', 'Another task in progress now!')
            return
        self.pomodoro_view = PomodoroWindow(
            self, issue_key,
            issue_title,
            self.view.tray_icon
        )
        self.pomodoro_view.show()
        self.pomodoro_view.log_work_if_file_exists()

    def open_timelog_from_pomodoro(self, issue_key):
        params = [issue_key]
        if not os.path.exists(self.pomodoro_view.LOG_PATH):
            params.append('0m')
        else:
            with open(self.pomodoro_view.LOG_PATH, 'r') as log_file:
                try:
                    hours, minutes = log_file.readline().split(':')
                except ValueError:
                    hours = minutes = '0'
                if hours == '0':
                    params.append('{}m'.format(minutes))
                elif minutes == '0':
                    params.append('{}h'.format(hours))
                else:
                    params.append('{}h {}m'.format(hours, minutes))
        self.open_timelog_window(*params)

    def open_timelog_window(self, issue_key, time_spent=None):
        issue = self.jira_client.issue(issue_key)
        self.time_log_view = TimeLogWindow(
            issue_key,
            time_spent,
            save_callback=self.save_issue_worklog
        )
        existing_estimate = self.jira_client.get_remaining_estimate(issue)
        self.time_log_view.set_existing_estimate(existing_estimate)
        self.time_log_view.show()

    def save_issue_worklog(self, issue_key):
        """Save button event handler
        take user input values, save JIRAalues into Jira time tracking,
        show popup for successfully save or exception
        """

        issue = self.jira_client.issue(issue_key)
        time_spent = self.time_log_view.time_spent_line.text()
        start_date = self.time_log_view.date_start
        if not start_date:
            return
        comment = self.time_log_view.work_description_line.toPlainText()
        remaining_estimate = self.time_log_view.new_remaining_estimate
        log_work_params = self.take_timelog_values(
            remaining_estimate,
            self.time_log_view
        )
        try:
            self.jira_client.log_work(
                issue,
                time_spent,
                start_date,
                comment,
                **log_work_params)
            self.time_log_view.close()
            self.refresh_issue_list()
            self.view.timer.start(LOG_TIME)
            self.view.tray_icon.showMessage(
                'Saving work log',
                'Successfully saved',
                msecs=200
            )
            if self.pomodoro_view:
                self.pomodoro_view.reset_timer()

        except JIRAError as e:
            QMessageBox.about(self.time_log_view, "Error", e.text)

    def quit_app(self):
        if self.pomodoro_view:
            if not self.pomodoro_view.quit():
                return
        exit()
