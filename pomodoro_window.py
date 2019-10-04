import sys

from PyQt5.QtWidgets import (
    QApplication,
    QProgressBar,
    QPushButton,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QDialog,
    QSizePolicy,
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QTimer, QTime, Qt

from center_window import CenterWindow
from config import QSS_PATH

SHORT_BREAK = 'short'
LONG_BREAK = 'long'
SKIP_BREAK = 'skip'
POMODORO = 'pomodoro'
TIME = dict(
    short=QTime(0, 0, 5),
    long=QTime(0, 0, 15),
    pomodoro=QTime(0, 0, 3)
)


class CustomDialog(QDialog):
    def __init__(self, parent, cur_break):
        super(CustomDialog, self).__init__(parent=parent)
        self.resize(200, 200)
        self.setWindowFlag(Qt.WindowCloseButtonHint, False)
        self.cur_break = cur_break
        self.return_break = SKIP_BREAK
        self.main_box = QVBoxLayout()
        self.setLayout(self.main_box)
        self.message_label = QLabel(
            'Your pomodoro is over. It is time for a {} break.'.format(self.cur_break)
        )
        self.message_label.setAlignment(Qt.AlignCenter)

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
    def __init__(self, issue_key, issue_title):
        super().__init__()
        self.setStyleSheet(open(QSS_PATH, 'r').read())
        self.resize(500, 200)
        self.setWindowTitle('Pomodoro Timer')
        self.issue_key = issue_key
        self.issue_title = issue_title
        self.pomodoros_count = 0
        self.cur_time = POMODORO
        self.time = TIME[POMODORO]
        self.time_in_seconds = self.get_time_in_seconds()

        self.main_box = QVBoxLayout()
        self.setLayout(self.main_box)

        self.issue_label = QLabel(
            '{}: {}'.format(self.issue_key, self.issue_title)
        )
        self.issue_label.setAlignment(Qt.AlignCenter)
        self.issue_label.setObjectName('issue_label')

        self.pbar = QProgressBar()
        self.pbar.setMaximum(self.time_in_seconds)
        self.pbar.setValue(0)
        self.pbar.setTextVisible(False)
        self.timer = QTimer()

        self.timer.timeout.connect(self.handle_timer)
        self.time_label = QLabel()
        self.time_label.setObjectName('time_label')
        self.time_label.setText(self.time.toString())
        self.time_label.setAlignment(Qt.AlignCenter)

        self.btns_box = QHBoxLayout()
        self.timer_btn = QPushButton('Start')
        self.timer_btn.clicked.connect(self.toggle_timer)

        self.reset_btn = QPushButton('Reset')
        self.reset_btn.clicked.connect(self.reset_btn_click)

        self.logwork_btn = QPushButton('Log work')
        self.logwork_btn.clicked.connect(self.logwork_btn_click)

        self.btns_box.addWidget(self.timer_btn)
        self.btns_box.addWidget(self.reset_btn)
        self.btns_box.addWidget(self.logwork_btn)

        self.pomodoros_box = QHBoxLayout()
        self.pomodoros_box.setSpacing(5)

        self.main_box.addWidget(self.issue_label)
        self.main_box.addWidget(self.time_label)
        self.main_box.addWidget(self.pbar, Qt.AlignCenter)
        self.main_box.addLayout(self.btns_box)
        self.main_box.addLayout(self.pomodoros_box)

        self.main_box.addStretch()

    def handle_timer(self):
        value = self.pbar.value()
        if value < self.time_in_seconds:
            value += 1
            self.pbar.setValue(value)
            self.time = self.time.addSecs(-1)
            self.time_label.setText(self.time.toString())
        else:
            self.stop_timer()
            self.set_timer()

    def update_timer(self):
        self.time_in_seconds = self.get_time_in_seconds()
        self.pbar.setMaximum(self.time_in_seconds)
        self.pbar.setValue(0)
        self.time_label.setText(self.time.toString())

    def set_pomodoro_timer(self):
        self.stop_timer()
        self.cur_time = POMODORO
        self.time = TIME[POMODORO]
        self.update_timer()

    def stop_timer(self):
        self.timer.stop()
        self.timer_btn.setText('Start')
        self.reset_btn.setEnabled(True)
        self.logwork_btn.setEnabled(True)

    def set_pomodoro_mark(self):
        label = QLabel()
        pixmap = QPixmap('tomato2.png')
        label.setPixmap(pixmap)
        label.setObjectName('test')
        if self.pomodoros_count > 1:
            self.pomodoros_box.itemAt(
                self.pomodoros_count - 2
            ).widget().setSizePolicy(
                QSizePolicy.Fixed, QSizePolicy.Expanding
            )
        self.pomodoros_box.addWidget(label)

    def toggle_timer(self):
        if self.timer_btn.text() == 'Start':
            self.reset_btn.setEnabled(False)
            self.logwork_btn.setEnabled(False)
            self.timer.start(1000)
            self.timer_btn.setText('Stop')
        else:
            self.set_pomodoro_timer()

    def get_time_in_seconds(self):
        return QTime(0, 0, 0).secsTo(self.time)

    def reset_btn_click(self):
        pass

    def logwork_btn_click(self):
        pass

    def set_timer(self):
        if self.cur_time is POMODORO:
            self.pomodoros_count += 1
            self.set_pomodoro_mark()
            if not self.pomodoros_count % 4:
                self.cur_time = LONG_BREAK
            else:
                self.cur_time = SHORT_BREAK
            self.dialog = CustomDialog(self, self.cur_time)
            self.cur_time = self.dialog.exec()
        else:
            self.cur_time = POMODORO
        if self.cur_time is not SKIP_BREAK:
            self.time = TIME[self.cur_time]
        else:
            self.time = TIME[POMODORO]
        self.update_timer()
        if self.cur_time not in(POMODORO, SKIP_BREAK):
            self.toggle_timer()
        else:
            self.set_pomodoro_timer()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    e = PomodoroWindow('Some-key', 'Some title')
    e.show()
    sys.exit(app.exec_())
