from PyQt5.QtCore import Qt, QMutex, QThread, pyqtSignal
from jira import JIRAError
from pyqtspinner.spinner import WaitingSpinner
from requests.exceptions import ConnectionError, ReadTimeout


class Thread(QThread):
    finished = pyqtSignal(str)

    def __init__(self, callback, mutex):
        super().__init__()
        self.error_text = None
        self.callback = callback
        self.mutex = mutex

    def run(self):
        self.mutex.lock()
        try:
            self.callback()
            self.error_text = None
        except (ConnectionError, ReadTimeout):
            self.error_text = 'Connection error!\nPlease, check your internet connection'
        except JIRAError as ex:
            self.error_text = ex.text
        except Exception as ex:
            self.error_text = str(ex)
        finally:
            self.mutex.unlock()
            self.finished.emit(self.error_text)


class ProcessWithThreadsMixin:
    mutex = QMutex()

    def __init__(self):
        self.finish_thread_callback = None
        self.thread_list = []

    def set_loading_indicator(self):
        self.indicator = WaitingSpinner(
            self.view,
            True,
            True,
            Qt.ApplicationModal
        )

    def start_loading(self, started_callback, finished_callback, with_indicator=True):
        self.finish_thread_callback = finished_callback
        if with_indicator:
            self.indicator.start()
        thread = Thread(started_callback, self.mutex)
        thread.finished.connect(self.stop_loading)
        thread.start()
        self.thread_list.append(thread)

    def stop_loading(self, error_text):
        self.indicator.stop()
        self.thread_list = [thread for thread in self.thread_list if not thread.isFinished()]
        self.finish_thread_callback(error_text)
