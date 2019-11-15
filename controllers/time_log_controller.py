from functools import partial

from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import Qt

from config import LOG_TIME
from controllers.loading_indicator import LoadingIndicator
from controllers.mixins import ProcessWithThreadsMixin
from time_log_window import TimeLogWindow
from main_window import MainWindow


class TimeLogController(ProcessWithThreadsMixin):
    def __init__(self, main_controller, jira_client, issue, time_spent=None):
        super().__init__()
        self.main_controller = main_controller
        self.jira_client = jira_client
        self.time_spent = time_spent
        self.issue = issue
        self.existing_estimate = self.jira_client.get_remaining_estimate(self.issue)
        self.log_work_params = None
        self.start_date = None
        self.init_view()

    def init_view(self):
        self.view = TimeLogWindow(self, self.issue.key, self.time_spent)
        self.view.set_existing_estimate(self.existing_estimate)
        self.indicator = LoadingIndicator(self.view, self.view.main_box)

    def get_timelog_parameters(self):
        self.time_spent = self.view.time_spent_line.text()
        self.start_date = self.view.date_start
        if not self.start_date:
            return False
        self.comment = self.view.work_description_line.toPlainText()
        remaining_estimate = self.view.new_remaining_estimate

        if not remaining_estimate:
            self.log_work_params = dict()

        elif remaining_estimate.get('name') == 'existing_estimate':
            self.log_work_params = dict(
                adjust_estimate='new',
                new_estimate=remaining_estimate.get('value')
            )
        elif remaining_estimate.get('name') == 'set_new_estimate':
            estimate = self.view.set_new_estimate_value.text()
            self.log_work_params = dict(
                adjust_estimate='new',
                new_estimate=estimate
            )
        elif remaining_estimate.get('name') == 'reduce_estimate':
            estimate = self.view.reduce_estimate_value.text()
            self.log_work_params = dict(
                adjust_estimate='manual',
                reduce_by=estimate
            )
        else:
            QMessageBox.about(self.view, 'Error', 'Something went wrong')
            return False
        return True

    def save(self):
        if self.get_timelog_parameters():
            save_callback = partial(
                self.jira_client.log_work,
                self.issue,
                self.time_spent,
                self.start_date,
                self.comment,
                **self.log_work_params
            )
            self.start_loading(save_callback, self.save_handler)

    def save_handler(self, error):
        if error:
            QMessageBox.about(self.view, 'Error', error)
        else:
            if not isinstance(self.view, MainWindow):
                self.view.close()
            self.main_controller.refresh_issue_list()
            self.main_controller.view.timer_log_work.start(LOG_TIME)
            if self.main_controller.pomodoro_view and \
                    self.main_controller.pomodoro_view.issue_key == self.issue.key:
                self.main_controller.pomodoro_view.reset_timer()


class QuickTimeLog(TimeLogController):
    def init_view(self):
        self.view = self.main_controller.view
        self.indicator = self.main_controller.indicator

    def get_timelog_parameters(self):
        issue_item = self.view.issue_list_widget.findItems(
            self.issue.key, Qt.MatchExactly
        )[0]
        self.issue_widget = self.view.issue_list_widget.itemWidget(issue_item)
        self.time_spent = self.issue_widget.time_spent_line.text()
        self.comment = self.issue_widget.comment_line.text()
        self.log_work_params = dict()
        return True

    def save_handler(self, error):
        self.issue_widget.time_spent_line.clear()
        self.issue_widget.comment_line.clear()
