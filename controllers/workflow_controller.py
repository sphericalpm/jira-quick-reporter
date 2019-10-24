from PyQt5.QtWidgets import QMessageBox
from jira import JIRAError

from workflow_window import WorkflowWindow, CompleteWorflowWindow
from .mixins import TimeLogMixin


class WorkflowController:
    def __init__(
        self,
        jira_client,
        issue_obj,
        status_id,
        existing_estimate,
        original_estimate,
        controller
    ):
        self.controller = controller
        self.jira_client = jira_client
        self.issue_obj = issue_obj
        self.existing_estimate = existing_estimate
        self.original_estimate = original_estimate
        self.status_id = status_id

    def show(self):
        self.view = WorkflowWindow(
            self.issue_obj,
            self.existing_estimate,
            self.original_estimate,
            self
        )
        self.view.show()

    def save_click(self):
        assignee = self.view.assignee_line.text()
        original_estimate = self.view.original_estimate_line.text()
        remaining_estimate = self.view.remaining_estimate_line.text()
        comment = self.view.comment_line.toPlainText()

        if assignee != 'Me':
            try:
                self.issue_obj.update(assignee={'name': assignee})
            except JIRAError as e:
                QMessageBox.about(self.view, 'Error', e.text)
                return

        if comment:
            self.jira_client.client.add_comment(self.issue_obj, comment)

        try:
            self.controller.view.tray_icon.showMessage(
                'Saving...',
                'Please wait',
                msecs=200
            )
            self.issue_obj.update(
                fields={
                    'timetracking': {
                        'remainingEstimate': remaining_estimate,
                        'originalEstimate': original_estimate,
                    }
                }
            )
        except JIRAError as e:
            QMessageBox.about(self.view, 'Error', e.text)
        try:
            self.jira_client.client.transition_issue(
                    self.issue_obj,
                    transition=self.status_id
                )
        except JIRAError as e:
            QMessageBox.about(self.view, 'Error', e.text)

        self.controller.refresh_issue_list()
        self.view.close()


class CompleteWorkflowController(TimeLogMixin):
    def __init__(self, jira_client, issue_obj, status, controller):
        self.controller = controller
        self.jira_client = jira_client
        self.issue_obj = issue_obj
        self.status = status

    def show(self):
        self.view = CompleteWorflowWindow(
            self,
            self.issue_obj,
            save_callback=self.save_click
            )
        self.view.show()

    def save_click(self, issue_key):
        time_spent = self.view.time_spent_line.text()
        start_date = self.view.date_start
        comment = self.view.work_description_line.toPlainText()
        remaining_estimate = self.view.new_remaining_estimate
        assignee = self.view.assignee_line.text()
        log_work_params = self.take_timelog_values(remaining_estimate, self.view)

        self.controller.view.tray_icon.showMessage(
            'Saving...',
            'Please wait',
            msecs=250
        )

        if not start_date:
            return

        if assignee != "Me":
            try:
                self.issue_obj.update(assignee={'name': assignee})
            except JIRAError as e:
                QMessageBox.about(self.view, 'Error', e.text)
                return

        try:
            # save timelog
            self.jira_client.log_work(
                self.issue_obj,
                time_spent,
                start_date,
                comment,
                **log_work_params)
        except JIRAError as e:
            QMessageBox.about(self.view, "Error", e.text)
            return

        try:
            # change resolution
            resolution = self.view.set_resolution.currentText()
            self.jira_client.client.transition_issue(
                self.issue_obj,
                transition=self.status,
                resolution={
                        'name': resolution,
                }
            )
        except JIRAError as e:
            QMessageBox.about(self.view, "Error", e.text)
            return

        try:
            # save version
            version = self.view.set_version.currentText()
            self.issue_obj.update(fields={'fixVersions': [{'name': version}]})
        except JIRAError as e:
            QMessageBox.about(self.view, "Error", e.text)
            return

        self.controller.refresh_issue_list()
        self.view.close()
