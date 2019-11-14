from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QMutex

from controllers.loading_indicator import Thread


class ProcessWithThreadsMixin:
    mutex = QMutex()

    def __init__(self):
        self.finish_thread_callback = None
        self.error_message = None
        self.indicator = None

    def start_loading(self, started_callback, finished_callback):
        self.finish_thread_callback = finished_callback
        self.indicator.spinner.start()
        self.new_thread = Thread(started_callback, self.mutex, self.error_message)
        self.new_thread.start()
        self.new_thread.finished.connect(self.stop_loading)

    def stop_loading(self, error_text):
        self.indicator.spinner.stop()
        self.finish_thread_callback(error_text)
        self.error_message = None
        self.mutex.unlock()
