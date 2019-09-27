from datetime import datetime

from PyQt5.QtWidgets import (
    QPushButton,
    QLineEdit,
    QGridLayout,
    QLabel,
    QTextEdit,
    QMessageBox,
    QRadioButton
)

from jira.exceptions import JIRAError
from center_window import CenterWindow


class TimeLogWindow(CenterWindow):

    def __init__(self, issue, jira):
        super().__init__()

        self.show_time_log_window(issue, jira)

    def show_time_log_window(self, issue, jira):
        self.issue = issue
        self.jira = jira

        # main window characteristics
        self.resize(600, 450)
        self.center()
        self.setWindowTitle('Log Work: %s' % issue)

        # vbox elements description
        time_spent = QLabel('Time Spent (eg. 3w 4d 12h):')
        date_start = QLabel('Date Started (eg. 12-05-2019 13:15):')

        self.remaining_estimate = QLabel('Remaining estimate')

        self.automatically_estimate = QRadioButton('Adjust automatically')
        self.automatically_estimate.setChecked(True)
        self.automatically_estimate.value = "automatically_estimate"
        self.automatically_estimate.toggled.connect(self.radio_click)

        existing_estimate = self.check_remaining_estimate()

        self.existing_estimate = QRadioButton(
            'Use existing estimate of %s' % existing_estimate
        )
        self.existing_estimate.value = {
            "name": "existing_estimate",
            "value": existing_estimate
        }
        self.existing_estimate.toggled.connect(self.radio_click)

        self.set_new_estimate = QRadioButton('Set to new')
        self.set_new_estimate_value = QLineEdit()
        self.set_new_estimate.value = {
            "name": "set_new_estimate",
        }
        self.set_new_estimate.toggled.connect(self.radio_click)

        self.reduce_estimate = QRadioButton('Reduced by')
        self.reduce_estimate_value = QLineEdit()
        self.reduce_estimate.value = {
            "name": "reduce_estimate",
        }
        self.reduce_estimate.toggled.connect(self.radio_click)

        self.new_remaining_estimate = None

        work_description = QLabel('Work Description:')

        self.time_spent_line = QLineEdit()
        self.date_start_line = QLineEdit(
            datetime.strftime(datetime.now(), '%d-%m-%Y %H:%M')
        )
        self.work_description_line = QTextEdit()

        self.save_button = QPushButton('Save')
        self.save_button.setToolTip('save new time tracking values into Jira')

        # add elements to box
        vbox = QGridLayout()

        vbox.addWidget(time_spent)
        vbox.addWidget(self.time_spent_line)

        vbox.addWidget(date_start)
        vbox.addWidget(self.date_start_line)

        vbox.addWidget(self.remaining_estimate)
        vbox.addWidget(self.automatically_estimate)
        vbox.addWidget(self.existing_estimate)
        vbox.addWidget(self.set_new_estimate)
        vbox.addWidget(self.set_new_estimate_value)
        vbox.addWidget(self.reduce_estimate)
        vbox.addWidget(self.reduce_estimate_value)

        vbox.addWidget(work_description)
        vbox.addWidget(self.work_description_line)
        vbox.addWidget(self.save_button)

        self.setLayout(vbox)

        # button settings, show window command
        self.save_button.clicked.connect(self.save_click)

        self.show()

    def save_click(self):
        '''Save button event handler
        take user input values, save JIRAalues into Jira time tracking,
        show popup for successfully save or exception
        '''

        time_spent = self.time_spent_line.text()
        date = self.date_start_line.text()
        start_date = datetime.strptime(date, '%d-%m-%Y %H:%M')
        comment = self.work_description_line.toPlainText()

        new_estimate = self.new_remaining_estimate

        if not new_estimate:
            log_work_params = dict()
        elif new_estimate.get('name') == 'existing_estimate':
            log_work_params = dict(
                adjust_estimate='new',
                new_estimate=new_estimate.get('value')
            )
        elif new_estimate.get('name') == 'set_new_estimate':
            estimate = self.set_new_estimate_value.text()
            log_work_params = dict(
                adjust_estimate='new',
                new_estimate=estimate
            )
        elif new_estimate.get('name') == 'reduce_estimate':
            estimate = self.reduce_estimate_value.text()
            log_work_params = dict(
                adjust_estimate='manual',
                new_estimate=estimate
            )
        else:
            QMessageBox.about(self, "Error", "something went wrong")
            return
        try:
            self.jira.log_work(
                self.issue,
                time_spent,
                start_date,
                comment,
                **log_work_params)
            QMessageBox.about(self, 'Save', 'Successfully saved')
        except JIRAError as e:
            QMessageBox.about(self, "Error", e.text)

    def radio_click(self):
        '''Check which radio button was pressed'''

        radioButton = self.sender()
        if radioButton.isChecked():
            self.new_remaining_estimate = radioButton.value

    def check_remaining_estimate(self):
        try:
            existing_estimate = self.issue.fields.timetracking.raw['remainingEstimate']
        except (AttributeError, TypeError, KeyError):
            existing_estimate = "0m"
        return existing_estimate
