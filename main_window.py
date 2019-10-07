from PyQt5.QtWidgets import (
    QWidget,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QGridLayout,
    QLineEdit
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from functools import partial

from center_window import CenterWindow
from config import QSS_PATH


class QCustomWidget(QWidget):
    """ Custom list item
    Displays the issue key, title and a shorthand
    for the time estimated/spent/remaining
    """

    def __init__(self):
        super().__init__()

        with open(QSS_PATH, "r") as qss_file:
            self.setStyleSheet(qss_file.read())

        self.estimated_label = QLabel()
        self.estimated_label.setObjectName('estimated_label')
        self.spent_label = QLabel()
        self.spent_label.setObjectName('spent_label')
        self.remaining_label = QLabel()
        self.remaining_label.setObjectName('remaining_label')
        self.logwork_btn = QPushButton('Log work')
        self.logwork_btn.setObjectName('logwork_btn')
        self.logwork_btn.setMaximumSize(self.logwork_btn.size())

        timetracking_grid = QGridLayout()
        timetracking_grid.addWidget(self.estimated_label, 0, 0)
        timetracking_grid.addWidget(self.spent_label, 0, 1)
        timetracking_grid.addWidget(self.remaining_label, 0, 2)
        timetracking_grid.addWidget(self.logwork_btn, 0, 3, Qt.AlignRight)

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

        with open('qss/style.qss', "r") as qss_file:
            self.setStyleSheet(qss_file.read())

        self.controller = controller
        self.resize(800, 450)
        self.center()
        self.setWindowTitle('JIRA Quick Reporter')
        self.setWindowIcon(QIcon('logo.png'))

        self.main_box = QVBoxLayout()
        self.hbox = QHBoxLayout()
        self.list_box = QVBoxLayout()
        self.create_filter_box = QHBoxLayout()
        self.my_filters_list = QListWidget()
        self.my_filters_list.itemSelectionChanged.connect(
            self.controller.filter_selected
        )

        self.hbox.addWidget(self.my_filters_list)
        self.hbox.addLayout(self.list_box, Qt.AlignCenter)

        self.btn_box = QHBoxLayout()

        filter_label = QLabel('Create filter: ')
        self.filter_field = QLineEdit()
        self.filter_button = QPushButton('Save')
        self.filter_button.clicked.connect(self.controller.save_filter)
        self.create_filter_box.addWidget(filter_label)
        self.create_filter_box.addWidget(self.filter_field)
        self.create_filter_box.addWidget(self.filter_button)

        self.main_box.addLayout(self.create_filter_box)
        self.main_box.addLayout(self.hbox)
        self.main_box.addLayout(self.btn_box)
        self.setLayout(self.main_box)

        self.refresh_btn = QPushButton('Refresh')
        self.refresh_btn.clicked.connect(self.controller.filter_selected)
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
        issue_list_widget.setObjectName('issue_list')
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
                partial(self.controller.open_timelog_window, issue['key'])
            )

            # add issue item to list
            issue_list_widget_item = QListWidgetItem(issue_list_widget)
            issue_list_widget_item.setSizeHint(issue_widget.sizeHint())
            issue_list_widget.addItem(issue_list_widget_item)
            issue_list_widget.setItemWidget(
                issue_list_widget_item, issue_widget
            )

    def show_filters(self, filters_dict):
        for key in filters_dict.keys():
            self.my_filters_list.addItem(key)
        self.my_filters_list.setCurrentItem(self.my_filters_list.item(0))
        self.my_filters_list.setMaximumWidth(
            self.my_filters_list.sizeHintForColumn(0) + 10
        )

    def add_filter(self, filter):
        self.my_filters_list.addItem(filter)

    def get_current_filter(self):
        return self.my_filters_list.currentItem().text()

    def get_new_filter(self):
        return self.filter_field.text()

    def set_filter_jql_to_field(self, jql):
        self.filter_field.setText(jql)
