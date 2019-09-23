import sys
from PyQt5.QtWidgets import (
    QWidget,
    QDesktopWidget,
    QApplication,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QHBoxLayout,
    QLabel
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt


class QCustomWidget(QWidget):
    """
    Class for custom list item
    """
    def __init__(self):
        super().__init__()
        self.timetracking_box = QVBoxLayout()
        self.timetracking_box.setAlignment(Qt.AlignRight)
        self.estimated_label = QLabel()
        self.spent_label = QLabel()
        self.remaining_label = QLabel()
        self.estimated_label.setMinimumWidth(200)
        self.spent_label.setMinimumWidth(200)
        self.remaining_label.setMinimumWidth(200)

        self.timetracking_box.addWidget(self.estimated_label)
        self.timetracking_box.addWidget(self.spent_label)
        self.timetracking_box.addWidget(self.remaining_label)

        hbox = QHBoxLayout()
        self.issue_title_label = QLabel()
        self.issue_title_label.setMaximumWidth(800)
        hbox.addWidget(self.issue_title_label)
        hbox.addLayout(self.timetracking_box)

        vbox = QVBoxLayout()
        self.issue_key_label = QLabel()
        vbox.addWidget(self.issue_key_label)
        vbox.addLayout(hbox)
        self.setLayout(vbox)

    def set_issue_key(self, key):
        self.issue_key_label.setText(key)

    def set_issue_title(self, title):
        self.issue_title_label.setText(title)

    def set_time(self, estimated, spent, remaining):
        self.estimated_label.setText('Estimated: ' + estimated)
        self.spent_label.setText('Logged: ' + spent)
        self.remaining_label.setText('Remaining: ' + remaining)


class MainWindow(QWidget):
    jira_client = None

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.resize(650, 450)
        self.center()
        self.setWindowTitle('JIRA Quick Reporter')
        self.setWindowIcon(QIcon('logo.png'))
        self.show_issues_list()
        self.show()

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def show_issues_list(self):
        """
        Show list of issues
        """
        issue_list = self.jira_client.get_issues_list()
        vbox = QVBoxLayout()
        issue_list_widget = QListWidget(self)
        vbox.addWidget(issue_list_widget)
        for issue in issue_list:
            issue_widget = QCustomWidget()
            issue_widget.set_issue_key(issue['key'])
            issue_widget.set_issue_title(issue['title'])
            issue_widget.set_time(issue['time_estimated'],
                                  issue['time_spent'],
                                  issue['time_remaining'])
            issue_list_widget_item = QListWidgetItem(issue_list_widget)
            issue_list_widget_item.setSizeHint(issue_widget.sizeHint())
            issue_list_widget.addItem(issue_list_widget_item)
            issue_list_widget.setItemWidget(issue_list_widget_item,
                                            issue_widget)
        self.setLayout(vbox)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    ex = MainWindow()
    sys.exit(app.exec_())
