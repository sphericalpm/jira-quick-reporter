import sys
import os

from PyQt5.QtWidgets import QApplication
from jira import JIRAError
from jiraclient import JiraClient
from controllers.main_controller import MainController
from controllers.login_controller import LoginController


if __name__ == '__main__':
    app = QApplication(sys.argv)

    path = os.path.dirname(os.path.realpath(__file__))
    my_credentials_path = os.path.join(path, "my_credentials.txt")

    if os.path.exists(my_credentials_path):
        with open(my_credentials_path, 'r', encoding='utf-8') as file:
            content = file.read()
            try:
                email, token = content.split(';')
                jira_client = JiraClient(email, token)
                main_controller = MainController(jira_client)
            except (ValueError, JIRAError):
                os.remove(my_credentials_path)
                login_controller = LoginController()
    else:
        login_controller = LoginController()

    sys.exit(app.exec_())
