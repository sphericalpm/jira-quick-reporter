from PyQt5.QtWidgets import QMessageBox

from controllers.loading_indicator import Thread


class TimeLogMixin:
    def take_timelog_values(self, remaining_estimate, target_window):
        if not remaining_estimate:
            log_work_params = dict()

        elif remaining_estimate.get('name') == 'existing_estimate':
            log_work_params = dict(
                adjust_estimate='new',
                new_estimate=remaining_estimate.get('value')
            )
        elif remaining_estimate.get('name') == 'set_new_estimate':
            estimate = target_window.set_new_estimate_value.text()
            log_work_params = dict(
                adjust_estimate='new',
                new_estimate=estimate
            )
        elif remaining_estimate.get('name') == 'reduce_estimate':
            estimate = target_window.reduce_estimate_value.text()
            log_work_params = dict(
                adjust_estimate='manual',
                reduce_by=estimate
            )
        else:
            QMessageBox.about(
                target_window,
                'Error',
                'something went wrong'
            )
            return

        return log_work_params


class ProcessWithThreadsMixin:
    def __init__(self):
        self.finish_thread_callback = None
        self.error_message = None
        self.indicator = None

    def start_loading(self, started_callback, finished_callback):
        self.finish_thread_callback = finished_callback
        self.indicator.spinner.start()
        self.new_thread = Thread(started_callback, self.error_message)
        self.new_thread.start()
        self.new_thread.finished.connect(self.stop_loading)

    def stop_loading(self, error_text):
        self.indicator.spinner.stop()
        self.finish_thread_callback(error_text)
        self.error_message = None
