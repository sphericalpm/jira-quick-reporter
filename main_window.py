import sys
from PyQt5.QtWidgets import (
    QWidget,
    QDesktopWidget,
    QApplication,
)
from PyQt5.QtGui import QIcon


class MainWindow(QWidget):

    def __init__(self, tasks):
        super().__init__()

        self.initUI(tasks)

    def initUI(self, tasks):

        self.resize(650, 450)
        self.center()
        self.setWindowTitle('JIRA Quick Reporter')
        self.setWindowIcon(QIcon('logo.png'))

        self.show()

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())


if __name__ == '__main__':

    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    tasks = ['first', 'second', 'third']
    ex = MainWindow(tasks)

    sys.exit(app.exec_())
