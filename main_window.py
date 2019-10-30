from functools import partial

from PyQt5.QtCore import Qt, QTimer, QEvent, QUrl
from PyQt5.QtGui import QIcon, QDesktopServices
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
    QLineEdit,
    QSystemTrayIcon,
    QMenu,
    QMessageBox,
    QAction,
    QSizePolicy,
    QComboBox,
    QFrame,
    QStyle
)

from center_window import CenterWindow
from config import (
    QSS,
    LOGO_PATH,
    LOG_TIME,
    RING_SOUND_PATH,
    FILTER_FIELD_HELP_URL,
    DEFAULT_FILTERS
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

        self.set_workflow = QComboBox(self)

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
        self.resize(800, 450)
        self.setWindowTitle('JIRA Quick Reporter')
        self.setWindowIcon(QIcon(LOGO_PATH))
        self.current_item = None

        self.vbox = QVBoxLayout()

        self.save_btn_box = QHBoxLayout()
        self.filter_name_label = QLabel()
        self.filter_name_label.setObjectName('filter_name_label')
        self.filter_name_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.filter_name_label.setAlignment(Qt.AlignLeft)
        self.filter_edited_label = QLabel('-> edited')
        self.filter_edited_label.setObjectName('filter_edited_label')
        self.filter_edited_label.hide()
        self.filter_edited_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.save_filter_btn = QPushButton('Save as')
        self.save_filter_btn.setObjectName('save_filter_btn')
        self.save_filter_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.save_filter_btn.clicked.connect(self.controller.save_filter)

        self.overwrite_filter_button = QPushButton('Save')
        self.overwrite_filter_button.setToolTip('You need to edit filter query first')
        self.overwrite_filter_button.setObjectName('save_filter_btn')
        self.overwrite_filter_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.overwrite_filter_button.clicked.connect(self.controller.save_existing_filter)

        self.save_btn_box.addWidget(self.filter_name_label, Qt.AlignLeft)
        self.save_btn_box.addWidget(self.filter_edited_label, Qt.AlignLeft)
        self.save_btn_box.addWidget(self.save_filter_btn, Qt.AlignLeft)
        self.save_btn_box.addWidget(self.overwrite_filter_button, Qt.AlignLeft)
        self.save_btn_box.addStretch()

        self.create_filter_box = QHBoxLayout()
        self.filter_field = QLineEdit()
        self.filter_field.setObjectName('filter_field')
        self.action_help = QAction()
        self.action_help.setIcon(self.style().standardIcon(QStyle.SP_MessageBoxQuestion))
        self.help_filter_url = QUrl(FILTER_FIELD_HELP_URL)
        self.action_help.triggered.connect(self.filter_field_help)
        self.filter_field.addAction(self.action_help, QLineEdit.TrailingPosition)
        self.filter_field.installEventFilter(self)
        self.search_issues_button = QPushButton('Search')
        self.search_issues_button.setObjectName('search_issues_button')
        self.search_issues_button.clicked.connect(self.controller.search_issues_by_filter)
        self.create_filter_box.addWidget(self.filter_field)
        self.create_filter_box.addWidget(self.search_issues_button)

        self.list_box = QVBoxLayout()
        self.issue_list_widget = QListWidget(self)
        self.issue_list_widget.setObjectName('issue_list')

        self.vbox.addLayout(self.save_btn_box)
        self.vbox.addLayout(self.create_filter_box)
        self.vbox.addLayout(self.list_box)

        self.filters_frame = QFrame()
        self.filters_frame.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.filters_frame.setFrameShape(QFrame.StyledPanel)
        self.filters_frame.setObjectName('filters_frame')
        self.filters_frame.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.filters_box = QVBoxLayout(self.filters_frame)
        self.filters_box_label = QLabel('Issues and filters')
        self.filters_box_label.setObjectName('filters_box_label')
        self.filters_box.addWidget(self.filters_box_label)
        self.filters_list = QListWidget()
        self.filters_list.installEventFilter(self)
        self.filters_list.itemClicked.connect(self.on_filter_selected)
        self.filters_list.setObjectName('filters_list')
        self.filters_box.addWidget(self.filters_list)

        self.load_more_issues_btn = QPushButton('Load more')
        width = self.load_more_issues_btn.fontMetrics().boundingRect(
            self.load_more_issues_btn.text()
        ).width() + 20
        self.load_more_issues_btn.setMaximumWidth(width)
        self.load_more_issues_btn.clicked.connect(
            lambda: self.controller.refresh_issue_list(True)
        )

        self.btn_box = QHBoxLayout()
        self.refresh_btn = QPushButton('Refresh')
        self.refresh_btn.clicked.connect(self.controller.refresh_issue_list)
        self.btn_box.addWidget(self.refresh_btn, alignment=Qt.AlignRight)
        self.vbox.addLayout(self.btn_box)

        self.toggle_frame_filters_btn = QPushButton('<')
        self.toggle_frame_filters_btn.clicked.connect(self.toggle_frame_filters)
        self.toggle_frame_filters_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.toggle_frame_filters_btn.setObjectName('toggle_filters_btn')

        self.main_box = QHBoxLayout()
        self.main_box.addWidget(self.filters_frame)
        self.main_box.addWidget(self.toggle_frame_filters_btn, alignment=Qt.AlignTop)
        self.main_box.addLayout(self.vbox)
        self.setLayout(self.main_box)

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
            issue_list_widget_item = QListWidgetItem(self.issue_list_widget)
            issue_list_widget_item.setSizeHint(issue_widget.sizeHint())
            self.issue_list_widget.addItem(issue_list_widget_item)
            self.issue_list_widget.setItemWidget(
                issue_list_widget_item, issue_widget
            )

    def show_filters(self, filters_dict):
        for key in filters_dict.keys():
            self.filters_list.addItem(key)
        self.filters_list.item(0).setText(self.filters_list.item(0).text().capitalize())

        # add separator after first item
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setObjectName('separator')
        item_separator = QListWidgetItem()
        item_separator.setFlags(Qt.NoItemFlags)
        self.filters_list.insertItem(1, item_separator)
        self.filters_list.setItemWidget(item_separator, separator)

        self.filters_list.setCurrentItem(self.filters_list.item(2))
        self.on_filter_selected(self.filters_list.currentItem())
        self.filters_list.setMaximumWidth(
            self.filters_list.sizeHintForColumn(0) + 10
        )

    def filter_field_help(self):
        QDesktopServices.openUrl(self.help_filter_url)

    def on_filter_selected(self, item):
        self.current_item = item
        self.filter_name_label.setText(item.text())
        self.controller.search_issues_by_filter_name(item)

        # if current filter is not 'Search issues'
        if self.filters_list.currentRow():
            # activate overwrite button
            self.overwrite_filter_button.show()
            self.overwrite_filter_button.setEnabled(False)
            self.save_filter_btn.hide()
        else:
            # activate save button
            self.overwrite_filter_button.hide()
            self.save_filter_btn.show()

    def toggle_frame_filters(self):
        if self.toggle_frame_filters_btn.text() == '<':
            self.toggle_frame_filters_btn.setText('>')
            self.filters_frame.hide()
        else:
            self.toggle_frame_filters_btn.setText('<')
            self.filters_frame.show()

    def eventFilter(self, object, event):
        # if user started typing in filter field
        if object is self.filter_field and event.type() == QEvent.KeyRelease:
            # if current filter is not 'Search issues'
            if self.filters_list.currentRow():
                current_filter_name = self.filters_list.currentItem().text()
                # if query of current filter has not changed
                if self.controller.get_filter_by_name(current_filter_name) != self.filter_field.text():
                    # show that filter has been edited
                    self.filter_edited_label.show()
                    self.overwrite_filter_button.setEnabled(True)
                else:
                    self.filter_edited_label.hide()
                    self.overwrite_filter_button.setEnabled(False)

        if event.type() == QEvent.ContextMenu:
            self.filters_list.setCurrentItem(self.current_item)
            if object.itemAt(event.pos()) is self.filters_list.currentItem():
                item_text = self.filters_list.currentItem().text().lower()
                if item_text in DEFAULT_FILTERS:
                    return super().eventFilter(object, event)
                context_menu = QMenu()
                action_delete = QAction('Delete', self)
                context_menu.addAction(action_delete)
                if context_menu.exec_(event.globalPos()):
                    reply = QMessageBox.question(
                        self,
                        'Delete filter',
                        'Are you sure wou want to delete '
                        '\'{}\' filter?'.format(item_text),
                        QMessageBox.Yes | QMessageBox.Cancel
                    )
                    if reply == QMessageBox.Yes:
                        self.controller.delete_filter(item_text)
                        self.filters_list.takeItem(
                            self.filters_list.currentRow()
                        )
                        self.filters_list.setCurrentRow(0)
                        self.on_filter_selected(self.filters_list.currentItem())
        return super().eventFilter(object, event)

    def closeEvent(self, QCloseEvent):
        QCloseEvent.ignore()
        self.hide()
