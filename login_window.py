from PyQt5.QtWidgets import (
    QApplication,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QCheckBox
)
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import Qt

from center_window import CenterWindow


class LoginWindow(CenterWindow):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
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
        btn_login.clicked.connect(self.controller.login)

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

    def email(self):
        return self.email_field.text()

    def token(self):
        return self.token_field.text()

    def set_wait_cursor(self):
        QApplication.setOverrideCursor(Qt.WaitCursor)

    def stop_wait_cursor(self):
        QApplication.restoreOverrideCursor()

    def remember_cb_state(self):
        if self.cb_remember_me.checkState() == Qt.Checked:
            return 1
        else:
            return 0

    def set_error_to_label(self, text):
        self.label_error.setText(text)
        self.label_error.show()
        self.token_field.clear()
