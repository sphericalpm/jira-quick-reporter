import sys
import os

import requests
from PyQt5.QtWidgets import QApplication, QMessageBox
from jira import JIRAError

from jiraclient import JiraClient
from controllers.main_controller import MainController
from controllers.login_controller import LoginController
from config import CREDENTIALS_PATH


if __name__ == '__main__':
    app = QApplication(sys.argv)

    path = os.path.dirname(os.path.realpath(__file__))

    if os.path.exists(CREDENTIALS_PATH):
        with open(CREDENTIALS_PATH, 'r', encoding='utf-8') as file:
            content = file.read()
            try:
                email, token = content.split(';')
                jira_client = JiraClient(email, token)
                main_controller = MainController(jira_client)
            except (ValueError, JIRAError):
                login_controller = LoginController()
            except requests.exceptions.ConnectionError as e:
                QMessageBox.warning(
                    None,
                    'Connection error',
                    'Check your internet connection and try again'
                )
    else:
        login_controller = LoginController()

    sys.exit(app.exec_())
