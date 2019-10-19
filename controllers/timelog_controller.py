from jira import JIRAError
from PyQt5.QtWidgets import QMessageBox

from time_log_window import TimeLogWindow


class TimeLogController:
    def __init__(self, jira_client, issue_key, main_controller):
        self.main_controller = main_controller
        self.jira_client = jira_client
        self.issue_key = issue_key

    def show(self):
        self.issue = self.jira_client.issue(self.issue_key)
        self.view = TimeLogWindow(self, self.issue_key)
        self.existing_estimate = self.jira_client.get_remaining_estimate(self.issue)
        self.view.set_existing_estimate(self.existing_estimate)
        self.view.show()

    def save_click(self):
        """Save button event handler
        take user input values, save JIRAalues into Jira time tracking,
        show popup for successfully save or exception
        """

        time_spent = self.view.time_spent_line.text()
        start_date = self.view.date_start
        if not start_date:
            return
        comment = self.view.comment()
        remaining_estimate = self.view.new_remaining_estimate

        if not remaining_estimate or \
                remaining_estimate.get('name') == 'automatically_estimate':
            log_work_params = {}

        elif remaining_estimate.get('name') == 'existing_estimate':
            log_work_params = {
                'adjust_estimate': 'new',
                'new_estimate': remaining_estimate.get('value')
            }
        elif remaining_estimate.get('name') == 'set_new_estimate':
            estimate = self.view.set_new_estimate_value.text()
            log_work_params = {
                'adjust_estimate': 'new',
                'new_estimate': estimate
            }
        elif remaining_estimate.get('name') == 'reduce_estimate':
            estimate = self.view.reduce_estimate_value.text()
            log_work_params = {
                'adjust_estimate': 'manual',
                'new_estimate': estimate
            }
        else:
            QMessageBox.about(self.view, 'Error', 'something went wrong')
            return
        try:
            self.jira_client.log_work(
                self.issue,
                time_spent,
                start_date,
                comment,
                **log_work_params)
            self.view.close()
            self.main_controller.refresh_issue_list()
        except JIRAError as e:
            QMessageBox.about(self.view, "Error", e.text)
