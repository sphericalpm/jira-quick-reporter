from controllers.loading_indicator import Thread


class ProcessWithThreadsMixin:
    def __init__(self):
        self.finish_thread_callback = None
        self.error_message = None
        self.indicator = None

    def start_loading(self, started_callback, finished_callback, with_indicator=True):
        self.finish_thread_callback = finished_callback
        if with_indicator:
            self.indicator.spinner.start()
        self.new_thread = Thread(started_callback, self.error_message)
        self.new_thread.start()
        self.new_thread.finished.connect(self.stop_loading)

    def stop_loading(self, error_text):
        self.indicator.spinner.stop()
        self.finish_thread_callback(error_text)
        self.error_message = None
