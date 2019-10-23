from PyQt5.QtWidgets import (
    QPushButton,
    QLineEdit,
    QGridLayout,
    QLabel,
    QTextEdit,
    QComboBox
)

from center_window import CenterWindow
from time_log_window import TimeLogWindow


class WorkflowWindow(CenterWindow):
    def __init__(self, issue, status, controller):
        super().__init__()
        self.issue = issue
        self.choosen_status = status
        self.controller = controller
        self.set_style()
        self.resize(600, 450)
        self.setWindowTitle('{status}: {issue}'.format(
            status=self.choosen_status,
            issue=self.issue
            )
        )

        # vbox elements description
        assignee = QLabel('Assignee (eg. vsmith):')
        original_estimate = QLabel('Original Estimate (eg. 13w 4d 12h):')
        remaining_estimate = QLabel('Remaining estimate (eg. 13w 4d 12h):')

        comment = QLabel('Comment:')

        self.assignee_line = QLineEdit('Me')
        self.original_estimate_line = QLineEdit(
            self.issue.fields.timetracking.originalEstimate
        )
        self.remaining_estimate_line = QLineEdit(
            self.issue.fields.timetracking.remainingEstimate
        )
        self.comment_line = QTextEdit()

        self.save_button = QPushButton('Save')
        self.save_button.setToolTip('Save changes')

        # add elements to box
        vbox = QGridLayout()

        vbox.addWidget(assignee)
        vbox.addWidget(self.assignee_line)

        vbox.addWidget(original_estimate)
        vbox.addWidget(self.original_estimate_line)

        vbox.addWidget(remaining_estimate)
        vbox.addWidget(self.remaining_estimate_line)

        vbox.addWidget(comment)
        vbox.addWidget(self.comment_line)
        vbox.addWidget(self.save_button)

        self.setLayout(vbox)
        self.save_button.clicked.connect(self.controller.save_click)


class CompleteWorflowWindow(TimeLogWindow):
    def __init__(self, controller, issue, save_callback=None):
        self.controller = controller
        self.issue = issue
        super().__init__(issue, save_callback=save_callback)

    def build_issue_form_vbox(self):
        vbox = super().build_issue_form_vbox()

        assignee = QLabel('Assignee (eg. vsmith):')
        self.assignee_line = QLineEdit('Me')
        vbox.addWidget(assignee)
        vbox.addWidget(self.assignee_line)

        resolution = QLabel('Resolution:')
        vbox.addWidget(resolution)
        self.set_resolution = QComboBox(self)
        vbox.addWidget(self.set_resolution)

        possible_resolutions = self.controller.jira_client.get_possible_resolutions(self.issue)
        self.set_resolution.addItems(possible_resolutions)
        self.set_resolution.setCurrentIndex(0)

        fix_versions = QLabel('Fix versions:')
        vbox.addWidget(fix_versions)
        self.set_version = QComboBox(self)
        vbox.addWidget(self.set_version)

        possible_versions = self.controller.jira_client.get_possible_versions(self.issue)
        self.set_version.addItems(possible_versions)
        self.set_version.setCurrentIndex(0)
        return vbox
