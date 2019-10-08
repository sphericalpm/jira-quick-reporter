from PyQt5.QtWidgets import (
    QApplication,
    QLabel,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QCheckBox,
    QFormLayout
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

from center_window import CenterWindow
from config import QSS_PATH, LOGO_PATH


class LoginWindow(CenterWindow):
    def __init__(self, controller):
        super().__init__()

        with open(QSS_PATH, 'r') as qss_file:
            self.setStyleSheet(qss_file.read())

        self.controller = controller
        self.resize(380, 200)
        self.center()
        self.setWindowTitle('JIRA Quick Reporter')
        self.setWindowIcon(QIcon(LOGO_PATH))
        self.setMaximumSize(self.size())

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

        # create remember me checkbox
        self.cb_remember_me = QCheckBox('Remember me')

        self.btn_box.addWidget(self.cb_remember_me)
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

    def set_wait_cursor(self):
        QApplication.setOverrideCursor(Qt.WaitCursor)

    def stop_wait_cursor(self):
        QApplication.restoreOverrideCursor()

    def remember_cb_state(self):
        return 1 if self.cb_remember_me.isChecked() else 0

    def set_error_to_label(self, text):
        self.label_error.setText(text)
        self.label_error.show()
        self.token_field.clear()
