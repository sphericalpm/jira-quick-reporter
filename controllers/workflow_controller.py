from PyQt5.QtWidgets import QMessageBox
from jira import JIRAError

from config import LOG_TIME
from controllers.mixins import ProcessWithThreadsMixin
from controllers.time_log_controller import TimeLogController
from workflow_window import WorkflowWindow, CompleteWorflowWindow


class WorkflowController(ProcessWithThreadsMixin):
    def __init__(
        self,
        jira_client,
        issue,
        status_id,
        existing_estimate,
        original_estimate,
        assignee,
        controller
    ):
        super().__init__()
        self.controller = controller
        self.jira_client = jira_client
        self.issue = issue
        self.existing_estimate = existing_estimate
        self.original_estimate = original_estimate
        self.status_id = status_id
        self.assignee = assignee
        self.is_save = False
        self.view = WorkflowWindow(
            self.issue,
            self.existing_estimate,
            self.original_estimate,
            self.assignee,
            self
        )
        self.set_loading_indicator()

    def show(self):
        self.view.show()

    def save(self):
        self.start_loading(self.save_workflow, self.save_worflow_handler)

    def save_workflow(self):
        assignee = self.view.assignee_line.text()
        original_estimate = self.view.original_estimate_line.text()
        remaining_estimate = self.view.remaining_estimate_line.text()
        comment = self.view.comment_line.toPlainText()

        if assignee != self.assignee:
            try:
                self.issue.update(assignee={'name': assignee})
            except JIRAError as e:
                raise ValueError(e.text)

        if comment:
            self.jira_client.client.add_comment(self.issue, comment)

        try:
            self.issue.update(
                fields={
                    'timetracking': {
                        'remainingEstimate': remaining_estimate,
                        'originalEstimate': original_estimate,
                    }
                }
            )
        except JIRAError as e:
            raise ValueError(e.text)
        try:
            self.jira_client.client.transition_issue(
                    self.issue,
                    transition=self.status_id
                )
        except JIRAError as e:
            raise ValueError(e.text)

        self.is_save = True

    def save_worflow_handler(self, error_text):
        if error_text:
            QMessageBox.about(self.view, 'Error', error_text)
        else:
            self.controller.refresh_issue_list()
            self.view.close()

    def close(self):
        if not self.is_save:
            self.controller.reset_workflow(self.issue)


class CompleteWorkflowController(TimeLogController):
    def __init__(self, jira_client, issue, status, assignee, main_controller):
        self.status = status
        self.assignee = assignee
        self.is_save = False
        self.possible_resolutions = jira_client.get_possible_resolutions()
        self.possible_versions = jira_client.get_possible_versions(issue)
        super().__init__(main_controller, jira_client, issue)

    def init_view(self):
        self.view = CompleteWorflowWindow(
            self,
            self.issue.key,
            self.assignee,
            self.possible_resolutions,
            self.possible_versions
        )
        self.view.set_existing_estimate(self.existing_estimate)

    def show(self):
        self.view.show()

    def save(self):
        if self.get_timelog_parameters():
            self.start_loading(self.save_workflow, self.save_handler)

    def save_workflow(self):
        assignee = self.view.assignee_line.text()
        if assignee != self.assignee:
            try:
                self.issue.update(assignee={'name': assignee})
            except JIRAError as e:
                raise ValueError(e.text)

        try:
            # save timelog
            self.jira_client.log_work(
                self.issue,
                self.time_spent,
                self.start_date,
                self.comment,
                **self.log_work_params)
        except JIRAError as e:
            raise ValueError(e.text)

        try:
            # change resolution
            resolution = self.view.set_resolution.currentText()
            self.jira_client.client.transition_issue(
                self.issue,
                transition=self.status,
                resolution={
                        'name': resolution,
                }
            )
        except JIRAError as e:
            raise ValueError(e.text)

        try:
            # save version
            version = self.view.set_version.currentText()
            self.issue.update(fields={'fixVersions': [{'name': version}]})
        except JIRAError as e:
            raise ValueError(e.text)

    def save_handler(self, error_text):
        if error_text:
            QMessageBox.about(self.view, 'Error', error_text)
        else:
            self.is_save = True
            self.main_controller.view.timer_log_work.start(LOG_TIME)
            self.main_controller.refresh_issue_list()
            self.view.close()

    def close(self):
        if not self.is_save:
            self.main_controller.reset_workflow(self.issue)
