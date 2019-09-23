from jira import JIRA


class JiraClient:
    """
    Class for work with Jira API
    """
    options = {'server': 'https://spherical.atlassian.net'}
    client = None

    def __init__(self, email, token):
        """
        Initialization and user authentication
        :param email: user email to authenticate
        :param token: API token to authenticate
        """
        if not email and not token:
            raise ValueError('You need to specify email and token')
        self.client = JIRA(self.options, basic_auth=(email, token))

    def get_issues_list(self):
        """
        Get issues assigned to user in JIRA
        :return: list of issues
        """
        issues = []
        issues_search = self.client.search_issues(
                'assignee = currentUser() and '
                'status in ("in progress", "open")',
                fields='key, summary, timetracking')

        for issue in issues_search:
            issues_dict = dict(
                key=issue.key,
                title=getattr(issue.fields, 'summary', None),
                time_estimated=getattr(issue.fields.timetracking,
                                       'originalEstimate', None),
                time_remaining=getattr(issue.fields.timetracking,
                                       'remainingEstimate', None),
                time_spent=getattr(issue.fields.timetracking,
                                   'timeSpent', None),
                link=issue.permalink())
            issues.append(issues_dict)
        return issues
