from PyQt5.QtMultimedia import QSound
from PyQt5.QtWidgets import (
    QProgressBar,
    QPushButton,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QDialog,
    QSizePolicy,
    QMessageBox,
    QSpinBox,
    QFormLayout,
    QFrame
)
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import QTimer, QTime, Qt

from center_window import CenterWindow
from config import QSS_PATH, RINGING_SOUND_PATH, POMODORO_MARK_PATH

SHORT_BREAK = 'short'
LONG_BREAK = 'long'
SKIP_BREAK = 'skip'
POMODORO = 'pomodoro'


class CustomDialog(QDialog):
    def __init__(self, parent, cur_break):
        super(CustomDialog, self).__init__(parent=parent)
        self.resize(200, 200)
        self.cur_break = cur_break
        self.return_break = SKIP_BREAK
        self.main_box = QVBoxLayout()
        self.setLayout(self.main_box)
        self.message_label = QLabel(
            'Your pomodoro is over. '
            '\nIt is time for a {} break.'.format(self.cur_break)
        )
        self.message_label.setAlignment(Qt.AlignCenter)
        self.message_label.setObjectName('break_label')

        self.short_break_btn = QPushButton('Start short break')
        self.short_break_btn.clicked.connect(self.short_break_btn_click)
        self.long_break_btn = QPushButton('Start long break')
        self.long_break_btn.clicked.connect(self.long_break_btn_click)
        self.skip_break_btn = QPushButton('Skip break')
        self.skip_break_btn.clicked.connect(self.skip_break_btn_click)

        if self.cur_break == 'short':
            self.short_break_btn.setObjectName('cur_break_btn')
        else:
            self.long_break_btn.setObjectName('cur_break_btn')

        self.main_box.addWidget(self.message_label)
        self.main_box.addWidget(self.long_break_btn)
        self.main_box.addWidget(self.skip_break_btn)
        self.main_box.addWidget(self.short_break_btn)

    def exec(self):
        super(CustomDialog, self).exec()
        return self.return_break

    def short_break_btn_click(self):
        self.return_break = SHORT_BREAK
        self.accept()

    def long_break_btn_click(self):
        self.return_break = LONG_BREAK
        self.accept()

    def skip_break_btn_click(self):
        self.return_break = SKIP_BREAK
        self.accept()


class PomodoroWindow(CenterWindow):
    def __init__(self, controller, issue_key, issue_title):
        super().__init__()
        self.controller = controller
        with open(QSS_PATH, "r") as qss_file:
            self.setStyleSheet(qss_file.read())
        self.setWindowTitle('Pomodoro Timer')
        self.time_dict = dict(
            short=QTime(0, 5, 0),
            long=QTime(0, 15, 0),
            pomodoro=QTime(0, 25, 0)
        )
        self.issue_key = issue_key
        self.issue_title = issue_title
        self.pomodoros_count = 0
        self.next_time_name = POMODORO
        self.active_time_name = None
        self.past_pomodoros_time = QTime(0, 0, 0)
        self.time = self.time_dict[POMODORO]
        self.time_in_seconds = QTime(0, 0, 0).secsTo(self.time)

        self.timer_box = QVBoxLayout()
        self.frame_settings = QFrame()
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
        self.pbar.setMaximum(self.time_in_seconds)
        self.pbar.setValue(0)
        self.pbar.setTextVisible(False)
        self.timer = QTimer()

        self.timer.timeout.connect(self.handle_timer)
        self.time_label = QLabel()
        self.time_label.setObjectName('time_label')
        self.time_label.setText(self.time.toString('mm:ss'))
        self.time_label.setAlignment(Qt.AlignCenter)

        self.btns_box = QHBoxLayout()
        self.timer_btn = QPushButton('Start')
        self.timer_btn.clicked.connect(self.toggle_timer)

        self.reset_btn = QPushButton('Reset')
        self.reset_btn.clicked.connect(self.reset)

        self.logwork_btn = QPushButton('Log work')
        self.logwork_btn.clicked.connect(
            lambda: self.controller.open_timelog_from_pomodoro(issue_key)
        )
        self.logwork_btn.setEnabled(False)

        self.settings_btn = QPushButton('Settings')
        self.settings_btn.clicked.connect(self.open_settings)

        self.btns_box.addWidget(self.timer_btn)
        self.btns_box.addWidget(self.reset_btn)
        self.btns_box.addWidget(self.logwork_btn)
        self.btns_box.addWidget(self.settings_btn)

        self.pomodoros_box = QHBoxLayout()
        self.pomodoros_box.setSpacing(5)
        self.pomodoros_count_label = QLabel()
        self.pomodoros_count_label.setObjectName('pomodoros_count')

        self.pomodoro_time_settings = QSpinBox()
        self.pomodoro_time_settings.setRange(1, 45)
        self.long_break_settings = QSpinBox()
        self.long_break_settings.setRange(1, 30)
        self.short_break_settings = QSpinBox()
        self.short_break_settings.setRange(1, 10)
        self.save_settings_btn = QPushButton('Save')
        self.save_settings_btn.clicked.connect(self.save_time_settings)

        self.settings_form = QFormLayout(self.frame_settings)
        self.settings_form.addRow(QLabel('Pomodoro time'), self.pomodoro_time_settings)
        self.settings_form.addRow(QLabel('Long break'), self.long_break_settings)
        self.settings_form.addRow(QLabel('Short break'), self.short_break_settings)
        self.settings_form.addRow(self.save_settings_btn)
        self.frame_settings.hide()

        self.timer_box.addWidget(self.issue_label)
        self.timer_box.addStretch()
        self.timer_box.addWidget(self.time_label)
        self.timer_box.addWidget(self.pbar, Qt.AlignCenter)
        self.timer_box.addLayout(self.btns_box)
        self.timer_box.addLayout(self.pomodoros_box)
        self.timer_box.addStretch()
        self.main_box.addLayout(self.timer_box)
        self.main_box.addWidget(self.frame_settings)

    def save_time_settings(self):
        if self.pomodoro_time_settings.isEnabled():
            self.time_dict[POMODORO].setHMS(
                0,
                self.pomodoro_time_settings.value(),
                0
            )
        if self.long_break_settings.isEnabled():
            self.time_dict[LONG_BREAK].setHMS(
                0,
                self.long_break_settings.value(),
                0
            )
        if self.short_break_settings.isEnabled():
            self.time_dict[SHORT_BREAK].setHMS(
                0,
                self.short_break_settings.value(),
                0
            )
        if not self.active_time_name:
            self.time = self.time_dict[self.next_time_name]
            self.update_timer()

    def open_settings(self):
        if self.frame_settings.isHidden():
            self.frame_settings.show()
        else:
            self.frame_settings.hide()

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
        else:
            self.stop_timer()
            QSound.play(RINGING_SOUND_PATH)
            if self.next_time_name is POMODORO:
                self.log_time()
                self.reset_btn.setText('Reset')
            self.set_timer()

    def update_timer(self):
        self.time_in_seconds = QTime(0, 0, 0).secsTo(self.time)
        self.pbar.setMaximum(self.time_in_seconds)
        self.pbar.setValue(0)
        self.time_label.setText(self.time.toString('mm:ss'))

    def set_pomodoro_timer(self):
        self.next_time_name = POMODORO
        self.time = self.time_dict[POMODORO]
        self.update_timer()

    def stop_timer(self):
        self.timer.stop()
        self.timer_btn.setText('Start')
        #self.reset_btn.setText('Reset')
        self.settings_btn.setEnabled(True)
        if self.next_time_name is not POMODORO or not QTime(0, 0, 0).secsTo(self.time):
            self.active_time_name = None
            self.set_settings_enable(pomodoro=False)

        # change style after a break
        self.issue_label.setObjectName('issue_label')
        self.issue_label.setStyleSheet('issue_label')
        self.pbar.setObjectName('')
        self.pbar.setStyleSheet('')

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

    def set_pomodoro_mark(self):
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
        for i in range(self.pomodoros_box.count()):
            self.pomodoros_box.itemAt(0).widget().setParent(None)

    def set_settings_enable(self, pomodoro=True, long_break=True, short_break=True):
        self.pomodoro_time_settings.setEnabled(pomodoro)
        self.long_break_settings.setEnabled(long_break)
        self.short_break_settings.setEnabled(short_break)

    def toggle_timer(self):
        if self.timer_btn.text() == 'Start':
            # change style before a break
            if self.next_time_name is not POMODORO:
                self.issue_label.setObjectName('issue_label_break')
                self.issue_label.setStyleSheet('issue_label_break')
                self.pbar.setObjectName('break')
                self.pbar.setStyleSheet('break')
                self.reset_btn.setEnabled(False)
                if self.next_time_name is SHORT_BREAK:
                    self.set_settings_enable(short_break=False)
                else:
                    self.set_settings_enable(long_break=False)
            else:
                self.reset_btn.setText('Cancel Pomodoro')
                self.set_settings_enable(pomodoro=False)

            self.logwork_btn.setEnabled(False)
            self.timer.start(1000)
            self.timer_btn.setText('Stop')
            self.active_time_name = self.next_time_name
        else:
            self.stop_timer()
            if self.next_time_name is POMODORO:
                self.log_time()
            else:
                self.set_pomodoro_timer()

    def log_time(self):
        cur_time_secs = QTime(0, 0, 0).secsTo(self.time)
        spent_time = self.time_dict[POMODORO].addSecs(-cur_time_secs)
        self.past_pomodoros_time = spent_time

    def reset(self):
        print('reset')
        self.active_time_name = None
        self.set_settings_enable()
        self.logwork_btn.setEnabled(False)
        print(self.logwork_btn.isEnabled())

        if self.reset_btn.text() is 'Reset':
            self.pomodoros_count = 0
            self.past_pomodoros_time.setHMS(0, 0, 0)
            self.clear_pomodoros()
            self.set_pomodoro_timer()
        else:
            self.stop_timer()
            self.past_pomodoros_time.setHMS(0, 0, 0)
            self.set_pomodoro_timer()
            self.reset_btn.setText('Reset')

    def set_timer(self):
        """
        In this method decides which timer will go next
        """

        # if pomodoro time's up
        if self.next_time_name is POMODORO:
            self.pomodoros_count += 1
            if self.pomodoros_count < 5:
                self.set_pomodoro_mark()
            elif self.pomodoros_count == 5:
                self.set_pomodoro_count()
            else:
                self.pomodoros_count_label.setText(
                    str(self.pomodoros_count)
                )

            # if four pomodoros have completed
            if not self.pomodoros_count % 4:
                self.next_time_name = LONG_BREAK
            else:
                self.next_time_name = SHORT_BREAK
            self.dialog = CustomDialog(self, self.next_time_name)
            self.next_time_name = self.dialog.exec()
        else:
            self.next_time_name = POMODORO
        if self.next_time_name is not SKIP_BREAK:
            self.time = self.time_dict[self.next_time_name]
        else:
            self.time = self.time_dict[POMODORO]

        self.update_timer()
        if self.next_time_name not in(POMODORO, SKIP_BREAK):
            self.toggle_timer()
        else:
            self.set_pomodoro_timer()

    def get_past_pomodoros_time(self):
        if self.past_pomodoros_time.second():
            print('yes')
            return self.past_pomodoros_time.addSecs(60).toString('h:m')
        else:
            return self.past_pomodoros_time.toString('h:m')

    def closeEvent(self, event):
        if self.pomodoros_count:
            reply = QMessageBox.question(
                self, 'Message',
                'You did not log your work. \nAre you sure you want to exit?',
                QMessageBox.Yes, QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
