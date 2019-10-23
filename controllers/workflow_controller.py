from PyQt5.QtWidgets import QMessageBox
from jira import JIRAError

from workflow_window import WorkflowWindow, CompleteWorflowWindow


class WorkflowController:
    def __init__(self, jira_client, issue_obj, status, controller):
        self.controller = controller
        self.jira_client = jira_client
        self.issue_obj = issue_obj
        self.status = status

    def show(self):
        self.view = WorkflowWindow(self.issue_obj, self.status, self)
        self.view.show()

    def save_click(self):
        assignee = self.view.assignee_line.text()
        original_estimate = self.view.original_estimate_line.text()
        remaining_estimate = self.view.remaining_estimate_line.text()
        comment = self.view.comment_line.toPlainText()

        if assignee != "Me":
            try:
                self.issue_obj.update(assignee={'name': assignee})
            except JIRAError as e:
                QMessageBox.about(self.view, 'Error', e.text)
                return

        if comment != "":
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

        self.view.close()


class CompleteWorkflowController:
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

    def get_possible_resolutions(self, issue):
        resolutions = self.jira_client.client.resolutions()
        possible_resolutions = [resolution.name for resolution in resolutions]

        return possible_resolutions

    def get_possible_versions(self, issue):
        all_projects = self.jira_client.client.projects()
        current_project_key = issue.key.split('-')[0]

        for id, project in enumerate(all_projects):
            if project.key == current_project_key:
                current_project_id = id

        versions = self.jira_client.client.project_versions(
            all_projects[current_project_id]
        )
        possible_versions = [version.name for version in versions]

        return possible_versions

    def save_click(self, issue_key):
        time_spent = self.view.time_spent_line.text()
        start_date = self.view.date_start
        comment = self.view.work_description_line.toPlainText()
        remaining_estimate = self.view.new_remaining_estimate
        assignee = self.view.assignee_line.text()
        log_work_params = self.take_timelog_values(remaining_estimate)

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

    def take_timelog_values(self, remaining_estimate):
        if not remaining_estimate:
            log_work_params = dict()

        elif remaining_estimate.get('name') == 'existing_estimate':
            log_work_params = dict(
                adjust_estimate='new',
                new_estimate=remaining_estimate.get('value')
            )
        elif remaining_estimate.get('name') == 'set_new_estimate':
            estimate = self.view.set_new_estimate_value.text()
            log_work_params = dict(
                adjust_estimate='new',
                new_estimate=estimate
            )
        elif remaining_estimate.get('name') == 'reduce_estimate':
            estimate = self.view.reduce_estimate_value.text()
            log_work_params = dict(
                adjust_estimate='manual',
                new_estimate=estimate
            )
        else:
            QMessageBox.about(
                self.view,
                'Error',
                'something went wrong'
            )
            return

        return log_work_params
