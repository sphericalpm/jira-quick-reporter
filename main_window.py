import sys
from PyQt5.QtWidgets import (
    QWidget,
    QDesktopWidget,
    QApplication,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

from jiraclient import JiraClient
from time_log_window import TimeLogWindow
from my_jira_token import my_token, email


class QCustomWidget(QWidget):
    """
    Class for custom list item
    """
    issue = None

    def __init__(self, issue):
        super().__init__()
        self.issue = issue

        self.timetracking_box = QHBoxLayout()
        self.estimated_label = QLabel()
        self.spent_label = QLabel()
        self.remaining_label = QLabel()
        self.logwork_btn = QPushButton('Log work')

        self.estimated_label.setMinimumWidth(200)
        self.spent_label.setMinimumWidth(200)
        self.remaining_label.setMinimumWidth(200)
        self.logwork_btn.setFixedWidth(90)
        self.logwork_btn.setStyleSheet('background-color:white')
        self.logwork_btn.clicked.connect(self.open_timelog_window_click)

        self.timetracking_box.addWidget(self.estimated_label)
        self.timetracking_box.addWidget(self.spent_label)
        self.timetracking_box.addWidget(self.remaining_label)
        self.timetracking_box.addWidget(self.logwork_btn)

        self.issue_key_label = QLabel()
        self.issue_title_label = QLabel()
        self.issue_title_label.setStyleSheet('font: bold')
        self.issue_title_label.setMaximumWidth(500)
        self.issue_title_label.setWordWrap(True)
        self.issue_key_label.setOpenExternalLinks(True)

        vbox = QVBoxLayout()
        vbox.addWidget(self.issue_key_label)
        vbox.addWidget(self.issue_title_label)
        vbox.addLayout(self.timetracking_box)
        self.setLayout(vbox)

    def open_timelog_window_click(self):
        self.time_log_window = TimeLogWindow(
            self.issue,
            JiraClient(email, my_token)  # TODO change to JiraClient instance from authorisation window
        )
        self.time_log_window.show()

    def set_issue_key(self, key, link):
        self.issue_key_label.setText(f'<a href={link}>{key}</a>')

    def set_issue_title(self, title):
        self.issue_title_label.setText(title)

    def set_time(self, estimated, spent, remaining):
        self.estimated_label.setText(f'Estimated: {estimated}')
        self.spent_label.setText(f'Logged: {spent}')
        self.remaining_label.setText(f'Remaining: {remaining}')


class MainWindow(QWidget):
    jira_client = JiraClient(email, my_token)

    def __init__(self):
        super().__init__()
        self.main_box = QVBoxLayout()
        self.list_box = QVBoxLayout()
        self.btn_box = QHBoxLayout()
        self.refresh_btn = QPushButton('Refresh')
        self.init_ui()

    def init_ui(self):
        self.resize(800, 450)
        self.center()
        self.setWindowTitle('JIRA Quick Reporter')
        self.setWindowIcon(QIcon('logo.png'))

        self.main_box.addLayout(self.list_box)
        self.main_box.addLayout(self.btn_box)
        self.setLayout(self.main_box)
        self.show_issues_list()
        self.set_refresh_button()
        self.show()

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def show_issues_list(self):
        """
        Show list of issues
        """
        issues = self.jira_client.get_issues()  # TODO change to JiraClient instance from authorisation window
        if not issues:
            label_info = QLabel('You have no issues.')
            label_info.setAlignment(Qt.AlignCenter)
            self.list_box.addWidget(label_info)
            return

        issue_list_widget = QListWidget(self)
        issue_list_widget.setStyleSheet(
                'QListWidget::item { border-bottom: 1px solid lightgray }')
        self.list_box.addWidget(issue_list_widget)

        for issue in issues:
            issue_widget = QCustomWidget(issue)
            issue_widget.set_issue_key(issue.key, issue.permalink())
            issue_widget.set_issue_title(issue.fields.summary)

            if issue.fields.timetracking.raw:
                timetracking = issue.fields.timetracking
                issue_widget.set_time(
                    getattr(timetracking, 'originalEstimate', '0m'),
                    getattr(timetracking, 'timeSpent', '0m'),
                    getattr(timetracking, 'remainingEstimate', '0m'),
                )
            else:
                issue_widget.set_time('0m', '0m', '0m')

            issue_list_widget_item = QListWidgetItem(issue_list_widget)
            issue_list_widget_item.setSizeHint(issue_widget.sizeHint())
            issue_list_widget.addItem(issue_list_widget_item)
            issue_list_widget.setItemWidget(issue_list_widget_item, issue_widget)

    def set_refresh_button(self):
        self.refresh_btn.setFixedWidth(90)
        self.refresh_btn.clicked.connect(self.refresh_click)
        self.btn_box.addWidget(self.refresh_btn, alignment=Qt.AlignRight)

    def refresh_click(self):
        for i in range(self.list_box.count()):
            self.list_box.itemAt(i).widget().setParent(None)
        self.show_issues_list()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    ex = MainWindow()
    sys.exit(app.exec_())
