import os
import stat

from jira import JIRAError
from config import CREDENTIALS_PATH

from login_window import LoginWindow
from controllers.main_controller import MainController
from jiraclient import JiraClient


class LoginController:
    def __init__(self):
        self.view = LoginWindow(self)
        self.view.show()
        self.jira_client = None

    def login(self):
        email = self.view.email_field.text()
        token = self.view.token_field.text()

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
        """
        Save email and token into my_credentials.txt
        with 600 permission
        """

        with open(CREDENTIALS_PATH, 'w', encoding='utf-8') as file:
            file.write('{email};{token}'.format(email=email, token=token))

        if os.name == 'posix':
            os.chmod(CREDENTIALS_PATH, stat.S_IRUSR | stat.S_IWUSR)
        elif os.name is 'nt':
            import win32security
            import win32api
            import ntsecuritycon as con

            user, dom, t = win32security.LookupAccountName('', win32api.GetUserName())
            sd = win32security.GetFileSecurity(
                CREDENTIALS_PATH,
                win32security.DACL_SECURITY_INFORMATION
            )
            dacl = sd.GetSecurityDescriptorDacl()
            count = dacl.GetAceCount()
            for i in range(count):
                dacl.DeleteAce(0)

            dacl.AddAccessAllowedAce(
                win32security.ACL_REVISION,
                con.FILE_GENERIC_READ | con.FILE_GENERIC_WRITE,
                user
            )
            sd.SetSecurityDescriptorDacl(1, dacl, 0)
            win32security.SetFileSecurity(CREDENTIALS_PATH, win32security.DACL_SECURITY_INFORMATION, sd)

    def open_main_window(self):
        main_controller = MainController(self.jira_client)
        self.view.close()
