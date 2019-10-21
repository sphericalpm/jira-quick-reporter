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
    QSizePolicy
)

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

        timetracking_grid = QGridLayout()
        timetracking_grid.addWidget(self.estimated_label, 0, 0)
        timetracking_grid.addWidget(self.spent_label, 0, 1)
        timetracking_grid.addWidget(self.remaining_label, 0, 2)

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
        self.issue_key_label.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed
        )
        self.issue_menu_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.hbox.addWidget(self.issue_menu_btn, Qt.AlignRight)

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
        self.pomodoro_window = None
        self.selected_issue_key = None
        self.resize(800, 450)
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
        self.timer = QTimer()
        self.timer.timeout.connect(self.notification_to_log_work)
        self.timer.start(LOG_TIME)

    def notification_to_log_work(self):
        QSound.play(RING_SOUND_PATH)
        self.tray_icon.showMessage(
            '1 hour had passed',
            'Don\'t forget to log your work!',
            msecs=2000
        )
        self.timer.start(LOG_TIME)

    def show_issues_list(self, issues_list, load_more=False):
        # clear listbox
        if not load_more:
            for _ in range(self.list_box.count()):
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

            # add issue item to list
            issue_list_widget_item = QListWidgetItem(self.issue_list_widget)
            issue_list_widget_item.setSizeHint(issue_widget.sizeHint())
            self.issue_list_widget.addItem(issue_list_widget_item)
            self.issue_list_widget.setItemWidget(
                issue_list_widget_item, issue_widget
            )

    def closeEvent(self, QCloseEvent):
        QCloseEvent.ignore()
        self.hide()
