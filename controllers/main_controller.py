import os

from PyQt5.QtWidgets import (
    QMessageBox
)
from jira import JIRAError

from main_window import MainWindow
from time_log_window import TimeLogWindow
from pomodoro_window import PomodoroWindow

DEFAULT_ISSUES_COUNT = 50


class MainController:
    def __init__(self, jira_client):
        self.jira_client = jira_client
        self.issues_count = 0
        self.view = MainWindow(self)
        self.pomodoro_view = None
        self.time_log_view = None
        self.refresh_issue_list()
        self.view.show()

    def get_issue_list(self):
        issues_list = []
        issues = self.jira_client.get_issues(self.issues_count)
        current_issues_count = len(issues)
        self.issues_count += current_issues_count
        if current_issues_count < DEFAULT_ISSUES_COUNT:
            self.view.load_more_issues_btn.hide()
        else:
            self.view.load_more_issues_btn.show()

        # create list of issues
        for issue in issues:
            issues_dict = {
                'title': issue.fields.summary,
                'key': issue.key,
                'link': issue.permalink()
            }

            # if the task was logged
            if issue.fields.timetracking.raw:
                timetracking = issue.fields.timetracking
                issues_dict.update({
                    'estimated': getattr(timetracking, 'originalEstimate', '0m'),
                    'logged': getattr(timetracking, 'timeSpent', '0m'),
                    'remaining': getattr(timetracking, 'remainingEstimate', '0m'),
                })
            else:
                issues_dict.update({
                    'estimated': '0m',
                    'logged': '0m',
                    'remaining': '0m',
                })
            issues_list.append(issues_dict)
        return issues_list

    def refresh_issue_list(self, load_more=False):
        if not load_more:
            self.issues_count = 0
        issues_list = self.get_issue_list()
        self.view.show_issues_list(issues_list, load_more)

    def open_pomodoro_window(self, issue_key, issue_title):
        if self.pomodoro_view:
            if self.pomodoro_view.issue_key is issue_key \
                    or not self.pomodoro_view.quit():
                return
        self.pomodoro_view = PomodoroWindow(
            self, issue_key,
            issue_title,
            self.view.tray_menu
        )
        self.pomodoro_view.show()
        self.pomodoro_view.log_work_if_file_exists()

    def quit_app(self):
        if self.pomodoro_view:
            if not self.pomodoro_view.quit():
                return
        exit()

    def open_timelog_from_pomodoro(self, issue_key):
        params = [issue_key]
        if not os.path.exists(self.pomodoro_view.LOG_PATH):
            params.append('0m')
        else:
            with open(self.pomodoro_view.LOG_PATH, 'r') as log_file:
                try:
                    h, m = log_file.readline().split(':')
                except ValueError:
                    print('exc')
                    h = m = '0'
                if h == '0':
                    params.append('{}m'.format(m))
                elif m == '0':
                    params.append('{}h'.format(h))
                else:
                    params.append('{}h {}m'.format(h, m))
        self.open_timelog_window(*params)

    def open_timelog_window(self, issue_key, time_spent=None):
        issue = self.jira_client.issue(issue_key)
        self.time_log_view = TimeLogWindow(issue_key, time_spent)
        existing_estimate = self.jira_client.get_remaining_estimate(issue)
        self.time_log_view.set_existing_estimate(existing_estimate)
        self.time_log_view.show()
        self.time_log_view.save_button.clicked.connect(
            lambda: self.save_issue_worklog(issue_key)
        )

    def save_issue_worklog(self, issue_key):
        """Save button event handler
        take user input values, save JIRAalues into Jira time tracking,
        show popup for successfully save or exception
        """

        issue = self.jira_client.issue(issue_key)
        time_spent = self.time_log_view.time_spent_line.text()
        start_date = self.time_log_view.date_start
        if not start_date:
            return
        comment = self.time_log_view.work_description_line.toPlainText()
        remaining_estimate = self.time_log_view.new_remaining_estimate

        if not remaining_estimate:
            log_work_params = dict()
        elif remaining_estimate.get('name') == 'existing_estimate':
            log_work_params = dict(
                adjust_estimate='new',
                new_estimate=remaining_estimate.get('value')
            )
        elif remaining_estimate.get('name') == 'set_new_estimate':
            estimate = self.time_log_view.set_new_estimate_value.text()
            log_work_params = dict(
                adjust_estimate='new',
                new_estimate=estimate
            )
        elif remaining_estimate.get('name') == 'reduce_estimate':
            estimate = self.time_log_view.reduce_estimate_value.text()
            log_work_params = dict(
                adjust_estimate='manual',
                new_estimate=estimate
            )
        else:
            QMessageBox.about(
                self.time_log_view,
                'Error',
                'something went wrong'
            )
            return
        try:
            self.jira_client.log_work(
                issue,
                time_spent,
                start_date,
                comment,
                **log_work_params)
            self.time_log_view.close()
            self.refresh_issue_list()
            if self.pomodoro_view:
                self.pomodoro_view.reset()

        except JIRAError as e:
            QMessageBox.about(self.time_log_view, "Error", e.text)
