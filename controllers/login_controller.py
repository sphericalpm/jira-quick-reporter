import os
import stat

from jira import JIRAError
from PyQt5.QtWidgets import QMessageBox

from login_window import LoginWindow
from controllers.main_controller import MainController
from jiraclient import JiraClient


class LoginController:
    def __init__(self):
        self.view = LoginWindow(self)
        self.view.show()
        self.jira_client = None

    def login(self):
        email = self.view.email()
        token = self.view.token()

        self.view.set_wait_cursor()
        try:
            self.jira_client = JiraClient(email, token)
            if self.view.remember_cb_state():
                self.remember_me(email, token)
            self.open_main_window()
        except JIRAError:
            self.view.set_error_to_label('The email or token is incorrect.')
        except UnicodeEncodeError:
            self.view.set_error_to_label('English letters only')
        self.view.stop_wait_cursor()

    def remember_me(self, email, token):
        ''' Save email and token into my_credentials.txt with 600 permission
        '''

        with open('my_credentials.txt', 'w', encoding='utf-8') as file:
            file.write('{email};{token}'.format(email=email, token=token))

        os.chmod('my_credentials.txt', stat.S_IRUSR | stat.S_IWUSR)
        QMessageBox.about(self.view, 'Saved', 'Successfully remembered')

    def open_main_window(self):
        main_controller = MainController(self.jira_client)
        self.view.close()
