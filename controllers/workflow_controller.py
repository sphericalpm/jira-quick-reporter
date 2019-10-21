from PyQt5.QtWidgets import QMessageBox
from jira import JIRAError

from workflow_window import WorkflowWindow


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
            from receive_accountId import find_accountId_for_user
            account_id = find_accountId_for_user(assignee)

            if account_id:
                try:
                    self.jira_client.client.assign_issue(self.issue_obj, account_id)
                except JIRAError as e:
                    QMessageBox.about(self.view, 'Error', e.text)


        return assignee, original_estimate, remaining_estimate, comment
