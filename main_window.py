from PyQt5.QtWidgets import (
    QWidget,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QGridLayout,
    QComboBox
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from functools import partial

from center_window import CenterWindow
from config import QSS_PATH, LOGO_PATH


class QCustomWidget(QWidget):
    """ Custom list item
    Displays the issue key, title and a shorthand
    for the time estimated/spent/remaining
    """

    def __init__(self):
        super().__init__()
        self.estimated_label = QLabel()
        self.estimated_label.setObjectName('estimated_label')
        self.spent_label = QLabel()
        self.spent_label.setObjectName('spent_label')
        self.remaining_label = QLabel()
        self.remaining_label.setObjectName('remaining_label')

        self.logwork_btn = QPushButton('Log work')
        self.logwork_btn.setObjectName('logwork_btn')
        self.logwork_btn.setMaximumSize(self.logwork_btn.size())

        self.set_workflow = QComboBox(self)

        timetracking_grid = QGridLayout()
        timetracking_grid.addWidget(self.estimated_label, 0, 0)
        timetracking_grid.addWidget(self.spent_label, 0, 1)
        timetracking_grid.addWidget(self.remaining_label, 0, 2)
        timetracking_grid.addWidget(self.logwork_btn, 0, 3, Qt.AlignRight)
        timetracking_grid.addWidget(self.set_workflow, 1, 3, Qt.AlignRight)

        # create labels for issue key and title
        self.issue_key_label = QLabel()
        self.issue_title_label = QLabel()
        self.issue_title_label.setObjectName('issue_title_label')
        self.issue_title_label.setWordWrap(True)
        self.issue_key_label.setOpenExternalLinks(True)

        # create main box layout
        vbox = QVBoxLayout()
        vbox.addWidget(self.issue_key_label)
        vbox.addWidget(self.issue_title_label)
        vbox.addLayout(timetracking_grid)
        self.setLayout(vbox)

    def set_issue_key(self, key, link):
        """
        Set a link to the web page of the task
        to issue_key label
        """

        self.issue_key_label.setText(
            '<a href={link}>{key}</a>'.format(link=link, key=key)
        )

    def set_issue_title(self, title):
        self.issue_title_label.setText(title)

    def set_time(self, estimated, spent, remaining):
        """
        Set the estimated/spent/remaining
        time values to appropriate labels
        """

        self.estimated_label.setText('Estimated: {}'.format(estimated))
        self.spent_label.setText('Logged: {}'.format(spent))
        self.remaining_label.setText('Remaining: {}'.format(remaining))


class MainWindow(CenterWindow):
    """
    Displays list with tasks assigned to current user in JIRA
    """
    def __init__(self, controller):
        super().__init__()

        with open(QSS_PATH, 'r') as qss_file:
            self.setStyleSheet(qss_file.read())

        self.controller = controller
        self.selected_issue_key = None
        self.resize(800, 450)
        self.center()
        self.setWindowTitle('JIRA Quick Reporter')
        self.setWindowIcon(QIcon(LOGO_PATH))

        self.main_box = QVBoxLayout()
        self.list_box = QVBoxLayout()
        self.btn_box = QHBoxLayout()

        self.issue_list_widget = QListWidget(self)

        self.main_box.addLayout(self.list_box)
        self.main_box.addLayout(self.btn_box)
        self.setLayout(self.main_box)

        self.load_more_issues_btn = QPushButton('Load more')
        width = self.load_more_issues_btn.fontMetrics().boundingRect(
            self.load_more_issues_btn.text()
        ).width() + 20
        self.load_more_issues_btn.setMaximumWidth(width)
        self.load_more_issues_btn.clicked.connect(
            lambda: self.controller.refresh_issue_list(True)
        )

        self.refresh_btn = QPushButton('Refresh')
        self.refresh_btn.clicked.connect(self.controller.refresh_issue_list)
        self.btn_box.addWidget(self.refresh_btn, alignment=Qt.AlignRight)

    def show_issues_list(self, issues_list, load_more=False):
        # clear listbox
        if not load_more:
            for i in range(self.list_box.count()):
                self.list_box.itemAt(0).widget().setParent(None)
            self.issue_list_widget.clear()

        if not issues_list and not load_more:
            label_info = QLabel('You have no issues.')
            label_info.setAlignment(Qt.AlignCenter)
            self.list_box.addWidget(label_info)
            return
        elif not load_more:
            self.list_box.addWidget(self.issue_list_widget)
            self.list_box.addWidget(self.load_more_issues_btn)

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
                partial(self.controller.open_timelog_window, issue['key'])
            )

            current_workflow = issue['issue_obj'].fields.status
            possible_workflows = list(issue['workflow'].keys())

            if current_workflow.name != 'Backlog':  # when it's 'Backlog' status,
                # JIRA API provides possibility to change it to 'Return to backlog'.
                # Cause it's the same that we already have we won't show it one more time
                possible_workflows.insert(0, current_workflow.name)  # insert because of
                # setCurrentIndex() can have only positive value

            issue_widget.set_workflow.addItems(possible_workflows)
            issue_widget.set_workflow.setCurrentIndex(0)

            issue_widget.set_workflow.activated[str].connect(
                partial(
                    self.controller.change_workflow,
                    issue['workflow'],
                    issue['issue_obj'],
                )
            )

            # add issue item to list
            issue_list_widget_item = QListWidgetItem(self.issue_list_widget)
            issue_list_widget_item.setSizeHint(issue_widget.sizeHint())
            self.issue_list_widget.addItem(issue_list_widget_item)
            self.issue_list_widget.setItemWidget(
                issue_list_widget_item, issue_widget
            )
