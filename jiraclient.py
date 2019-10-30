from jira import JIRA
from jira import JIRAError

from config import MAX_RETRIES


class JiraClient:
    def __init__(self, email, token, server='https://spherical.atlassian.net'):
        self.client = JIRA(
            server=server,
            basic_auth=(email, token),
            max_retries=MAX_RETRIES,
            timeout=4,
        )

    def get_issues(self, start_at):
        return self.client.search_issues(
                'assignee = currentUser()',
                fields='key, summary, timetracking, status, assignee',
                startAt=start_at
        )

    def log_work(
            self,
            issue,
            time_spent,
            start_date,
            comment,
            adjust_estimate=None,
            new_estimate=None,
            reduce_by=None
    ):
        self.client.add_worklog(
            issue=issue,
            timeSpent=time_spent,
            adjustEstimate=adjust_estimate,
            newEstimate=new_estimate,
            reduceBy=reduce_by,
            started=start_date,
            comment=comment
        )

    def get_possible_resolutions(self):
        resolutions = self.client.resolutions()
        possible_resolutions = [resolution.name for resolution in resolutions]

        return possible_resolutions

    def get_possible_versions(self, issue):
        all_projects = self.client.projects()
        current_project_key = issue.key.split('-')[0]

        for id, project in enumerate(all_projects):
            if project.key == current_project_key:
                current_project_id = id

        versions = self.client.project_versions(
            all_projects[current_project_id]
        )
        possible_versions = [version.name for version in versions]

        return possible_versions

    @staticmethod
    def get_remaining_estimate(issue):
        try:
            existing_estimate = issue.fields.timetracking.raw['remainingEstimate']
        except (AttributeError, TypeError, KeyError):
            existing_estimate = "0m"
        return existing_estimate

    @staticmethod
    def get_original_estimate(issue):
        try:
            original_estimate = issue.fields.timetracking.originalEstimate
        except JIRAError as e:
            return "0m"
        return original_estimate

    def issue(self, key):
        return self.client.issue(key)
