from PyQt5.QtWidgets import (
    QPushButton,
    QLineEdit,
    QGridLayout,
    QLabel,
    QTextEdit,
)

from center_window import CenterWindow


class WorkflowWindow(CenterWindow):
    def __init__(self, issue, status, controller):
        super().__init__()
        self.issue = issue
        self.choosen_status = status
        self.controller = controller
        self.set_style()
        self.center()
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

        comment = QLabel('Work Description:')

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
