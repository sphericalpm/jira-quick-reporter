import os

from PyQt5.QtCore import QTimer, QTime, Qt, QSettings
from PyQt5.QtGui import QPixmap
from PyQt5.QtMultimedia import QSound
from PyQt5.QtWidgets import (
    QWidget,
    QProgressBar,
    QPushButton,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QDialog,
    QSizePolicy,
    QMessageBox,
    QFormLayout,
    QAction,
    QSlider
)

from center_window import CenterWindow
from config import (
    QSS,
    RING_SOUND_PATH,
    POMODORO_MARK_PATH,
    LOGGED_TIME_DIR
)

SHORT_BREAK = 'short'
LONG_BREAK = 'long'
POMODORO = 'pomodoro'


class BreakDialog(QDialog):
    def __init__(self, cur_break):
        super(BreakDialog, self).__init__()
        self.setWindowTitle('Break')
        self.cur_break = cur_break
        self.another_break = SHORT_BREAK if self.cur_break == LONG_BREAK else LONG_BREAK
        self.main_box = QVBoxLayout()
        self.setLayout(self.main_box)
        self.message_label = QLabel(
            'It is time for a {} break.'.format(self.cur_break)
        )
        self.message_label.setAlignment(Qt.AlignCenter)
        self.btn_box = QHBoxLayout()
        self.another_break_btn = QPushButton(
            'Start {} break'.format(self.another_break)
        )
        self.another_break_btn.clicked.connect(self.another_break_btn_click)
        self.skip_break_btn = QPushButton('Skip break')
        self.skip_break_btn.clicked.connect(self.skip_break_btn_click)

        self.main_box.addWidget(self.message_label)
        self.btn_box.addWidget(self.another_break_btn)
        self.btn_box.addWidget(self.skip_break_btn)
        self.main_box.addLayout(self.btn_box)

    def exec(self):
        super(BreakDialog, self).exec()
        return self.cur_break

    def another_break_btn_click(self):
        self.cur_break = self.another_break
        self.accept()

    def skip_break_btn_click(self):
        self.cur_break = POMODORO
        self.accept()


class Settings(QWidget):
    def __init__(self, pomodoro_window):
        super().__init__()
        self.setStyleSheet(QSS)
        self.setWindowTitle('Settings')
        self.pomodoro_window = pomodoro_window
        self.main_box = QFormLayout()
        self.setLayout(self.main_box)
        self.setMinimumWidth(500)

        self.pomodoro_time = self.pomodoro_window.time_dict[POMODORO].minute()
        self.long_break_time = self.pomodoro_window.time_dict[LONG_BREAK].minute()
        self.short_break_time = self.pomodoro_window.time_dict[SHORT_BREAK].minute()

        self.pomodoro_label = QLabel()
        self.pomodoro_label.setAlignment(Qt.AlignRight)
        self.long_label = QLabel()
        self.long_label.setAlignment(Qt.AlignRight)
        self.short_label = QLabel()
        self.short_label.setAlignment(Qt.AlignRight)

        self.pomodoro_slider = QSlider(Qt.Horizontal)
        self.pomodoro_slider.setRange(1, 45)
        self.pomodoro_slider.valueChanged.connect(self.pomodoro_change)
        self.pomodoro_slider.setValue(self.pomodoro_time)

        self.long_break_slider = QSlider(Qt.Horizontal)
        self.long_break_slider.valueChanged.connect(self.long_change)
        self.long_break_slider.setRange(1, 30)
        self.long_break_slider.setValue(self.long_break_time)

        self.short_break_slider = QSlider(Qt.Horizontal)
        self.short_break_slider.valueChanged.connect(self.short_change)
        self.short_break_slider.setRange(1, 10)
        self.short_break_slider.setValue(self.short_break_time)

        self.main_box.addRow(QLabel('Pomodoro duration'), self.pomodoro_label)
        self.main_box.addRow(self.pomodoro_slider)
        self.main_box.setSpacing(5)
        self.main_box.addRow(QLabel('Long break duration'), self.long_label)
        self.main_box.addRow(self.long_break_slider)
        self.main_box.addRow(QLabel('Short break duration'), self.short_label)
        self.main_box.addRow(self.short_break_slider)

    def pomodoro_change(self, minutes):
        self.pomodoro_label.setText('{} min'.format(minutes))
        self.pomodoro_window.update_time_from_settings(minutes, POMODORO)

    def long_change(self, minutes):
        self.long_label.setText('{} min'.format(minutes))
        self.pomodoro_window.update_time_from_settings(minutes, LONG_BREAK)

    def short_change(self, minutes):
        self.short_label.setText('{} min'.format(minutes))
        self.pomodoro_window.update_time_from_settings(minutes, SHORT_BREAK)

    def closeEvent(self, QCloseEvent):
        QCloseEvent.ignore()
        self.hide()


class PomodoroWindow(CenterWindow):
    def __init__(self, controller, issue_key, issue_title, tray_icon):
        super().__init__()
        self.center()
        self.setStyleSheet(QSS)
        self.controller = controller
        self.tray_icon = tray_icon
        if not os.path.exists(LOGGED_TIME_DIR):
            os.mkdir(LOGGED_TIME_DIR)
        self.LOG_PATH = os.path.join(
            LOGGED_TIME_DIR, '{}.txt'.format(issue_key)
        )
        self.setWindowTitle('Pomodoro Timer')
        self.settings = QSettings('Spherical', 'Jira Quick Reporter')
        pomodoro_settings = int(self.settings.value(POMODORO, 25))
        long_break_settings = int(self.settings.value(LONG_BREAK, 15))
        short_break_settings = int(self.settings.value(SHORT_BREAK, 5))

        self.time_dict = dict(
            short=QTime(0, short_break_settings, 0),
            long=QTime(0, long_break_settings, 0),
            pomodoro=QTime(0, pomodoro_settings, 0)
        )

        self.issue_key = issue_key
        self.issue_title = issue_title
        self.pomodoros_count = 0
        self.current_time_name = POMODORO
        self.is_active_timer = False
        self.logged_time = QTime(0, 0, 0)
        self.time = self.time_dict[POMODORO]
        self.time_in_seconds = QTime(0, 0, 0).secsTo(self.time)

        self.timer_box = QVBoxLayout()
        self.main_box = QHBoxLayout()
        self.setLayout(self.main_box)

        self.issue_label = QLabel(
            '{}: {}'.format(self.issue_key, self.issue_title)
        )
        self.issue_label.setAlignment(Qt.AlignCenter)
        self.issue_label.setObjectName('issue_label')
        self.issue_label.setWordWrap(True)
        self.issue_label.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed
        )

        self.pbar = QProgressBar()
        self.pbar.setRange(0, self.time_in_seconds)
        self.pbar.setValue(0)
        self.pbar.setTextVisible(False)
        self.timer = QTimer()

        self.timer.timeout.connect(self.handle_timer)
        self.time_label = QLabel()
        self.time_label.setObjectName('time_label')
        self.time_label.setText(self.time.toString('mm:ss'))
        self.time_label.setAlignment(Qt.AlignCenter)

        self.btns_box = QHBoxLayout()
        self.start_btn = QPushButton('Start')
        self.start_btn.clicked.connect(self.toggle_timer)

        self.stop_btn = QPushButton('Stop')
        self.stop_btn.clicked.connect(self.toggle_timer)

        self.logwork_btn = QPushButton('Log work')
        self.logwork_btn.clicked.connect(
            lambda: self.controller.open_timelog_from_pomodoro(issue_key)
        )
        self.logwork_btn.setEnabled(False)

        self.btns_box.addWidget(self.start_btn)
        self.btns_box.addWidget(self.stop_btn)
        self.btns_box.addWidget(self.logwork_btn)

        self.pomodoros_box = QHBoxLayout()
        self.pomodoros_box.setSpacing(5)
        self.pomodoros_count_label = QLabel()
        self.pomodoros_count_label.setObjectName('pomodoros_count')

        self.timer_box.addWidget(self.issue_label)
        self.timer_box.addStretch()
        self.timer_box.addWidget(self.time_label)
        self.timer_box.addWidget(self.pbar, Qt.AlignCenter)
        self.timer_box.addLayout(self.btns_box)
        self.timer_box.addLayout(self.pomodoros_box)
        self.timer_box.addStretch()
        self.main_box.addLayout(self.timer_box)

        self.action_show_time = QAction(self)
        self.action_show_time.setEnabled(False)
        self.action_open_timer = QAction('Open timer', self)
        self.action_open_timer.triggered.connect(self.show)
        self.action_quit_timer = QAction('Quit timer', self)
        self.action_quit_timer.triggered.connect(self.quit)
        self.action_settings = QAction('Settings', self)

        self.settings_window = Settings(self)

        self.action_settings.triggered.connect(self.settings_window.show)
        self.action_reset = QAction('Reset timer', self)
        self.action_reset.triggered.connect(self.reset_timer)
        self.action_start_timer = QAction('Start', self)
        self.action_start_timer.triggered.connect(self.toggle_timer)
        self.action_stop_timer = QAction('Stop', self)
        self.action_stop_timer.triggered.connect(self.toggle_timer)
        self.action_log_work = QAction('Log work', self)
        self.action_log_work.triggered.connect(
            lambda: self.controller.open_timelog_from_pomodoro(issue_key)
        )
        self.action_log_work.setEnabled(False)

        self.tray_icon.contextMenu().addSeparator()
        self.tray_icon.contextMenu().addAction(self.action_show_time)
        self.action_show_time.setText(self.time.toString('mm:ss'))
        self.tray_icon.contextMenu().addAction(self.action_open_timer)
        self.tray_icon.contextMenu().addAction(self.action_settings)
        self.tray_icon.contextMenu().addAction(self.action_quit_timer)
        self.tray_icon.contextMenu().addSeparator()
        self.tray_icon.contextMenu().addAction(self.action_start_timer)
        self.tray_icon.contextMenu().addAction(self.action_stop_timer)
        self.tray_icon.contextMenu().addAction(self.action_reset)
        self.tray_icon.contextMenu().addAction(self.action_log_work)

    def log_work_if_file_exists(self):
        if os.path.exists(self.LOG_PATH):
            reply = QMessageBox.question(
                self,
                'Warning',
                'You have not logged your work.\n Do you want to log it?',
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.controller.open_timelog_from_pomodoro(self.issue_key)
            else:
                os.remove(self.LOG_PATH)

    def update_time_from_settings(self, minutes, time_name):
        if self.current_time_name != time_name:
            self.time_dict[time_name].setHMS(0, minutes, 0)
        elif not self.is_active_timer:
            self.time_dict[time_name].setHMS(0, minutes, 0)
            self.update_timer()
        elif self.time_dict[time_name].minute() > minutes:
            spent_time_seconds = self.time.secsTo(self.time_dict[time_name])
            if minutes <= spent_time_seconds // 60:
                self.stop_timer()
                QSound.play(RING_SOUND_PATH)
                self.set_timer()
            else:
                time_diff = self.time_dict[time_name].minute() - minutes
                self.change_timer(minutes, -time_diff)
        elif self.time_dict[time_name].minute() < minutes:
            time_diff = minutes - self.time_dict[time_name].minute()
            self.change_timer(minutes, time_diff)

    def change_timer(self, minutes, time_diff):
        self.time_dict[self.current_time_name].setHMS(0, minutes, 0)
        self.time = self.time.addSecs(time_diff * 60)
        self.time_in_seconds = minutes * 60
        self.pbar.setMaximum(self.time_in_seconds)
        self.time_label.setText(self.time.toString('mm:ss'))
        self.action_show_time.setText(self.time.toString('mm:ss'))

    def handle_timer(self):
        """
        Updates timer label and progress bar every second
        until time is over
        """

        value = self.pbar.value()
        if value < self.time_in_seconds:
            value += 1
            self.pbar.setValue(value)
            self.time = self.time.addSecs(-1)
            self.time_label.setText(self.time.toString('mm:ss'))
            self.action_show_time.setText(self.time.toString('mm:ss'))
            if not value % 60:
                self.log_time()
        else:
            self.stop_timer()
            QSound.play(RING_SOUND_PATH)
            if self.current_time_name != POMODORO:
                self.tray_icon.showMessage(
                    'Pomodoro',
                    'Your break is over',
                    msecs=2000)
            self.set_timer()

    def update_timer(self):
        self.time_in_seconds = QTime(0, 0, 0).secsTo(self.time)
        self.pbar.setMaximum(self.time_in_seconds)
        self.pbar.setValue(0)
        self.time_label.setText(self.time.toString('mm:ss'))
        self.action_show_time.setText(self.time.toString('mm:ss'))

    def set_pomodoro_timer(self):
        self.is_active_timer = False
        self.current_time_name = POMODORO
        self.time = self.time_dict[POMODORO]
        self.update_timer()

    def set_pomodoro_count(self):
        """
        Set pomodoro mark and number of past pomodoros
        """

        self.clear_pomodoros()
        label = QLabel()
        pixmap = QPixmap(POMODORO_MARK_PATH)
        label.setPixmap(pixmap)
        self.pomodoros_box.addWidget(self.pomodoros_count_label)
        self.pomodoros_count_label.setSizePolicy(
                QSizePolicy.Fixed, QSizePolicy.Expanding
            )
        self.pomodoros_box.addWidget(label)
        self.pomodoros_count_label.setText(str(self.pomodoros_count))

    def set_pomodoro_img(self):
        label = QLabel()
        pixmap = QPixmap(POMODORO_MARK_PATH)
        label.setPixmap(pixmap)
        if self.pomodoros_count > 1:
            self.pomodoros_box.itemAt(
                self.pomodoros_count - 2
            ).widget().setSizePolicy(
                QSizePolicy.Fixed, QSizePolicy.Expanding
            )
        self.pomodoros_box.addWidget(label)

    def clear_pomodoros(self):
        for _ in range(self.pomodoros_box.count()):
            self.pomodoros_box.itemAt(0).widget().setParent(None)

    def toggle_timer(self):
        sender = self.sender().text()
        if sender in ['Start', 'Resume']:
            self.start_timer()
        elif sender == 'Pause':
            self.pause_timer()
        else:
            self.stop_timer()
            self.set_pomodoro_timer()

    def log_time(self):
        self.logged_time = self.logged_time.addSecs(60)
        with open(self.LOG_PATH, 'w') as log_file:
            log_file.write(self.logged_time.toString('h:m'))

    def start_timer(self):
        self.is_active_timer = True
        # change style before a break
        if self.current_time_name != POMODORO:
            self.issue_label.setObjectName('issue_label_break')
            self.issue_label.setStyleSheet('issue_label_break')
            self.pbar.setObjectName('break')
            self.pbar.setStyleSheet('break')
            self.stop_btn.hide()
            self.start_btn.setText('Stop')
            self.action_start_timer.setEnabled(False)
        else:
            self.tray_icon.showMessage(
                'Pomodoro',
                'Focus on your task',
                msecs=2000
            )
            self.start_btn.setText('Pause')
            self.action_start_timer.setText('Pause')
        self.logwork_btn.setEnabled(False)
        self.action_log_work.setEnabled(False)
        self.timer.start(1000)

    def stop_timer(self):
        self.timer.stop()
        self.is_active_timer = False
        self.start_btn.setText('Start')
        self.action_start_timer.setText('Start')
        self.logwork_btn.setEnabled(True)
        self.action_log_work.setEnabled(True)
        if self.current_time_name != POMODORO:
            self.stop_btn.show()
            self.action_start_timer.setEnabled(True)

        # change style after a break
        self.issue_label.setObjectName('issue_label')
        self.issue_label.setStyleSheet('issue_label')
        self.pbar.setObjectName('')
        self.pbar.setStyleSheet('')

    def pause_timer(self):
        self.timer.stop()
        self.start_btn.setText('Resume')
        self.action_start_timer.setText('Resume')
        self.logwork_btn.setEnabled(True)
        self.action_log_work.setEnabled(True)

    def reset_timer(self):
        self.logwork_btn.setEnabled(False)
        self.action_log_work.setEnabled(False)
        self.stop_timer()
        self.pomodoros_count = 0
        self.logged_time.setHMS(0, 0, 0)
        self.clear_pomodoros()
        self.set_pomodoro_timer()
        if os.path.exists(self.LOG_PATH):
            os.remove(self.LOG_PATH)

    def set_pomodoro_mark(self):
        if self.pomodoros_count < 5:
            self.set_pomodoro_img()
        elif self.pomodoros_count == 5:
            self.set_pomodoro_count()
        else:
            self.pomodoros_count_label.setText(
                str(self.pomodoros_count)
            )

    def set_timer(self):
        """
        In this method decides which timer will go next
        """

        # if pomodoro time's up
        if self.current_time_name == POMODORO:
            self.pomodoros_count += 1
            self.set_pomodoro_mark()

            # if four pomodoros have completed
            if not self.pomodoros_count % 4:
                self.current_time_name = LONG_BREAK
            else:
                self.current_time_name = SHORT_BREAK
            dialog = BreakDialog(self.current_time_name)

            # close dialog after 4 seconds
            QTimer.singleShot(4000, dialog.close)

            # get break name (short, long or skip) from dialog
            self.current_time_name = dialog.exec()
            if self.current_time_name != POMODORO:
                self.time = self.time_dict[self.current_time_name]
                self.update_timer()
                self.start_timer()
                return

        # if break time's up
        self.set_pomodoro_timer()

    def quit(self):
        if os.path.exists(self.LOG_PATH):
            reply = QMessageBox.question(
                self,
                'Warning',
                'You did not log your work. \nAre you sure you want to exit?',
                QMessageBox.Yes, QMessageBox.No
            )
            if reply == QMessageBox.No:
                return False

        self.settings.setValue(
            POMODORO, self.time_dict[POMODORO].minute()
        )
        self.settings.setValue(
            LONG_BREAK, self.time_dict[LONG_BREAK].minute()
        )
        self.settings.setValue(
            SHORT_BREAK, self.time_dict[SHORT_BREAK].minute()
        )
        self.settings.sync()
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.close()
        return True

    def closeEvent(self, event):
        if self.testAttribute(Qt.WA_DeleteOnClose):
            self.controller.pomodoro_view = None
            event.accept()
        else:
            event.ignore()
            self.hide()
