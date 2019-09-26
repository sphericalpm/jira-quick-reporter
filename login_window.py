import sys
from PyQt5.QtWidgets import (
    QWidget,
    QDesktopWidget,
    QApplication,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton
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

        # create login button
        btn_login = QPushButton('Login')
        btn_login.setFixedSize(150, 30)
        btn_login.setStyleSheet('margin-right: 35')
        btn_login.clicked.connect(self.login)
        self.btn_box.addWidget(token_get_link)
        self.btn_box.addWidget(btn_login)

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

    def open_main_window(self, jira_client):
        self.main_window = MainWindow(jira_client)
        self.main_window.show()
        self.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    login_window = LoginWindow()
    sys.exit(app.exec_())
