import os
import stat

from jira import JIRAError

from config import CREDENTIALS_PATH
from controllers.main_controller import MainController
from controllers.loading_indicator import LoadingIndicator, Thread
from jiraclient import JiraClient
from login_window import LoginWindow
from utils.decorators import catch_timeout_exception


class LoginController:
    def show(self):
        self.view = LoginWindow(self)
        self.view.show()
        self.jira_client = None

    @catch_timeout_exception
    def login(self, *args):
        self.indicator = LoadingIndicator(self, self.view.form)
        self.indicator.show()
        self.new_thread = Thread(self.save_and_open_issue_list)
        self.new_thread.start()
        self.new_thread.finished.connect(self.stop_indicator)

    def stop_indicator(self, result, error):
        self.indicator.spinner.stop()
        if result:
            self.open_main_window()
        elif error:
            self.view.set_error_to_label(error)

    def save_and_open_issue_list(self):
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
            return ValueError('English letters only')

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
