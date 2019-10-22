from PyQt5.QtWidgets import QMessageBox
from jira import JIRAError
import requests
from requests.auth import HTTPBasicAuth
import json

from workflow_window import WorkflowWindow, CompleteWorflowWindow
from config import CREDENTIALS_PATH, API_LINK_FOR_ACCOUNT_ID


class WorkflowController:
    def __init__(self, jira_client, issue_obj, status, controller):
        self.controller = controller
        self.jira_client = jira_client
        self.issue_obj = issue_obj
        self.status = status

    def show(self):
        self.view = WorkflowWindow(self.issue_obj, self.status, self)
        self.view.show()

    def find_account_id_for_user(self, assignee):
        with open(CREDENTIALS_PATH, 'r', encoding='utf-8') as file:
            content = file.readline()
            email, token = content.split(';')

        url = API_LINK_FOR_ACCOUNT_ID.format(assignee)
        auth = HTTPBasicAuth(email, token)

        headers = {
            "Accept": "application/json"
        }

        response = requests.request(
            "GET",
            url,
            headers=headers,
            auth=auth
        )

        try:
            decode_response = json.loads(response.text)
            account_id = decode_response[0]['accountId']

            return account_id

        except json.decoder.JSONDecodeError as e:
            QMessageBox.about(self.view, 'Error', e.text)


    def save_click(self):
        assignee = self.view.assignee_line.text()
        original_estimate = self.view.original_estimate_line.text()
        remaining_estimate = self.view.remaining_estimate_line.text()
        comment = self.view.comment_line.toPlainText()

        if assignee != "Me":
            account_id = self.find_account_id_for_user(assignee)

            if account_id:
                try:
                    self.jira_client.client.assign_issue(self.issue_obj, account_id)
                except JIRAError as e:
                    QMessageBox.about(self.view, 'Error', e.text)
                    return
            else:
                QMessageBox.about(self.view, 'Error', 'Account not found')
                return

        if comment != "":
            self.jira_client.client.add_comment(self.issue_obj, comment)

        try:
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
        self.view = CompleteWorflowWindow(self, self.issue_obj, save_callback=self.save_click)
        self.view.show()

    def get_possible_resolutions(self, issue):
        resolutions = self.jira_client.client.resolutions()
        possible_resolutions = [resolution.name for resolution in resolutions]

        return possible_resolutions

    def save_click(self, issue_key):
        issue = self.jira_client.issue(issue_key)
        time_spent = self.view.time_spent_line.text()
        start_date = self.view.date_start

        if not start_date:
            return
        comment = self.view.work_description_line.toPlainText()
        remaining_estimate = self.view.new_remaining_estimate

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
        try:
            self.jira_client.log_work(
                issue,
                time_spent,
                start_date,
                comment,
                **log_work_params)

            resolution = self.view.set_resolution.currentText()
            resolutions = self.jira_client.client.resolutions()
            possible_resolutions = {resolution.name: resolution.id for resolution in resolutions}
            new_resolution = possible_resolutions[resolution]
            self.jira_client.client.transition_issue(issue, new_resolution)

            self.view.close()
            self.view.timer.start(LOG_TIME)
            self.view.tray_icon.showMessage(
                'Saving...',
                'Successfully saved',
                msecs=200
            )
        except JIRAError as e:
            QMessageBox.about(self.view, "Error", e.text)
