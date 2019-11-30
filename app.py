import sys
import os

from requests.exceptions import ConnectionError, ReadTimeout
from tendo import singleton
from PyQt5.QtWidgets import QApplication, QMessageBox
from jira import JIRAError

from jiraclient import JiraClient
from controllers.main_controller import MainController
from controllers.login_controller import LoginController
from config import CREDENTIALS_PATH


if __name__ == '__main__':
    me = singleton.SingleInstance()
    # possibility to open only one application at time
    app = QApplication(sys.argv)
    path = os.path.dirname(os.path.realpath(__file__))

    if os.path.exists(CREDENTIALS_PATH):
        with open(CREDENTIALS_PATH, 'r', encoding='utf-8') as file:
            content = file.read()
            try:
                email, token = content.split(';')
                jira_client = JiraClient(email, token)
                jira_client.client.search_issues(
                    'assignee = currentUser()',
                    maxResults=1
                )
                controller = MainController(jira_client)
                app.setQuitOnLastWindowClosed(False)
            except (ValueError, JIRAError):
                controller = LoginController(app)
            except (ConnectionError,
                    ReadTimeout):
                QMessageBox.warning(
                    None,
                    'Connection error',
                    'Check your internet connection and try again'
                )
                sys.exit()
    else:
        controller = LoginController(app)
    controller.show()
    sys.exit(app.exec_())
