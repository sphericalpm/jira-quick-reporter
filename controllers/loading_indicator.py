from PyQt5.QtCore import Qt, QThread, pyqtSignal
from jira import JIRAError
from pyqtspinner.spinner import WaitingSpinner
from requests.exceptions import ConnectionError, ReadTimeout


class LoadingIndicator:
    def __init__(self, view, widget):
        self.widget = widget
        self.spinner = WaitingSpinner(
            view,
            True,
            True,
            Qt.ApplicationModal)
        self.widget.addWidget(self.spinner)


class Thread(QThread):
    finished = pyqtSignal(str)

    def __init__(self, callback, error_text=None):
        super().__init__()
        self.error_text = error_text
        self.callback = callback

    def run(self):
        try:
            self.callback()
            self.error_text = None
        except (ConnectionError,
                ReadTimeout):
            self.error_text = 'Connection error!\nPlease, check your internet connection'
        except JIRAError as ex:
            if self.error_text is None:
                self.error_text = ex.text
        except Exception as ex:
            if self.error_text is None:
                self.error_text = str(ex)
        self.finished.emit(self.error_text)
