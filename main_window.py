from PyQt5.QtWidgets import (
    QWidget,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

from center_window import CenterWindow


class QCustomWidget(QWidget):
    ''' Custom list item
    Displays the issue key, title and a shorthand
    for the time estimated/spent/remaining
    '''

    def __init__(self):
        super().__init__()

        self.estimated_label = QLabel()
        self.spent_label = QLabel()
        self.remaining_label = QLabel()
        self.logwork_btn = QPushButton('Log work')

        # style settings for timelog labels
        self.estimated_label.setMinimumWidth(200)
        self.spent_label.setMinimumWidth(200)
        self.remaining_label.setMinimumWidth(200)

        self.logwork_btn.setStyleSheet('background-color:white')

        # create box layout for timelog labels
        self.timetracking_box = QHBoxLayout()
        self.timetracking_box.addWidget(self.estimated_label)
        self.timetracking_box.addWidget(self.spent_label)
        self.timetracking_box.addWidget(self.remaining_label)
        self.timetracking_box.addStretch()
        self.timetracking_box.addWidget(self.logwork_btn)

        # create labels for issue key and title
        self.issue_key_label = QLabel()
        self.issue_title_label = QLabel()
        self.issue_title_label.setStyleSheet('font: bold')
        self.issue_title_label.setWordWrap(True)
        self.issue_key_label.setOpenExternalLinks(True)

        # create main box layout
        vbox = QVBoxLayout()
        vbox.addWidget(self.issue_key_label)
        vbox.addWidget(self.issue_title_label)
        vbox.addLayout(self.timetracking_box)
        self.setLayout(vbox)

    def set_issue_key(self, key, link):
        ''' Set a link to the web page of the task to issue_key label '''

        self.issue_key_label.setText(f'<a href={link}>{key}</a>')

    def set_issue_title(self, title):
        self.issue_title_label.setText(title)

    def set_time(self, estimated, spent, remaining):
        ''' Set the estimated/spent/remaining
        time values to appropriate labels
        '''

        self.estimated_label.setText('Estimated: {}'.format(estimated))
        self.spent_label.setText('Logged: {}'.format(spent))
        self.remaining_label.setText('Remaining: {}'.format(remaining))


class MainWindow(CenterWindow):
    ''' Displays list with tasks assigned to current user in JIRA '''

    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.selected_issue_key = None
        self.resize(800, 450)
        self.center()
        self.setWindowTitle('JIRA Quick Reporter')
        self.setWindowIcon(QIcon('logo.png'))

        self.main_box = QVBoxLayout()
        self.list_box = QVBoxLayout()
        self.btn_box = QHBoxLayout()

        self.main_box.addLayout(self.list_box)
        self.main_box.addLayout(self.btn_box)
        self.setLayout(self.main_box)

        self.refresh_btn = QPushButton('Refresh')
        self.refresh_btn.clicked.connect(self.controller.refresh_issue_list)
        self.btn_box.addWidget(self.refresh_btn, alignment=Qt.AlignRight)

    def show_issues_list(self, issues_list):
        # clear listbox
        for i in range(self.list_box.count()):
            self.list_box.itemAt(i).widget().setParent(None)

        if not issues_list:
            label_info = QLabel('You have no issues.')
            label_info.setAlignment(Qt.AlignCenter)
            self.list_box.addWidget(label_info)
            return

        # create issue list widget
        issue_list_widget = QListWidget(self)
        issue_list_widget.setStyleSheet(
                'QListWidget::item { border-bottom: 1px solid lightgray }')
        self.list_box.addWidget(issue_list_widget)

        # create list of issues
        for issue in issues_list:
            issue_widget = QCustomWidget()
            issue_widget.set_issue_key(issue['key'], issue['link'])
            issue_widget.set_issue_title(issue['title'])
            issue_widget.set_time(
                issue['estimated'],
                issue['logged'],
                issue['remaining']
            )

            issue_widget.logwork_btn.clicked.connect(
                lambda: self.controller.open_timelog_window(issue['key'])
            )

            # add issue item to list
            issue_list_widget_item = QListWidgetItem(issue_list_widget)
            issue_list_widget_item.setSizeHint(issue_widget.sizeHint())
            issue_list_widget.addItem(issue_list_widget_item)
            issue_list_widget.setItemWidget(
                issue_list_widget_item, issue_widget
            )
