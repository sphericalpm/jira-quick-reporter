from PyQt5.QtWidgets import QMessageBox
from jira import JIRAError

from controllers.loading_indicator import LoadingIndicator
from controllers.mixins import TimeLogMixin, ProcessWithThreadsMixin
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
        self.indicator = LoadingIndicator(self.view, self.view.vbox)

    def show(self):
        self.view.show()

    def save_click(self):
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


class CompleteWorkflowController(TimeLogMixin, ProcessWithThreadsMixin):
    def __init__(self, jira_client, issue, status, assignee, controller):
        super().__init__()
        self.controller = controller
        self.jira_client = jira_client
        self.issue = issue
        self.status = status
        self.assignee = assignee
        self.is_save = False
        self.possible_resolutions = self.controller.jira_client.get_possible_resolutions()
        self.view = CompleteWorflowWindow(
            self,
            self.issue,
            self.assignee,
            self.possible_resolutions,
            save_callback=self.save_click
        )
        self.indicator = LoadingIndicator(self.view, self.view.vbox)

    def show(self):
        self.view.show()

    def save_click(self, issue_key):
        self.start_loading(self.save_workflow, self.save_worflow_handler)

    def save_workflow(self):
        time_spent = self.view.time_spent_line.text()
        start_date = self.view.date_start
        comment = self.view.work_description_line.toPlainText()
        remaining_estimate = self.view.new_remaining_estimate
        assignee = self.view.assignee_line.text()
        log_work_params = self.take_timelog_values(remaining_estimate, self.view)

        if not start_date:
            raise ValueError('Enter start date')

        if assignee != self.assignee:
            try:
                self.issue.update(assignee={'name': assignee})
            except JIRAError as e:
                raise ValueError(e.text)

        try:
            # save timelog
            self.jira_client.log_work(
                self.issue,
                time_spent,
                start_date,
                comment,
                **log_work_params)
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
