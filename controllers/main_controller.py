import configparser
import os
from PyQt5.QtWidgets import QMessageBox, QInputDialog

from main_window import MainWindow
from controllers.timelog_controller import TimeLogController
from jira import JIRAError


class MainController:
    def __init__(self, jira_client):
        self.jira_client = jira_client
        self.view = MainWindow(self)
        self.refresh_issue_list()
        self.config = configparser.ConfigParser()
        self.section = 'Filters'
        self.items = dict()
        self.view.show()
        self.create_filters()

    def get_issue_list(self, jql):
        issues_list = []
        issues = self.jira_client.get_issues(jql)

        # create list of issues
        for issue in issues:
            issues_dict = dict(
                title=issue.fields.summary,
                key=issue.key,
                link=issue.permalink()
            )

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

    def refresh_issue_list(self, jql=''):
        issues_list = self.get_issue_list(jql)
        self.view.show_issues_list(issues_list)

    def open_timelog_window(self, issue_key):
        time_log_controller = TimeLogController(self.jira_client, issue_key)

    def create_filters(self):
        # create if not exist
        if not os.path.exists('filters.ini'):
            self.set_section()
            self.write_to_ini()
        try:
            self.config.read('filters.ini')
        except configparser.ParsingError:
            self.config.clear()
            self.set_section()
            self.write_to_ini()

        self.set_items()
        if not self.items:
            self.write_to_ini()
            self.set_items()
        self.view.show_filters(self.items)

    def set_items(self):
        sections = self.config.sections()
        for section in sections:
            self.items.update(self.config.items(section))

    def set_section(self):
        self.config[self.section] = {
            'my open issues': 'assignee = currentUser() AND resolution = Unresolved'
        }

    def write_to_ini(self):
        with open('filters.ini', 'w') as ini_file:
            self.config.write(ini_file)

    def filter_selected(self):
        selected_key = self.view.get_current_filter()
        jql = self.items[selected_key]
        self.refresh_issue_list(jql)
        self.view.set_filter_jql_to_field(jql)

    def save_filter(self):
        jql = self.view.get_new_filter()
        if jql:
            try:
                self.jira_client.get_issues(jql)
                if jql not in self.items.values():
                    name, ok = QInputDialog.getText(
                        self.view,
                        'Input Dialog',
                        'Enter filter name:'
                    )
                    #TODO: check if name valid
                    if ok and not name:
                        QMessageBox.about(self.view, 'Error', 'Please, enter a filter name')
                    elif ok and name not in self.items:
                        self.config[self.section][name] = jql
                        self.write_to_ini()
                        # TODO: update config and list with filters
                    elif ok:
                        QMessageBox.about(self.view, 'Error', 'A filter with this name already exists')
                else:
                    QMessageBox.about(self.view, 'Error', 'A filter with this jql already exists')
            except JIRAError:
                QMessageBox.about(self.view, 'Error', 'The jql line is incorrect')
