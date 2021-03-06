from datetime import datetime
from time import gmtime, strftime, strptime, mktime

from PyQt5 import QtCore
from PyQt5.QtCore import QEvent
from PyQt5.QtWidgets import (
    QPushButton,
    QLineEdit,
    QGridLayout,
    QLabel,
    QTextEdit,
    QRadioButton
)

from center_window import CenterWindow
from config import QSS


class TimeLogWindow(CenterWindow):
    def __init__(self, controller, issue_key, time_spent=None):
        super().__init__()
        self.center()
        self.issue_key = issue_key
        self.time_spent = time_spent
        self.controller = controller
        self.setStyleSheet(QSS)
        self.resize(600, 450)
        self.setWindowTitle('Log Work: {issue}'.format(issue=issue_key))

        self.main_box = QGridLayout()
        self.build_issue_form_vbox()
        self.add_save_button()
        self.setLayout(self.main_box)

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Return:
            self.controller.save()

    def add_save_button(self):
        self.save_button = QPushButton('Save')
        self.save_button.setToolTip('save new time tracking values into Jira')
        self.save_button.clicked.connect(self.controller.save)
        self.main_box.addWidget(self.save_button)

    def build_issue_form_vbox(self):
        # main_box elements description
        time_spent_label = QLabel('Time Spent (eg. 3w 4d 12h):')
        date_start = QLabel('Date Started (eg. 12-05-2019 13:15):')

        self.remaining_estimate = QLabel('Remaining estimate')

        self.automatically_estimate = QRadioButton('Adjust automatically')
        self.automatically_estimate.setChecked(True)
        self.automatically_estimate.value = {'name': 'automatically_estimate'}
        self.automatically_estimate.toggled.connect(self.radio_click)

        self.existing_estimate = QRadioButton()
        self.existing_estimate.toggled.connect(self.radio_click)

        self.set_new_estimate = QRadioButton('Set to new')
        self.set_new_estimate_value = QLineEdit()
        self.set_new_estimate.value = {
            'name': 'set_new_estimate',
        }
        self.set_new_estimate.toggled.connect(self.radio_click)

        self.reduce_estimate = QRadioButton('Reduced by')
        self.reduce_estimate_value = QLineEdit()
        self.reduce_estimate.value = {
            'name': 'reduce_estimate',
        }
        self.reduce_estimate.toggled.connect(self.radio_click)

        self.new_remaining_estimate = None

        work_description = QLabel('Description:')

        self.time_spent_line = QLineEdit()
        if self.time_spent:
            self.time_spent_line.setText(self.time_spent)
        self.date_start_line = QLineEdit(
            datetime.now().strftime('%d-%m-%Y %H:%M')
        )
        self.date_start_line.installEventFilter(self)
        self.date_start = self.get_date_from_line()
        self.work_description_line = QTextEdit()

        # add elements to box
        self.main_box = QGridLayout()

        self.main_box.addWidget(time_spent_label)
        self.main_box.addWidget(self.time_spent_line)

        self.main_box.addWidget(date_start)
        self.main_box.addWidget(self.date_start_line)

        self.main_box.addWidget(self.remaining_estimate)
        self.main_box.addWidget(self.automatically_estimate)
        self.main_box.addWidget(self.existing_estimate)
        self.main_box.addWidget(self.set_new_estimate)
        self.main_box.addWidget(self.set_new_estimate_value)
        self.main_box.addWidget(self.reduce_estimate)
        self.main_box.addWidget(self.reduce_estimate_value)

        self.main_box.addWidget(work_description)
        self.main_box.addWidget(self.work_description_line)

    def set_existing_estimate(self, existing_estimate):
        self.existing_estimate.setText(
            'Use existing estimate of {}'.format(existing_estimate)
        )
        self.existing_estimate.value = {
            'name': 'existing_estimate',
            'value': existing_estimate
        }

    def get_date_from_line(self):
        # create time object from date_start_line
        date_line = strptime(
            self.date_start_line.text(),
            '%d-%m-%Y %H:%M'
        )
        # convert local time to utc
        date = strftime(
            '%d-%m-%Y %H:%M',
            gmtime(mktime(date_line))
        )
        return datetime.strptime(date, '%d-%m-%Y %H:%M')

    def eventFilter(self, obj, event):
        if event.type() == QEvent.FocusOut:
            if obj is self.date_start_line:
                try:
                    self.date_start = self.get_date_from_line()
                    self.date_start_line.setObjectName('')
                    self.date_start_line.setStyleSheet('')
                except ValueError:
                    self.date_start = None
                    self.date_start_line.setObjectName('error_field')
                    self.date_start_line.setStyleSheet('error_field')
        return False

    def radio_click(self):
        """ Check which radio button was pressed """

        radio_button = self.sender()
        if radio_button.isChecked():
            self.new_remaining_estimate = radio_button.value
