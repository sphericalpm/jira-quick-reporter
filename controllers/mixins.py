from PyQt5.QtCore import QMutex

from controllers.loading_indicator import Thread


class ProcessWithThreadsMixin:
    mutex = QMutex()

    def __init__(self):
        self.finish_thread_callback = None
        self.error_message = None
        self.indicator = None
        self.thread_list = []

    def start_loading(self, started_callback, finished_callback, with_indicator=True):
        self.finish_thread_callback = finished_callback
        if with_indicator:
            self.indicator.spinner.start()
        thread = Thread(started_callback, self.mutex, self.error_message)
        thread.finished.connect(self.stop_loading)
        thread.start()
        self.thread_list.append(thread)

    def stop_loading(self, error_text):
        self.indicator.spinner.stop()
        self.thread_list = [thread for thread in self.thread_list if not thread.isFinished()]
        self.finish_thread_callback(error_text)
        self.error_message = None
