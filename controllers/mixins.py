from PyQt5.QtWidgets import QMessageBox

from controllers.loading_indicator import LoadingIndicator, Thread


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


class SavingWithThreadsMixin():
    def save_click(self, issue_key):
        self.indicator = LoadingIndicator(self, self.view.vbox)
        self.indicator.show()
        self.new_thread = Thread(self.save_into_jira)
        self.new_thread.start()
        self.new_thread.finished.connect(self.stop_indicator)

    def stop_indicator(self, result, error):
        self.indicator.spinner.stop()
        if result:
            self.controller.refresh_issue_list()
            self.view.close()
        elif error:
            QMessageBox.about(self.view, 'Error', error)
