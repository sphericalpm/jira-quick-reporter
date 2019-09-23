import sys
from PyQt5.QtWidgets import (
    QWidget,
    QDesktopWidget,
    QApplication,
    QPushButton,
    QLineEdit,
    QGridLayout,
    QLabel,
    QTextEdit
)
from PyQt5.QtGui import QIcon


class TimeLogWindow(QWidget):
    """Time Tracking window

    displays filds for time spent, date start and work description,
    button 'Save': save/update new values in Jira,
    button 'To my tasks': goes to window with list of tasks

    """

    def __init__(self, tasks):
        super().__init__()
        self.initUI(tasks)

    def initUI(self, ticket_number):
        """
        Show time log window
        """

        self.resize(650, 450)
        self.center()
        self.setWindowTitle('Log Work: %s' % ticket_number)
        self.setWindowIcon(QIcon('logo.png'))

        time_spent = QLabel('Time Spent (eg. 3w 4d 12h):')
        date_start = QLabel('Date Started (eg. 23/Sep/19 3:15 PM):')
        work_description = QLabel('Work Description:')

        self.time_spent_line = QLineEdit()
        self.date_start_line = QLineEdit()
        self.work_description_line = QTextEdit()
        self.save_button = QPushButton('Save')
        self.to_my_tasks_button = QPushButton('To my tasks')

        vertical_box = QGridLayout()

        vertical_box.addWidget(time_spent)
        vertical_box.addWidget(self.time_spent_line)

        vertical_box.addWidget(date_start)
        vertical_box.addWidget(self.date_start_line)

        vertical_box.addWidget(work_description)
        vertical_box.addWidget(self.work_description_line)
        vertical_box.addWidget(self.save_button)
        vertical_box.addWidget(self.to_my_tasks_button)

        self.setLayout(vertical_box)
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

        take user input values
        TODO: save values into Jira time tracking

        """
        time_spent = self.time_spent_line.text()
        date_start = self.date_start_line.text()
        work_description = self.work_description_line.toPlainText()

    def my_tasks_click(self):
        """To my tasks event handler

        goes to task list window
        TODO: make transit to the task list window
        """
        pass


if __name__ == '__main__':
    app = QApplication(sys.argv)

    tasks = 'INF-30'  # test value
    window = TimeLogWindow(tasks)
    sys.exit(app.exec_())
