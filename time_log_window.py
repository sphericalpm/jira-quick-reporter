import sys
from PyQt5.QtWidgets import (
    QWidget,
    QDesktopWidget,
    QApplication,
    QPushButton,
    QLineEdit,
    QGridLayout,
    QLabel,
    QTextEdit,
    QMessageBox,
    QRadioButton
)
from PyQt5.QtGui import QIcon
from jiraclient import JiraClient
from jira.exceptions import JIRAError
from datetime import datetime

from my_jira_token import my_token, email


class TimeLogWindow(QWidget):
    """Time Tracking window

    displays filds for time spent, date start and work description,
    button 'Save': save/update new values in Jira,
    button 'To my tasks': goes to window with list of tasks

    """

    def __init__(self, issue, jira):
        super().__init__()

        self.initUI(issue, jira)

    def initUI(self, issue, jira):
        """
        Show time log window
        """
        # main window characteristics
        self.jira = jira
        self.resize(650, 450)
        self.center()
        self.setWindowTitle('Log Work: %s' % issue)
        self.setWindowIcon(QIcon('logo.png'))

        # item description
        time_spent = QLabel('Time Spent (eg. 3w 4d 12h):')
        date_start = QLabel('Date Started (eg. 12-05-2019 13:15):')

        self.remaining_estimate = QLabel('Remaining estimate')

        self.automatically_estimate = QRadioButton('Adjust automatically')
        self.automatically_estimate.setChecked(True)
        self.automatically_estimate.value = "automatically_estimate"
        self.automatically_estimate.toggled.connect(self.radio_click)

        try:
            existing_estimate = issue.fields.timetracking.raw['remainingEstimate']
        except AttributeError:
            existing_estimate = "0m"

        self.existing_estimate = QRadioButton('Use existing estimate of %s' % existing_estimate)
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
        self.date_start_line = QLineEdit(datetime.strftime(datetime.now(), '%d-%m-%Y %H:%M'))
        self.work_description_line = QTextEdit()

        self.save_button = QPushButton('Save')
        self.save_button.setToolTip('save new time tracking values into Jira')

        self.to_my_tasks_button = QPushButton('To my tasks')
        self.to_my_tasks_button.setToolTip('go to personal Jira issue')

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
        vbox.addWidget(self.to_my_tasks_button)

        self.setLayout(vbox)

        # button settings, show command
        self.save_button.clicked.connect(self.save_click)
        self.to_my_tasks_button.clicked.connect(self.my_tasks_click)

        self.show()

    def center(self):
        """
        Move window to the screen center
        """
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def save_click(self):
        """Save button event handler

        take user input values, save JIRAalues into Jira time tracking,
        show popup for successfully save or exception

        """
        time_spent = self.time_spent_line.text()
        date_start = self.date_start_line.text()
        comment = self.work_description_line.toPlainText()

        new_estimate = self.new_remaining_estimate

        if not new_estimate:
            try:
                self.jira.client.add_worklog(
                    issue=issue,
                    timeSpent=time_spent,
                    started=datetime.strptime(date_start, '%d-%m-%Y %H:%M'),
                    comment=comment,
                )
                QMessageBox.about(self, 'Save', 'Successfully saved')

            except JIRAError as e:
                QMessageBox.about(self, "Error", e.text)

        elif new_estimate.get('name') == 'existing_estimate':
            try:
                self.jira.client.add_worklog(
                    issue=issue,
                    timeSpent=time_spent,
                    adjustEstimate='new',
                    newEstimate=new_estimate.get('value'),
                    started=datetime.strptime(date_start, '%d-%m-%Y %H:%M'),
                    comment=comment,
                )
                QMessageBox.about(self, 'Save', 'Successfully saved')
            except JIRAError as e:
                QMessageBox.about(self, "Error", e.text)

        elif new_estimate.get('name') == 'set_new_estimate':
            try:
                estimate = self.set_new_estimate_value.text()
                self.jira.client.add_worklog(
                    issue=issue,
                    timeSpent=time_spent,
                    adjustEstimate='new',
                    newEstimate=estimate,
                    started=datetime.strptime(date_start, '%d-%m-%Y %H:%M'),
                    comment=comment,
                )
                QMessageBox.about(self, 'Save', 'Successfully saved')
            except JIRAError as e:
                QMessageBox.about(self, "Error", e.text)

        elif new_estimate.get('name') == 'reduce_estimate':
            try:
                estimate = self.reduce_estimate_value.text()
                self.jira.client.add_worklog(
                    issue=issue,
                    timeSpent=time_spent,
                    adjustEstimate='manual',
                    reduceBy=estimate,
                    started=datetime.strptime(date_start, '%d-%m-%Y %H:%M'),
                    comment=comment,
                )
                QMessageBox.about(self, 'Save', 'Successfully saved')
            except JIRAError as e:
                QMessageBox.about(self, "Error", e.text)

        else:
            QMessageBox.about(self, "Error", "something went wrong")

    def radio_click(self):
        """Check which radio button was pressed
        """
        radioButton = self.sender()

        if radioButton.isChecked():
            self.new_remaining_estimate = radioButton.value

    def my_tasks_click(self):
        """To my tasks event handler

        goes to task list window
        TODO: make transit to the task list window

        """
        pass


if __name__ == '__main__':

    jira = JiraClient(email, my_token)
    issues = jira.get_issues_list()
    issue = issues['INF-52']

    app = QApplication(sys.argv)

    me = TimeLogWindow(issue, jira)

    sys.exit(app.exec_())
