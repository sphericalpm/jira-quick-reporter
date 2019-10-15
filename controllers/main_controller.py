import configparser
import os

from PyQt5.QtWidgets import QMessageBox, QInputDialog
from PyQt5.QtCore import Qt
from jira import JIRAError

from main_window import MainWindow
from controllers.timelog_controller import TimeLogController
from config import FILTERS_PATH

DEFAULT_ISSUES_COUNT = 50
SECTION = 'Filters'


class MainController:
    def __init__(self, jira_client):
        self.jira_client = jira_client
        self.issues_count = 0
        self.current_jql = ''
        self.view = MainWindow(self)

        self.config = configparser.ConfigParser()
        self.items = dict()
        self.view.show()
        self.create_filters()

    def get_issue_list(self, jql):
        issues_list = []
        issues = self.jira_client.get_issues(self.issues_count, jql)
        current_issues_count = len(issues)
        self.issues_count += current_issues_count
        if current_issues_count < DEFAULT_ISSUES_COUNT:
            self.view.load_more_issues_btn.hide()
        else:
            self.view.load_more_issues_btn.show()
        if not current_issues_count:
            return

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
        issues_list = self.get_issue_list(self.current_jql)
        if not issues_list and load_more:
            return
        self.view.show_issues_list(issues_list, load_more)

    def open_timelog_window(self, issue_key):
        TimeLogController(self.jira_client, issue_key, self)

    def write_ini_if_errors(self):
        self.config.clear()
        self.set_section()
        self.write_to_ini()

    def create_filters(self):
        # create if not exist
        if not os.path.exists(FILTERS_PATH):
            self.set_section()
            self.write_to_ini()
        try:
            self.config.read(FILTERS_PATH)
        except configparser.ParsingError:
            self.write_ini_if_errors()
        if not self.config.sections():
            self.write_ini_if_errors()

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
        self.config[SECTION] = {
            'my open issues': 'assignee = currentuser() '
            'and resolution = unresolved'
        }

    def write_to_ini(self):
        with open(FILTERS_PATH, 'w+') as ini_file:
            self.config.write(ini_file)

    def filter_selected(self):
        selected_key = self.view.my_filters_list.currentItem().text()
        self.current_jql = self.items[selected_key]
        self.refresh_issue_list()
        self.view.filter_field.setText(self.current_jql)

    def delete_filter(self, filter_name):
        self.config.remove_option(SECTION, filter_name)
        self.items.pop(filter_name)
        self.write_to_ini()

    def save_filter(self):
        jql = self.view.filter_field.text().lower()
        if jql:
            if jql not in self.items.values():
                try:
                    self.jira_client.get_issues(jql=jql)
                    dlg = QInputDialog(self.view)
                    dlg.setWindowIconText('Save filter')
                    dlg.setLabelText('Enter filter name')
                    dlg.setInputMode(QInputDialog.TextInput)

                    while dlg.exec_():
                        name = dlg.textValue()
                        if not name or set(':=#') & set(name):
                            continue
                        elif name in self.items:
                            reply = QMessageBox.question(
                                self.view,
                                'Warning',
                                'A filter with name \'{}\' '
                                'already exists. Overwrite?'.format(name),
                                QMessageBox.Yes | QMessageBox.Cancel
                            )
                            if reply == QMessageBox.Yes:
                                self.config[SECTION][name] = jql
                                self.write_to_ini()
                                self.set_items()
                                items = self.view.my_filters_list.findItems(
                                    name, Qt.MatchExactly
                                )
                                self.view.my_filters_list.setCurrentItem(
                                    items[0]
                                )
                                break
                        else:
                            self.config[SECTION][name] = jql
                            self.write_to_ini()
                            self.set_items()
                            self.view.my_filters_list.addItem(name)
                            self.view.my_filters_list.setCurrentItem(
                                self.view.my_filters_list.item(
                                    self.view.my_filters_list.count() - 1
                                )
                            )
                            break

                except JIRAError:
                    QMessageBox.about(
                        self.view, 'Error',
                        'The jql query is incorrect'
                    )

            else:
                QMessageBox.warning(
                    self.view,
                    'Warning',
                    'A filter with this jql already exists.'
                )
