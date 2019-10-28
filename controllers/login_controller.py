import os
import stat

from jira import JIRAError

from config import CREDENTIALS_PATH
from controllers.main_controller import MainController
from jiraclient import JiraClient
from login_window import LoginWindow
from utils.decorators import catch_timeout_exception


class LoginController:
    def show(self):
        self.view = LoginWindow(self)
        self.view.show()
        self.jira_client = None

    @catch_timeout_exception
    def login(self):
        email = self.view.email_field.text()
        token = self.view.token_field.text()

        try:
            self.jira_client = JiraClient(email, token)
            if self.view.remember_me_btn.isChecked():
                self.remember_me(email, token)
            self.open_main_window()
        except JIRAError:
            self.view.set_error_to_label('The email or token is incorrect.')
        except UnicodeEncodeError:
            self.view.set_error_to_label('English letters only')

    def remember_me(self, email, token):
        """
        Save email and token into my_credentials.txt
        with 600 permission
        """

        with open(CREDENTIALS_PATH, 'w', encoding='utf-8') as file:
            file.write('{email};{token}'.format(email=email, token=token))

        os.chmod(CREDENTIALS_PATH, stat.S_IRUSR | stat.S_IWUSR)

    def open_main_window(self):
        main_controller = MainController(self.jira_client)
        main_controller.show()
        self.view.close()
