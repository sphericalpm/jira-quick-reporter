from PyQt5.QtWidgets import (
    QPushButton,
    QLineEdit,
    QGridLayout,
    QLabel,
    QTextEdit,
    QComboBox,
    QMainWindow
)
from PyQt5 import QtCore
from center_window import CenterWindow
from time_log_window import TimeLogWindow


class WorkflowWindow(CenterWindow, QMainWindow):
    def __init__(
        self,
        issue,
        existing_estimate,
        original_estimate,
        assignee,
        controller
    ):
        super().__init__()
        self.issue = issue
        self.existing_estimate = existing_estimate
        self.original_estimate = original_estimate
        self.controller = controller
        self.assignee = assignee

        self.set_style()
        self.resize(600, 450)
        self.setWindowTitle('Transit issue: {issue}'.format(
            issue=self.issue
            )
        )
        # vbox elements description
        assignee = QLabel('Assignee (eg. vsmith):')
        original_estimate = QLabel('Original Estimate (eg. 13w 4d 12h):')
        remaining_estimate = QLabel('Remaining estimate (eg. 13w 4d 12h):')

        comment = QLabel('Comment:')

        self.assignee_line = QLineEdit('{}'.format(self.assignee))
        self.original_estimate_line = QLineEdit(self.original_estimate)
        self.remaining_estimate_line = QLineEdit(self.existing_estimate)

        self.comment_line = QTextEdit()

        self.save_button = QPushButton('Save')
        self.save_button.setToolTip('Save changes')

        # add elements to box
        self.vbox = QGridLayout()

        self.vbox.addWidget(assignee)
        self.vbox.addWidget(self.assignee_line)

        self.vbox.addWidget(original_estimate)
        self.vbox.addWidget(self.original_estimate_line)

        self.vbox.addWidget(remaining_estimate)
        self.vbox.addWidget(self.remaining_estimate_line)

        self.vbox.addWidget(comment)
        self.vbox.addWidget(self.comment_line)
        self.vbox.addWidget(self.save_button)

        self.setLayout(self.vbox)
        self.save_button.clicked.connect(self.controller.save_click)

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Return:
            self.controller.save_click()


class CompleteWorflowWindow(TimeLogWindow):
    def __init__(
        self,
        controller,
        issue,
        assignee,
        possible_resolutions,
        save_callback=None
    ):
        self.controller = controller
        self.issue = issue
        self.assignee = assignee
        self.possible_resolutions = possible_resolutions
        super().__init__(issue, save_callback=save_callback)

    def build_issue_form_vbox(self):
        self.vbox = super().build_issue_form_vbox()

        assignee = QLabel('Assignee (eg. vsmith):')
        self.assignee_line = QLineEdit('{}'.format(self.assignee))
        self.vbox.addWidget(assignee)
        self.vbox.addWidget(self.assignee_line)

        resolution = QLabel('Resolution:')
        self.vbox.addWidget(resolution)
        self.set_resolution = QComboBox(self)
        self.vbox.addWidget(self.set_resolution)

        self.set_resolution.addItems(self.possible_resolutions)
        self.set_resolution.setCurrentIndex(0)

        fix_versions = QLabel('Fix versions:')
        self.vbox.addWidget(fix_versions)
        self.set_version = QComboBox(self)
        self.vbox.addWidget(self.set_version)

        possible_versions = self.controller.jira_client.get_possible_versions(self.issue)
        self.set_version.addItems(possible_versions)
        self.set_version.setCurrentIndex(0)
        return self.vbox
