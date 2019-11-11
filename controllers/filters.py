import configparser

from jira import JIRAError

from config import (
    FILTERS_PATH,
    FILTERS_DEFAULT_SECTION_NAME,
    DEFAULT_FILTERS
)


class IssueFiltersHandler:
    def __init__(self, jira_client):
        self.config = configparser.ConfigParser()
        self.items = dict()
        self.jira_client = jira_client

    def create_filters(self):
        try:
            self.config.read(FILTERS_PATH)
        except configparser.Error:
            self.config.clear()

        self.set_default_section()
        self.write_to_ini()
        self.set_filters()

        for filter_query in self.items.values():
            try:
                self.jira_client.get_issues(query=filter_query)
            except JIRAError:
                self.config.clear()
                self.set_default_section()
                self.write_to_ini()
                self.set_filters()
                raise ValueError('The query is incorrect')

    def set_filters(self):
        self.items.clear()
        self.items.update(self.config.items(FILTERS_DEFAULT_SECTION_NAME))

    def set_default_section(self):
        if FILTERS_DEFAULT_SECTION_NAME not in self.config.sections():
            self.config[FILTERS_DEFAULT_SECTION_NAME] = {}
        for filter_name, filter_query in DEFAULT_FILTERS.items():
            self.config[FILTERS_DEFAULT_SECTION_NAME][filter_name] = filter_query

    def write_to_ini(self):
        with open(FILTERS_PATH, 'w') as ini_file:
            self.config.write(ini_file)

    def delete_filter(self, filter_name):
        self.config.remove_option(FILTERS_DEFAULT_SECTION_NAME, filter_name)
        self.items.pop(filter_name)
        self.write_to_ini()

    def add_filter(self, filter_name, filter_query):
        self.config[FILTERS_DEFAULT_SECTION_NAME][filter_name] = filter_query
        self.write_to_ini()
        self.set_filters()

    def get_filter_by_name(self, name):
        return self.items[name.lower()]
