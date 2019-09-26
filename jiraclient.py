from jira import JIRA


class JiraClient:
    def __init__(self, email, token, server='https://spherical.atlassian.net'):
        if not email and not token:
            raise ValueError('You need to specify email and token')
        self.client = JIRA(
            server=server,
            basic_auth=(email, token),
            max_retries=1
        )

    def get_issues(self):
        return self.client.search_issues(
                'assignee = currentUser()',
                fields='key, summary, timetracking')
