from PyQt5.QtCore import Qt, QThread, pyqtSignal
from pyqtspinner.spinner import WaitingSpinner


class LoadingIndicator:
    def __init__(self, controller, widget):
        self.controller = controller
        self.widget = widget
        self.spinner = WaitingSpinner(
            self.controller.view,
            True,
            True,
            Qt.ApplicationModal)

    def show(self):
        self.widget.addWidget(self.spinner)
        self.spinner.start()


class Thread(QThread):
    finished = pyqtSignal(bool, str)

    def __init__(self, callback, parent=None):
        super().__init__()
        self.callback = callback

    def run(self):
        try:
            self.callback()
            self.finished.emit(True, None)
        except Exception as ex:
            self.finished.emit(False, str(ex))
