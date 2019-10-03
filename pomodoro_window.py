import sys

from PyQt5.QtWidgets import (
    QApplication,
    QProgressBar,
    QPushButton,
    QLabel,
    QVBoxLayout,
    QGridLayout,
    QHBoxLayout
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QTimer, QTime, Qt

from center_window import CenterWindow
from config import QSS_PATH


class PomodoroWindow(CenterWindow):
    def __init__(self, issue_key, issue_title):
        super().__init__()
        self.setStyleSheet(open(QSS_PATH, 'r').read())
        self.resize(500, 200)
        self.setWindowTitle('Pomodoro Timer')
        self.issue_key = issue_key
        self.issue_title = issue_title
        self.pomodoros_count = 0
        self.time_minutes = 1

        self.main_box = QVBoxLayout()
        self.setLayout(self.main_box)

        self.issue_label = QLabel(
            '{}: {}'.format(self.issue_key, self.issue_title)
        )
        self.issue_label.setAlignment(Qt.AlignCenter)
        self.issue_label.setObjectName('issue_label')

        self.pbar = QProgressBar()
        self.pbar.setMaximum(self.time_minutes * 60)
        self.pbar.setValue(0)
        self.pbar.setTextVisible(True)
        self.time = QTime(0, self.time_minutes, 0)
        self.timer = QTimer()

        self.timer.timeout.connect(self.handle_timer)
        self.time_label = QLabel()
        self.time_label.setObjectName('time_label')
        self.time_label.setText(self.time.toString())
        self.time_label.setAlignment(Qt.AlignCenter)

        self.btns_box = QHBoxLayout()
        self.btn_timer = QPushButton('Start')
        self.btn_timer.clicked.connect(self.btn_timer_click)
        self.btns_box.addWidget(self.btn_timer)

        self.pomodoros_grid = QGridLayout()
        self.pomodoros_grid.addWidget(QLabel(''), 0, 0)

        self.main_box.addWidget(self.issue_label)
        self.main_box.addWidget(self.time_label)
        self.main_box.addWidget(self.pbar, Qt.AlignCenter)
        self.main_box.addLayout(self.btns_box)
        self.main_box.addLayout(self.pomodoros_grid, Qt.AlignLeft)
        self.main_box.addStretch()

    def handle_timer(self):
        value = self.pbar.value()
        if value < self.time_minutes * 60:
            value += 1
            self.pbar.setValue(value)
            self.time = self.time.addSecs(-1)
            self.time_label.setText(self.time.toString())
        else:
            self.timer.stop()
            self.set_pomodoro()

    def set_pomodoro(self):
        label = QLabel()
        pixmap = QPixmap('tomato2.png')
        label.setPixmap(pixmap)
        self.pomodoros_grid.addWidget(label, 0, self.pomodoros_count)
        self.pomodoros_count += 1

    def btn_timer_click(self):
        if self.btn_timer.text() == 'Start':
            self.timer.start(1000)
            self.btn_timer.setText('Stop')
        else:
            self.timer.killTimer(1)
            self.pbar.setValue(0)
            self.time.setHMS(0, self.time_minutes, 0)
            self.time_label.setText(self.time.toString())
            self.btn_timer.setText('Start')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    e = PomodoroWindow('Some-key', 'Some title')
    e.show()
    sys.exit(app.exec_())
