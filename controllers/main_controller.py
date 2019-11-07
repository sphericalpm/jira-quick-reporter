import configparser
import os
from functools import partial

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMessageBox, QInputDialog
from jira import JIRAError

from config import (
    LOG_TIME,
    FILTERS_PATH,
    FILTERS_DEFAULT_SECTION_NAME,
    DEFAULT_FILTERS,
    REFRESH_TIME
)
from controllers.loading_indicator import LoadingIndicator
from controllers.mixins import TimeLogMixin, ProcessWithThreadsMixin
from controllers.workflow_controller import (
    WorkflowController,
    CompleteWorkflowController
)
from main_window import MainWindow
from pomodoro_window import PomodoroWindow
from time_log_window import TimeLogWindow


class MainController(TimeLogMixin, ProcessWithThreadsMixin):
    def __init__(self, jira_client):
        super().__init__()
        self.jira_client = jira_client
        self.issues_count = 0
        self.current_filter = ''
        self.view = MainWindow(self)
        self.pomodoro_view = None
        self.time_log_view = None
        self.config = configparser.ConfigParser()
        self.filters = dict()
        self.current_issues = {}
        self.insert_issue_list = []
        self.update_issue_list = []
        self.delete_issue_list = []
        self.main_indicator = LoadingIndicator(self.view, self.view.main_box)
        self.indicator = self.main_indicator

    def show(self):
        self.create_filters()
        self.view.show()

    def load_more_issues(self, filter_query):
        issues = self.jira_client.get_issues(self.issues_count, filter_query)
        new_issues_count = len(issues)

        for index, issue in enumerate(issues):
            self.current_issues[issue.key] = issue
            issue_dict = self.get_issue_parameters(issue)
            issue_dict['index'] = index + self.issues_count
            self.insert_issue_list.append(issue_dict)

        self.issues_count += new_issues_count

    def get_issues_list(self, filter_query):
        issues = self.jira_client.get_issues(0, filter_query, self.issues_count)

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
            self.current_issues.clear()
            self.view.show_no_issues()
            QMessageBox.about(self.view, 'Error', error)
            return

        if not self.issues_count:
            self.view.show_no_issues()
            return
        # if we have issues, make the widget for issues enable
        self.view.issue_list_widget.show()
        self.view.label_info.hide()
        if self.insert_issue_list:
            self.view.insert_issues(self.insert_issue_list)
        if self.update_issue_list:
            self.view.update_issues(self.update_issue_list)
        if self.delete_issue_list:
            self.view.delete_issues(self.delete_issue_list)
        self.insert_issue_list.clear()
        self.update_issue_list.clear()
        self.delete_issue_list.clear()
        self.view.timer_refresh.start(REFRESH_TIME)

    def refresh_issue_list(self, load_more=False):
        if load_more:
            callback = partial(self.load_more_issues, self.current_filter)
        else:
            callback = partial(self.get_issues_list, self.current_filter)
        self.indicator = self.main_indicator
        self.start_loading(callback, self.refresh_issue_list_widget)

    def change_workflow(self, workflow, issue_obj, status):
        self.issue = issue_obj
        self.status_id = workflow.get(status)
        existing_estimate = self.jira_client.get_remaining_estimate(self.issue)
        original_estimate = self.jira_client.get_original_estimate(self.issue)
        assignee = self.issue.fields.assignee.emailAddress

        if not self.status_id:
            return

        if status in ['Put on hold', 'Select for development']:
            self.indicator = self.main_indicator
            self.start_loading(
                self.simple_workflow_change,
                self.simple_workflow_change_handler
            )

        elif status in ['Complete', 'Declare done']:
            # open complete workflow window
            self.complete_workflow_controller = CompleteWorkflowController(
                self.jira_client,
                self.issue,
                status,
                assignee,
                self
            )
            self.complete_workflow_controller.show()
            self.complete_workflow_controller.view.set_existing_estimate(
                existing_estimate,
            )

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

    def open_timelog_window(self, issue_key, time_spent=None):
        self.indicator = self.main_indicator
        started_callback = partial(self.set_timelog_parameters, issue_key, time_spent)
        self.start_loading(started_callback, self.show_timelog_window)

    def set_timelog_parameters(self, issue_key, time_spent):
        self.issue = self.jira_client.issue(issue_key)
        self.time_spent = time_spent
        self.existing_estimate = self.jira_client.get_remaining_estimate(self.issue)

    def show_timelog_window(self, error_text):
        if error_text:
            QMessageBox.about(self.time_log_view, 'Error', error_text)
        else:
            self.time_log_view = TimeLogWindow(
                self.issue.key,
                self.time_spent,
                save_callback=self.save_issue_worklog
            )
            self.time_log_view.set_existing_estimate(self.existing_estimate)
            self.time_log_view.show()

    def save_issue_worklog(self, issue_key):
        """Save button event handler
        take user input values, save JIRAalues into Jira time tracking,
        show popup for successfully save or exception
        """

        self.current_issue = self.jira_client.issue(issue_key)
        self.time_spent = self.time_log_view.time_spent_line.text()
        self.start_date = self.time_log_view.date_start
        if not self.start_date:
            return
        self.comment = self.time_log_view.work_description_line.toPlainText()
        remaining_estimate = self.time_log_view.new_remaining_estimate
        self.log_work_params = self.take_timelog_values(
            remaining_estimate,
            self.time_log_view
        )

        self.indicator = LoadingIndicator(self.time_log_view, self.time_log_view.vbox)
        self.start_loading(self.save_worklog_into_jira, self.save_worklog_handler)

    def save_worklog_into_jira(self):
        try:
            self.jira_client.log_work(
                self.current_issue,
                self.time_spent,
                self.start_date,
                self.comment,
                **self.log_work_params)
        except JIRAError as e:
            raise ValueError(e.text)

    def save_worklog_handler(self, error):
        if error:
            QMessageBox.about(self.time_log_view, 'Error', error)
        else:
            self.time_log_view.close()
            self.refresh_issue_list()
            self.view.timer_log_work.start(LOG_TIME)
            if self.pomodoro_view:
                self.pomodoro_view.reset_timer()

    def create_filters(self):
        try:
            self.config.read(FILTERS_PATH)
        except configparser.Error:
            self.config.clear()

        self.set_default_section()
        self.write_to_ini()
        self.set_filters()

        for filter_query in self.filters.values():
            try:
                self.jira_client.get_issues(query=filter_query)
            except JIRAError:
                self.config.clear()
                self.set_default_section()
                self.write_to_ini()
                self.set_filters()
                break
            except (ConnectionError,
                    TimeoutError):
                QMessageBox.warning(
                    None,
                    'Connection error',
                    'Please, check your internet connection and try again'
                )
        self.view.show_filters(self.filters)

    def set_filters(self):
        self.filters.clear()
        self.filters.update(self.config.items(FILTERS_DEFAULT_SECTION_NAME))

    def set_default_section(self):
        if FILTERS_DEFAULT_SECTION_NAME not in self.config.sections():
            self.config[FILTERS_DEFAULT_SECTION_NAME] = {}
        for filter_name, filter_query in DEFAULT_FILTERS.items():
            self.config[FILTERS_DEFAULT_SECTION_NAME][filter_name] = filter_query

    def write_to_ini(self):
        with open(FILTERS_PATH, 'w') as ini_file:
            self.config.write(ini_file)

    def search_issues_by_filter_name(self, filter_name):
        self.current_filter = self.filters[filter_name.lower()]
        self.refresh_issue_list()
        self.view.filter_field.setText(self.current_filter)

    def search_issues_by_filter(self):
        self.current_filter = self.view.filter_field.text().lower()
        self.error_message = 'The query is incorrect'
        self.refresh_issue_list()

    def delete_filter(self, filter_name):
        self.config.remove_option(FILTERS_DEFAULT_SECTION_NAME, filter_name)
        self.filters.pop(filter_name)
        self.write_to_ini()

    def overwrite_filter(self, filter_name, filter_query):
        self.config[FILTERS_DEFAULT_SECTION_NAME][filter_name] = filter_query
        self.write_to_ini()
        self.set_filters()
        items = self.view.filters_list.findItems(
            filter_name, Qt.MatchExactly
        )
        self.view.filters_list.setCurrentItem(items[0])
        self.view.on_filter_selected(items[0])

    def add_filter(self, filter_name, filter_query):
        self.config[FILTERS_DEFAULT_SECTION_NAME][filter_name] = filter_query
        self.write_to_ini()
        self.set_filters()
        self.view.filters_list.addItem(filter_name)
        self.view.filters_list.setCurrentItem(
            self.view.filters_list.item(
                self.view.filters_list.count() - 1
            )
        )
        self.view.on_filter_selected(self.view.filters_list.currentItem())

    def get_filter_by_name(self, name):
        return self.filters[name.lower()]

    def existing_filter_saving_process(self, error_text):
        if error_text:
            QMessageBox.about(
                self.view, 'Error',
                error_text
            )
            return
        filter_name = self.view.filters_list.currentItem().text().lower()

        self.overwrite_filter(filter_name, self.current_filter)
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
            'Enter filter name \n(you cannot use \' :, =, #\' symbols)'
        )
        input_name_dialog.setInputMode(QInputDialog.TextInput)

        while input_name_dialog.exec_():
            filter_name = input_name_dialog.textValue().lower()
            if not filter_name or set(':=#') & set(filter_name):
                continue
            elif filter_name in self.filters:
                reply = QMessageBox.question(
                    self.view,
                    'Warning',
                    'A filter with name \'{}\' '
                    'already exists. Overwrite?'.format(filter_name),
                    QMessageBox.Yes | QMessageBox.Cancel
                )
                if reply == QMessageBox.Yes:
                    self.overwrite_filter(filter_name, self.current_filter)
                    break
            else:
                self.add_filter(filter_name, self.current_filter)
                break

    def save_filter(self, is_existing=False):
        self.current_filter = self.view.filter_field.text().lower()
        self.error_message = 'The query is incorrect'
        self.indicator = self.main_indicator
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
