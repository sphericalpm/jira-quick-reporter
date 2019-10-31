from functools import partial

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon
from PyQt5.QtMultimedia import QSound
from PyQt5.QtWidgets import (
    QWidget,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QGridLayout,
    QSystemTrayIcon,
    QMenu,
    QAction,
    QSizePolicy,
)

from redefined_QComboBox import MyQComboBox
from center_window import CenterWindow
from config import (
    QSS,
    LOGO_PATH,
    LOG_TIME,
    RING_SOUND_PATH
)


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

        self.set_workflow = MyQComboBox(self)

        timetracking_grid = QGridLayout()
        timetracking_grid.addWidget(self.estimated_label, 0, 0)
        timetracking_grid.addWidget(self.spent_label, 0, 1)
        timetracking_grid.addWidget(self.remaining_label, 0, 2)
        timetracking_grid.addWidget(self.set_workflow, 0, 3, Qt.AlignRight)

        # create labels for issue key and title
        self.issue_key_label = QLabel()
        self.issue_title_label = QLabel()
        self.issue_title_label.setObjectName('issue_title_label')
        self.issue_title_label.setWordWrap(True)
        self.issue_key_label.setOpenExternalLinks(True)

        self.hbox = QHBoxLayout()
        self.issue_menu_btn = QPushButton('. . .')
        self.issue_menu_btn.setObjectName('issue_menu_btn')
        issue_menu = QMenu()
        self.action_log_work = QAction('Log work', self)
        self.action_pomodoro_timer = QAction('Pomodoro timer', self)
        issue_menu.addAction(self.action_log_work)
        issue_menu.addAction(self.action_pomodoro_timer)
        self.issue_menu_btn.setMenu(issue_menu)

        self.hbox.addWidget(self.issue_key_label, Qt.AlignLeft)
        self.hbox.addWidget(self.issue_menu_btn, Qt.AlignRight)
        self.issue_menu_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        # create main box layout
        vbox = QVBoxLayout()
        vbox.addLayout(self.hbox)
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

        self.setStyleSheet(QSS)
        self.controller = controller
        self.resize(800, 450)
        self.setWindowTitle('JIRA Quick Reporter')
        self.setWindowIcon(QIcon(LOGO_PATH))

        self.main_box = QVBoxLayout()
        self.list_box = QVBoxLayout()
        self.btn_box = QHBoxLayout()

        self.issue_list_widget = QListWidget(self)
        self.list_box.addWidget(self.issue_list_widget)

        self.label_info = QLabel('You have no issues.')
        self.label_info.setAlignment(Qt.AlignCenter)
        self.list_box.addWidget(self.label_info)
        self.label_info.hide()

        self.main_box.addLayout(self.list_box)
        self.main_box.addLayout(self.btn_box)
        self.setLayout(self.main_box)

        self.refresh_btn = QPushButton('Refresh')
        self.refresh_btn.clicked.connect(self.controller.refresh_issue_list)
        self.btn_box.addWidget(self.refresh_btn, alignment=Qt.AlignRight)

        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon(LOGO_PATH))

        self.tray_menu = QMenu()
        self.action_open = QAction('Open JQR', self)
        self.action_quit = QAction('Quit JQR', self)
        self.tray_menu.addAction(self.action_open)
        self.action_open.triggered.connect(self.show)
        self.tray_menu.addAction(self.action_quit)
        self.action_quit.triggered.connect(self.controller.quit_app)
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.show()
        self.timer_log_work = QTimer()
        self.timer_log_work.timeout.connect(self.notification_to_log_work)
        self.timer_log_work.start(LOG_TIME)

        self.timer_refresh = QTimer()
        self.timer_refresh.timeout.connect(self.controller.refresh_issue_list)

    def notification_to_log_work(self):
        QSound.play(RING_SOUND_PATH)
        self.tray_icon.showMessage(
            '1 hour had passed',
            'Don\'t forget to log your work!',
            msecs=2000
        )
        self.timer_log_work.start(LOG_TIME)

    def update_issues(self, update_list):
        for issue in update_list:
            item = self.issue_list_widget.findItems(
                issue['key'], Qt.MatchExactly
            )[0]
            item.setText(issue['key'])
            issue_widget = self.issue_list_widget.itemWidget(item)
            issue_widget.set_issue_key(issue['key'], issue['link'])
            issue_widget.set_issue_title(issue['title'])
            issue_widget.set_time(
                issue['estimated'],
                issue['logged'],
                issue['remaining']
            )
            issue_widget.set_workflow.clear()
            issue_widget.set_workflow.addItems(issue['workflow'])
            issue_widget.set_workflow.setCurrentIndex(0)

    def delete_issues(self, delete_list):
        for issue in delete_list:
            item = self.issue_list_widget.findItems(
                issue['key'], Qt.MatchExactly
            )[0]
            self.issue_list_widget.takeItem(
                self.issue_list_widget.row(item)
            )

    def insert_issues(self, new_issues_list):
        for issue in new_issues_list:
            issue_widget = QCustomWidget()
            issue_widget.set_issue_key(issue['key'], issue['link'])
            issue_widget.set_issue_title(issue['title'])
            issue_widget.set_time(
                issue['estimated'],
                issue['logged'],
                issue['remaining']
            )

            issue_widget.action_log_work.triggered.connect(
                partial(
                    self.controller.open_timelog_window,
                    issue['key']
                )
            )

            issue_widget.action_pomodoro_timer.triggered.connect(
                partial(
                    self.controller.open_pomodoro_window,
                    issue['key'], issue['title']
                )
            )

            # add workflow statuses to dropdown
            possible_workflows = self.controller.get_possible_workflows(issue)

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
            issue_list_widget_item = QListWidgetItem()
            issue_list_widget_item.setText(issue['key'])
            issue_list_widget_item.setSizeHint(issue_widget.sizeHint())
            self.issue_list_widget.insertItem(issue['index'], issue_list_widget_item)
            self.issue_list_widget.setItemWidget(
                issue_list_widget_item, issue_widget
            )

    def show_no_issues(self):
        self.issue_list_widget.clear()
        self.issue_list_widget.hide()
        self.label_info.show()

    def set_workflow_current_state(self, issue_key):
        item = self.issue_list_widget.findItems(
            issue_key, Qt.MatchExactly
        )[0]
        custom_item = self.issue_list_widget.itemWidget(item)
        custom_item.set_workflow.setCurrentIndex(0)

    def wheelEvent(self, event):
        if event.angleDelta().y() < 0:
            self.controller.refresh_issue_list(True)
            event.accept()

    def closeEvent(self, QCloseEvent):
        QCloseEvent.ignore()
        self.hide()
