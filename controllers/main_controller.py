from main_window import MainWindow
from controllers.timelog_controller import TimeLogController


class MainController:
    def __init__(self, jira_client):
        self.jira_client = jira_client
        self.view = MainWindow(self)
        self.refresh_issue_list()
        self.view.show()

    def get_issue_list(self):
        issues_list = []
        issues = self.jira_client.get_issues()

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

    def refresh_issue_list(self):
        issues_list = self.get_issue_list()
        self.view.show_issues_list(issues_list)

    def open_timelog_window(self, issue_key):
        time_log_controller = TimeLogController(self.jira_client, issue_key, self)
