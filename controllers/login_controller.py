import os
import stat

from jira import JIRAError

from config import CREDENTIALS_PATH
from controllers.mixins import ProcessWithThreadsMixin
from controllers.main_controller import MainController
from controllers.loading_indicator import LoadingIndicator
from jiraclient import JiraClient
from login_window import LoginWindow


class LoginController(ProcessWithThreadsMixin):
    def __init__(self):
        super().__init__()
        self.view = LoginWindow(self)
        self.indicator = LoadingIndicator(self.view, self.view.form)
        self.jira_client = None

    def show(self):
        self.view.show()

    def login(self):
        self.start_loading(self.connect_to_jira, self.open_main_window)

    def connect_to_jira(self):
        email = self.view.email_field.text()
        token = self.view.token_field.text()
        try:
            self.jira_client = JiraClient(email, token)
            self.jira_client.client.search_issues(
                'assignee = currentUser()',
                maxResults=1
            )  # check if username is correct
            # use search_issues because jira.current_user always return none
            if self.view.remember_me_btn.isChecked():
                self.remember_me(email, token)
        except JIRAError:
            raise ValueError('Email or token is incorrect')
        except UnicodeEncodeError:
            raise ValueError('English letters only')

    def remember_me(self, email, token):
        """
        Save email and token into my_credentials.txt
        with 600 permission
        """

        with open(CREDENTIALS_PATH, 'w', encoding='utf-8') as file:
            file.write('{email};{token}'.format(email=email, token=token))

        os.chmod(CREDENTIALS_PATH, stat.S_IRUSR | stat.S_IWUSR)

    def open_main_window(self, error_text):
        if error_text:
            self.view.set_error_to_label(error_text)
        else:
            main_controller = MainController(self.jira_client)
            main_controller.show()
            self.view.close()
