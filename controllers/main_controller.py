import os

import requests
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMessageBox, QApplication
from jira import JIRAError

from config import LOG_TIME, ISSUES_COUNT, REFRESH_TIME
from main_window import MainWindow
from pomodoro_window import PomodoroWindow
from time_log_window import TimeLogWindow
from utils.decorators import catch_timeout_exception


class MainController:
    def __init__(self, jira_client):
        self.jira_client = jira_client
        self.issues_count = 0
        self.view = MainWindow(self)
        self.pomodoro_view = None
        self.time_log_view = None
        self.current_issues = {}

    def show(self):
        self.refresh_issue_list()
        self.view.show()

    def load_more_issues(self):
        new_issues_list = []
        issues = self.jira_client.get_issues(self.issues_count)
        new_issues_count = len(issues)

        for index, issue in enumerate(issues):
            self.current_issues[issue.key] = issue
            issue_dict = self.get_issue_parameters(issue)
            issue_dict['index'] = index + self.issues_count
            new_issues_list.append(issue_dict)

        self.issues_count += new_issues_count
        return new_issues_list

    def get_issues_list(self):
        # list of added issues for display on main window
        new_issues_list = []
        # list of updated issues for updated on main window
        update_issues_list = []

        # get firs ISSUES_COUNT issues
        issues = self.jira_client.get_issues(0)

        # if we have loaded issues before, then we need to get them
        if self.issues_count > ISSUES_COUNT:
            current_issues_count = len(issues)

            while current_issues_count < self.issues_count:
                loaded_issues = self.jira_client.get_issues(current_issues_count)
                loaded_issues_count = len(loaded_issues)
                if not loaded_issues_count:
                    break
                current_issues_count += loaded_issues_count
                issues += loaded_issues

        # create list of issues
        for index, issue in enumerate(issues):
            # if this is a new issue
            if issue.key not in self.current_issues:
                # add issue to the list of all available issues
                self.current_issues[issue.key] = issue
                issue_dict = self.get_issue_parameters(issue)
                issue_dict['index'] = index
                # add issue to the list for new issues
                new_issues_list.append(issue_dict)
            # if issue has been changed
            elif issue.raw['fields'] != self.current_issues[issue.key].raw['fields']:
                self.current_issues[issue.key] = issue
                issue_dict = self.get_issue_parameters(issue)
                # add issue to the list for updated issues
                update_issues_list.append(issue_dict)

        # update count of all available issues
        self.issues_count = len(self.current_issues)
        # get list of deleted issues
        delete_issues_list = [
            self.get_issue_parameters(issue) for issue in self.current_issues.values() if issue not in issues
        ]
        # remove deleted issues from the list of all available issues
        for issue in delete_issues_list:
            self.current_issues.pop(issue['key'])

        self.issues_count -= len(delete_issues_list)
        return new_issues_list, update_issues_list, delete_issues_list

    def get_issue_parameters(self, issue):
        issue_dict = dict(
            title=issue.fields.summary,
            key=issue.key,
            link=issue.permalink(),
            workflow=self.jira_client.get_possible_workflows(issue)
        )
        # if the task was logged
        if issue.fields.timetracking.raw:
            timetracking = issue.fields.timetracking.raw
            issue_dict.update({
                'estimated': timetracking.get('originalEstimate', '0m'),
                'logged': timetracking.get('timeSpent', '0m'),
                'remaining': timetracking.get('remainingEstimate', '0m'),
            })
        else:
            issue_dict.update({
                'estimated': '0m',
                'logged': '0m',
                'remaining': '0m',
            })
        return issue_dict

    def refresh_issue_list(self, load_more=False):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            if load_more:
                new_issues_list = self.load_more_issues()
            else:
                new_issues_list, update_issues_list, delete_issues_list = self.get_issues_list()

        except (requests.exceptions.ConnectionError,
                requests.exceptions.ReadTimeout):
            self.view.tray_icon.showMessage(
                'Connection error',
                'Please, check your internet connection'
            )
            self.current_issues.clear()
            self.view.show_no_issues()
            return
        finally:
            QApplication.restoreOverrideCursor()

        if not self.issues_count:
            self.view.show_no_issues()
            return
        # if we have issues, make the widget for issues enable
        self.view.issue_list_widget.show()
        self.view.label_info.hide()

        if new_issues_list:
            self.view.insert_issues(new_issues_list)
        if not load_more:
            if update_issues_list:
                self.view.update_issues(update_issues_list)
            if delete_issues_list:
                self.view.delete_issues(delete_issues_list)

        self.view.timer_refresh.start(REFRESH_TIME)
        QApplication.restoreOverrideCursor()

    def change_workflow(self, issue_key, workflow_items, status):
        current_status = workflow_items.itemText(0)
        if current_status == status:
            return
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            status_id = self.jira_client.client.find_transitionid_by_name(
                issue_key,
                status
            )

            try:
                if status_id:
                    self.jira_client.client.transition_issue(
                        issue_key,
                        transition=status_id
                    )
                self.refresh_issue_list()
            except JIRAError as e:
                QApplication.restoreOverrideCursor()
                QMessageBox.about(self.view, 'Error', e.text)
        except (requests.exceptions.ConnectionError,
                requests.exceptions.ReadTimeout):
            QMessageBox.warning(
                None,
                'Connection error',
                'Check your internet connection and try again'
            )
            self.view.set_workflow_current_state(issue_key)
        finally:
            QApplication.restoreOverrideCursor()

    def open_pomodoro_window(self, issue_key, issue_title):
        if self.pomodoro_view:
            if self.pomodoro_view.issue_key == issue_key:
                self.pomodoro_view.show()
            else:
                QMessageBox.warning(
                    None,
                    'Warning',
                    'Another task in progress now!'
                )
            return
        self.pomodoro_view = PomodoroWindow(
            self, issue_key,
            issue_title,
            self.view.tray_icon
        )
        self.pomodoro_view.show()
        self.pomodoro_view.log_work_if_file_exists()

    def open_timelog_from_pomodoro(self, issue_key):
        params = [issue_key]
        if not os.path.exists(self.pomodoro_view.LOG_PATH):
            params.append('0m')
        else:
            with open(self.pomodoro_view.LOG_PATH, 'r') as log_file:
                try:
                    hours, minutes = log_file.readline().split(':')
                except ValueError:
                    hours = minutes = '0'
                if hours == '0':
                    params.append('{}m'.format(minutes))
                elif minutes == '0':
                    params.append('{}h'.format(hours))
                else:
                    params.append('{}h {}m'.format(hours, minutes))
        self.open_timelog_window(*params)

    @catch_timeout_exception
    def open_timelog_window(self, issue_key, time_spent=None):
        issue = self.jira_client.issue(issue_key)
        self.time_log_view = TimeLogWindow(issue_key, time_spent)
        existing_estimate = self.jira_client.get_remaining_estimate(issue)
        self.time_log_view.set_existing_estimate(existing_estimate)
        self.time_log_view.show()
        self.time_log_view.save_button.clicked.connect(
            lambda: self.save_issue_worklog(issue_key)
        )

    @catch_timeout_exception
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
            self.view.timer_log_work.start(LOG_TIME)
            self.view.tray_icon.showMessage(
                'Saving work log',
                'Successfully saved',
                msecs=200
            )
            if self.pomodoro_view:
                self.pomodoro_view.reset_timer()

        except JIRAError as e:
            QMessageBox.about(self.time_log_view, "Error", e.text)

    def quit_app(self):
        if self.pomodoro_view:
            if not self.pomodoro_view.quit():
                return
        exit()
