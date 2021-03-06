from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5 import QtCore
from PyQt5.QtWidgets import (
    QLabel,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QCheckBox,
    QFormLayout,
    QMainWindow
)

from center_window import CenterWindow
from config import QSS, LOGO_PATH


class LoginWindow(CenterWindow, QMainWindow):
    def __init__(self, controller):
        super().__init__()
        self.setStyleSheet(QSS)
        self.controller = controller
        self.resize(380, 200)
        self.setWindowTitle('JIRA Quick Reporter')
        self.setWindowIcon(QIcon(LOGO_PATH))
        self.setMaximumSize(self.size())
        self.center()

        self.form = QFormLayout()
        self.setLayout(self.form)

        label_title = QLabel('Login to your account in JIRA')
        label_title.setObjectName('label_title')

        # create email field
        self.email_field = QLineEdit()
        self.email_field.setPlaceholderText('Enter your email')

        # create token field
        self.token_field = QLineEdit()
        self.token_field.setEchoMode(QLineEdit.Password)
        self.token_field.setPlaceholderText('Enter your token')

        # field with a link to create API token
        token_get_link = QLabel(
            '<a href="https://id.atlassian.com/manage/api-tokens">'
            'Create API token</a>'
        )
        token_get_link.setOpenExternalLinks(True)

        # create error field
        self.label_error = QLabel('The email or token is incorrect.')
        self.label_error.setObjectName('label_error')
        self.label_error.hide()

        # create login button
        self.btn_box = QHBoxLayout()
        btn_login = QPushButton('Login')
        btn_login.clicked.connect(self.controller.login)

        self.remember_me_btn = QCheckBox('Remember me')

        self.btn_box.addWidget(self.remember_me_btn)
        self.btn_box.addWidget(btn_login)

        # add widgets to form layout
        self.form.addRow(label_title)
        label_title.setAlignment(Qt.AlignCenter)
        self.form.addRow(self.email_field)
        self.form.addRow(self.token_field)
        self.form.addRow(token_get_link)
        self.form.addRow(self.label_error)
        self.form.addRow(self.btn_box)
        self.form.setAlignment(Qt.AlignCenter)

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Return:
            self.controller.login()

    def set_error_to_label(self, text):
        self.label_error.setText(text)
        self.label_error.show()
        self.token_field.clear()
