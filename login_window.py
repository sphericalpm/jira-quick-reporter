import sys
import stat
import os

from PyQt5.QtWidgets import (
    QApplication,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QCheckBox
)
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import Qt

from jira import JIRAError
from jiraclient import JiraClient
from main_window import MainWindow
from center_window import CenterWindow


class LoginWindow(CenterWindow):
    def __init__(self):
        super().__init__()
        self.resize(380, 230)
        self.center()
        self.setWindowTitle('JIRA Quick Reporter')
        self.setWindowIcon(QIcon('logo.png'))

        self.main_box = QVBoxLayout()
        self.setLayout(self.main_box)
        self.label_error = QLabel('The email or token is incorrect.')

        label_title = QLabel('Login to your account in JIRA')
        font16 = QFont()
        font16.setPointSize(16)
        label_title.setFont(font16)

        # create email field
        self.email_field = QLineEdit()
        self.email_field.setPlaceholderText('Enter your email')
        font14 = QFont()
        font14.setPointSize(14)
        self.email_field.setFont(font14)

        # create token field
        self.token_field = QLineEdit()
        self.token_field.setEchoMode(QLineEdit.Password)
        self.token_field.setPlaceholderText('Enter your token')
        self.token_field.setFont(font14)

        # create error field
        self.label_error.setStyleSheet('color:red')
        self.label_error.hide()

        # field with a link to create API token
        token_get_link = QLabel(
            '<a href="https://id.atlassian.com/manage/api-tokens">'
            'Create API token</a>'
        )
        token_get_link.setOpenExternalLinks(True)

        # create login button
        self.btn_box = QHBoxLayout()
        btn_login = QPushButton('Login')
        btn_login.setFont(font14)
        btn_login.clicked.connect(self.login)

        # create remember me checkbox
        self.cb_remember_me = QCheckBox('Remember me')
        self.cb_remember_me.setFont(font14)
        print(self.cb_remember_me.checkState())

        self.btn_box.addWidget(self.cb_remember_me)
        self.btn_box.addWidget(btn_login)

        # add widgets to main box layout
        self.main_box.addWidget(label_title, alignment=Qt.AlignCenter)
        self.main_box.addWidget(self.email_field, alignment=Qt.AlignBaseline)
        self.main_box.addWidget(self.token_field, alignment=Qt.AlignBaseline)
        self.main_box.addWidget(token_get_link)
        self.main_box.addWidget(self.label_error, alignment=Qt.AlignCenter)
        self.main_box.addLayout(self.btn_box)
        self.show()

    def login(self):
        email = self.email_field.text()
        token = self.token_field.text()

        QApplication.setOverrideCursor(Qt.WaitCursor)

        try:
            jira_client = JiraClient(email, token)
            if self.cb_remember_me.checkState() == Qt.Checked:
                self.remember_me(email, token)
            self.open_main_window(jira_client)
        except JIRAError:
            self.label_error.setText('The email or token is incorrect.')
            self.label_error.show()
            self.token_field.clear()
        except UnicodeEncodeError:
            self.label_error.setText('English letters only')
            self.label_error.show()
            self.token_field.clear()
            self.email_field.clear()
        QApplication.restoreOverrideCursor()

    def remember_me(self, email, token):
        ''' Save email and token into my_credentials.txt with 600 permission
        '''

        with open('my_credentials.txt', 'w', encoding='utf-8') as f:
            f.write(f'{email};{token}')

        os.chmod('my_credentials.txt', stat.S_IRUSR | stat.S_IWUSR)
        QMessageBox.about(self, 'Saved', 'Successfully remembered')

    def open_main_window(self, jira_client):
        self.main_window = MainWindow(jira_client)
        self.main_window.show()
        self.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)

    path = os.path.dirname(os.path.realpath(__file__))
    my_credentials_path = os.path.join(path, "my_credentials.txt")

    if os.path.exists(my_credentials_path):
        with open(my_credentials_path, 'r', encoding='utf-8') as f:
            content = f.read()
            try:
                email, token = content.split(';')
                jira_client = JiraClient(email, token)
                main_window = MainWindow(jira_client)
            except (ValueError, JIRAError):
                os.remove(my_credentials_path)
                login_window = LoginWindow()
    else:
        login_window = LoginWindow()

    sys.exit(app.exec_())
