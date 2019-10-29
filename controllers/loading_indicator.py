from PyQt5.QtCore import Qt, QThread, pyqtSignal
from pyqtspinner.spinner import WaitingSpinner


class LoadingIndicator:
    def __init__(self, controller, widget):
        self.controller = controller
        self.widget = widget

    def show(self):
        self.spinner = WaitingSpinner(
            self.controller.view,
            True,
            True,
            Qt.ApplicationModal)
        self.widget.addWidget(self.spinner)
        self.spinner.start()


class Thread(QThread):
    finished = pyqtSignal()

    def __init__(self, callback, parent=None):
        super().__init__()
        self.callback = callback

    def run(self):
        self.callback()
        self.finished.emit()
