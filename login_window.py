import sys
import stat
import os
from PyQt5.QtWidgets import (
    QWidget,
    QDesktopWidget,
    QApplication,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QMessageBox
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from jiraclient import JiraClient
from jira import JIRAError
from main_window import MainWindow


class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.main_box = QVBoxLayout()
        self.btn_box = QHBoxLayout()
        self.email_field = QLineEdit()
        self.token_field = QLineEdit()
        self.label_error = QLabel('The email or token is incorrect.')

        path = os.path.dirname(os.path.realpath(__file__))
        my_credentials_path = os.path.join(path, "my_credentials.txt")

        if os.path.exists(my_credentials_path):
            with open(my_credentials_path, 'r', encoding='utf-8') as f:
                content = f.read()
                email, token = content.split(';')

                jira_client = JiraClient(email, token)
                self.open_main_window(jira_client)
        else:
            self.init_ui()

    def init_ui(self):
        self.setFixedSize(400, 230)
        self.center()
        self.setWindowTitle('JIRA Quick Reporter')
        self.setWindowIcon(QIcon('logo.png'))
        self.setLayout(self.main_box)

        label_title = QLabel('Login to your account in JIRA')
        label_title.setStyleSheet('font:18px')

        # create email field
        self.email_field.setPlaceholderText('Enter your email')
        self.email_field.setFixedWidth(300)
        self.email_field.setFixedHeight(30)

        # create token field
        self.token_field.setEchoMode(QLineEdit.Password)
        self.token_field.setPlaceholderText('Enter your token')
        self.token_field.setFixedWidth(300)
        self.token_field.setFixedHeight(30)

        # create error field
        self.label_error.setStyleSheet('color:red')
        self.label_error.hide()

        # field with a link to create API token
        token_get_link = QLabel(
            '<a href="https://id.atlassian.com/manage/api-tokens">'
            'Create API token</a>'
        )
        token_get_link.setOpenExternalLinks(True)
        token_get_link.setStyleSheet('font: 14px')
        token_get_link.setStyleSheet('margin-left: 35')

        # create login, remember me buttons
        btn_login = QPushButton('Log In')
        btn_remember_me = QPushButton('Remember me')
        btn_login.setFixedSize(100, 30)
        btn_remember_me.setFixedSize(110, 30)
        btn_login.clicked.connect(self.login)
        btn_remember_me.clicked.connect(self.remember_me)
        self.btn_box.addWidget(token_get_link)
        self.btn_box.addWidget(btn_login)
        self.btn_box.addWidget(btn_remember_me)

        # add widgets to main box layout
        self.main_box.addWidget(label_title, alignment=Qt.AlignCenter)
        self.main_box.addWidget(self.email_field, alignment=Qt.AlignCenter)
        self.main_box.addWidget(self.token_field, alignment=Qt.AlignCenter)
        self.main_box.addWidget(self.label_error, alignment=Qt.AlignCenter)
        self.main_box.addLayout(self.btn_box)
        self.show()

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def login(self):
        email = self.email_field.text()
        token = self.token_field.text()

        QApplication.setOverrideCursor(Qt.WaitCursor)

        try:
            jira_client = JiraClient(email, token)
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

    def remember_me(self):
        """Save emai and token into my_credentials.txt with 600 permission
        """
        email = self.email_field.text()
        token = self.token_field.text()

        with open('my_credentials.txt', 'w', encoding='utf-8') as f:
            f.write("%s;%s" % (email, token))

        os.chmod('my_credentials.txt', stat.S_IRUSR | stat.S_IWUSR)
        QMessageBox.about(self, 'Saved', 'Successfully remembered')
        self.login()

    def open_main_window(self, jira_client):
        self.main_window = MainWindow(jira_client)
        self.main_window.show()
        self.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    login_window = LoginWindow()
    sys.exit(app.exec_())
