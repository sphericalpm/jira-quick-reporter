import os
from functools import partial

from PyQt5.QtWidgets import QMessageBox, QInputDialog
from jira import JIRAError

from config import REFRESH_TIME, ISSUES_COUNT
from controllers.mixins import ProcessWithThreadsMixin
from controllers.filters import IssueFiltersHandler
from controllers.time_log_controller import TimeLogController, QuickTimeLog
from controllers.workflow_controller import (
    WorkflowController,
    CompleteWorkflowController
)
from main_window import MainWindow
from pomodoro_window import PomodoroWindow


class MainController(ProcessWithThreadsMixin):
    def __init__(self, jira_client):
        super().__init__()
        self.jira_client = jira_client
        self.issues_count = 0
        self.current_filter = ''
        self.view = MainWindow(self)
        self.pomodoro_view = None
        self.time_log_controller = None
        self.filters_handler = IssueFiltersHandler(self.jira_client)
        self.current_issues = {}
        self.insert_issue_list = []
        self.update_issue_list = []
        self.delete_issue_list = []
        self.set_loading_indicator()
        self.error_messages_count = 0

    def show(self):
        self.start_loading(self.filters_handler.create_filters, self.create_filters_handler)

    def load_more_issues(self, filter_query):
        issues = self.jira_client.get_issues(self.issues_count, filter_query)
        new_issues_count = len(issues)

        for index, issue in enumerate(issues):
            self.current_issues[issue.key] = issue
            issue_dict = self.get_issue_parameters(issue)
            issue_dict['index'] = index + self.issues_count
            self.insert_issue_list.append(issue_dict)

        self.issues_count += new_issues_count

    def get_issues_list(self, filter_query, change_filter=False):
        if change_filter or self.issues_count < ISSUES_COUNT:
            limit = ISSUES_COUNT
        else:
            limit = self.issues_count
        issues = self.jira_client.get_issues(0, filter_query, limit)

        # create list of issues
        for index, issue in enumerate(issues):
            # if this is a new issue
            if issue.key not in self.current_issues:
                # add issue to the list of all available issues
                self.current_issues[issue.key] = issue
                issue_dict = self.get_issue_parameters(issue)
                issue_dict['index'] = index
                # add issue to the list for new issues
                self.insert_issue_list.append(issue_dict)
            # if issue has been changed
            elif issue.raw['fields'] != self.current_issues[issue.key].raw['fields']:
                self.current_issues[issue.key] = issue
                issue_dict = self.get_issue_parameters(issue)
                # add issue to the list for updated issues
                self.update_issue_list.append(issue_dict)
        # update count of all available issues
        self.issues_count = len(self.current_issues)
        # get list of deleted issues
        self.delete_issue_list = [
            self.get_issue_parameters(issue) for issue in self.current_issues.values() if issue not in issues
        ]
        # remove deleted issues from the list of all available issues
        for issue in self.delete_issue_list:
            del self.current_issues[issue['key']]

        self.issues_count -= len(self.delete_issue_list)

    def get_issue_parameters(self, issue):
        workflow = self.jira_client.client.transitions(issue)
        possible_workflow = {status['name']: status['id'] for status in workflow}
        issue_dict = dict(
            title=issue.fields.summary,
            key=issue.key,
            link=issue.permalink(),
            issue_obj=issue,
            workflow=possible_workflow
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

    def refresh_issue_list_widget(self, error):
        if error:
            self.error_messages_count += 1
            if self.error_messages_count <= 1:
                QMessageBox.about(self.view, 'Error', error)
            self.current_issues.clear()
            self.view.show_no_issues(error)
            return
        self.error_messages_count = 0
        if not self.issues_count:
            self.view.show_no_issues()
            return
        # if we have issues, make the widget for issues enable
        self.view.issue_list_widget.show()
        self.view.label_info.hide()
        if self.delete_issue_list:
            self.view.delete_issues(self.delete_issue_list)
        if self.update_issue_list:
            self.view.update_issues(self.update_issue_list)
        if self.insert_issue_list:
            self.view.insert_issues(self.insert_issue_list)
        self.insert_issue_list.clear()
        self.update_issue_list.clear()
        self.delete_issue_list.clear()
        self.view.timer_refresh.start(REFRESH_TIME)

    def refresh_issue_list(self, load_more=False, change_filter=False):
        if load_more:
            callback = partial(self.load_more_issues, self.current_filter)
        else:
            callback = partial(self.get_issues_list, self.current_filter, change_filter)
        self.start_loading(callback, self.refresh_issue_list_widget)

    def auto_refresh_issue_list(self):
        callback = partial(self.get_issues_list, self.current_filter)
        self.start_loading(callback, self.refresh_issue_list_widget, with_indicator=False)

    def change_workflow(self, workflow, issue_obj, new_status):
        self.issue = issue_obj
        self.status_id = workflow.get(new_status)
        existing_estimate = self.jira_client.get_remaining_estimate(self.issue)
        original_estimate = self.jira_client.get_original_estimate(self.issue)
        assignee = self.issue.fields.assignee.emailAddress
        backlog_statuses = ['Backlog', 'Return to Backlog']
        current_status = str(issue_obj.fields.status)

        if not self.status_id:
            return

        elif new_status in backlog_statuses and current_status in backlog_statuses:
            # if it is backlog now and user press backlog one more
            # time we should not show worklog window
            return

        elif new_status in ['Put on hold', 'Select for development']:
            self.start_loading(
                self.simple_workflow_change,
                self.simple_workflow_change_handler
            )

        elif new_status in ['Complete', 'Declare done']:
            # open complete workflow window
            self.complete_workflow_controller = CompleteWorkflowController(
                self.jira_client,
                self.issue,
                new_status,
                assignee,
                self
            )
            self.complete_workflow_controller.show()
        else:
            self.workflow_controller = WorkflowController(
                self.jira_client,
                self.issue,
                self.status_id,
                existing_estimate,
                original_estimate,
                assignee,
                self
            )
            self.workflow_controller.show()

    def simple_workflow_change(self):
        try:
            self.jira_client.client.transition_issue(
                    self.issue,
                    transition=self.status_id
                )
        except JIRAError as e:
            raise ValueError(e.text)

    def simple_workflow_change_handler(self, error):
        if error:
            QMessageBox.about(self.view, 'Error', error)
            self.reset_workflow(self.issue)
        else:
            self.refresh_issue_list()

    def get_possible_workflows(self, issue):
        current_workflow = issue['issue_obj'].fields.status
        possible_workflows = list(issue['workflow'].keys())

        if current_workflow.name != 'Backlog':  # when it's 'Backlog' status,
            # JIRA API provides possibility to change it to 'Return to backlog'.
            # Cause it's the same that we already have we won't show it one more time
            possible_workflows.insert(0, current_workflow.name)  # insert because of
            # setCurrentIndex() can have only positive value

        return possible_workflows

    def reset_workflow(self, issue):
        self.view.set_workflow_current_state(issue.key)

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

    def open_time_log(self, issue_key):
        params = [self, self.jira_client, self.current_issues[issue_key]]
        if not self.pomodoro_view or not os.path.exists(self.pomodoro_view.LOG_PATH):
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
        self.time_log_controller = TimeLogController(*params)
        self.time_log_controller.view.show()

    def log_work_from_list(self, issue_key):
        quick_time_log = QuickTimeLog(
            self,
            self.jira_client,
            self.current_issues[issue_key]
        )
        quick_time_log.save()

    def create_filters_handler(self, error_text):
        if error_text:
            QMessageBox.warning(
                None,
                'Error',
                error_text
            )
            self.quit_app()
        else:
            self.view.show_filters(self.filters_handler.items)
            self.view.show()

    def search_issues_by_filter_name(self, filter_name):
        self.current_filter = self.filters_handler.get_filter_by_name(filter_name.lower())
        self.refresh_issue_list(change_filter=True)
        self.view.query_field.setText(self.current_filter)

    def search_issues_by_query(self):
        self.current_filter = self.view.query_field.text().lower()
        self.refresh_issue_list(change_filter=True)

    def existing_filter_saving_process(self, error_text):
        if error_text:
            QMessageBox.about(
                self.view, 'Error',
                error_text
            )
            return
        filter_name = self.view.filters_list.currentItem().text().lower()
        self.filters_handler.add_filter(filter_name, self.current_filter)
        self.view.set_current_filter(filter_name)
        self.view.filter_edited_label.hide()

    def filter_saving_process(self, error_text):
        if error_text:
            QMessageBox.about(
                self.view, 'Error',
                error_text
            )
            return
        input_name_dialog = QInputDialog(self.view)
        input_name_dialog.setWindowIconText('Save filter')
        input_name_dialog.setLabelText(
            'Enter filter name \n(you cannot use \' : = # ;\' symbols)'
        )
        input_name_dialog.setInputMode(QInputDialog.TextInput)

        while input_name_dialog.exec_():
            filter_name = input_name_dialog.textValue().lower()
            if not filter_name or set(':=#;') & set(filter_name):
                continue
            elif filter_name in self.filters_handler.items:
                reply = QMessageBox.question(
                    self.view,
                    'Warning',
                    'A filter with name \'{}\' '
                    'already exists. Overwrite?'.format(filter_name),
                    QMessageBox.Yes | QMessageBox.Cancel
                )
                if reply == QMessageBox.Yes:
                    self.filters_handler.add_filter(filter_name, self.current_filter)
                    self.view.set_current_filter(filter_name)
                    break
            else:
                self.filters_handler.add_filter(filter_name, self.current_filter)
                self.view.add_filter(filter_name)
                break

    def save_filter(self, is_existing=False):
        self.current_filter = self.view.query_field.text().lower()
        started_callback = partial(self.jira_client.get_issues, query=self.current_filter)
        if is_existing:
            finished_callback = self.existing_filter_saving_process
        else:
            finished_callback = self.filter_saving_process
        self.start_loading(started_callback, finished_callback)

    def quit_app(self):
        if self.pomodoro_view:
            if not self.pomodoro_view.quit():
                return
        exit()
