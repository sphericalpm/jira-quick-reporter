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
        self.center()
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
        self.main_box = QGridLayout()

        self.main_box.addWidget(assignee)
        self.main_box.addWidget(self.assignee_line)

        self.main_box.addWidget(original_estimate)
        self.main_box.addWidget(self.original_estimate_line)

        self.main_box.addWidget(remaining_estimate)
        self.main_box.addWidget(self.remaining_estimate_line)

        self.main_box.addWidget(comment)
        self.main_box.addWidget(self.comment_line)
        self.main_box.addWidget(self.save_button)

        self.setLayout(self.main_box)
        self.save_button.clicked.connect(self.controller.save)

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Return:
            self.controller.save()

    def closeEvent(self, event):
        self.controller.close()
        event.accept()


class CompleteWorflowWindow(TimeLogWindow):
    def __init__(
        self,
        controller,
        issue_key,
        assignee,
        possible_resolutions,
        possible_versions
    ):
        self.controller = controller
        self.issue_key = issue_key
        self.assignee = assignee
        self.possible_resolutions = possible_resolutions
        self.possible_versions = possible_versions
        super().__init__(self.controller, issue_key)

    def build_issue_form_vbox(self):
        super().build_issue_form_vbox()

        assignee = QLabel('Assignee (eg. vsmith):')
        self.assignee_line = QLineEdit('{}'.format(self.assignee))
        self.main_box.addWidget(assignee)
        self.main_box.addWidget(self.assignee_line)

        resolution = QLabel('Resolution:')
        self.main_box.addWidget(resolution)
        self.set_resolution = QComboBox(self)
        self.main_box.addWidget(self.set_resolution)

        self.set_resolution.addItems(self.possible_resolutions)
        self.set_resolution.setCurrentIndex(0)

        fix_versions = QLabel('Fix versions:')
        self.main_box.addWidget(fix_versions)
        self.set_version = QComboBox(self)
        self.main_box.addWidget(self.set_version)

        self.set_version.addItems(self.possible_versions)
        self.set_version.setCurrentIndex(0)

    def closeEvent(self, event):
        self.controller.close()
        event.accept()
