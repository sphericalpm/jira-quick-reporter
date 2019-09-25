from jira import JIRA

class JiraClient:
    """
    Class for work with Jira API
    [Link for token creation](https://confluence.atlassian.com/cloud/api-tokens-938839638.html?_ga=2.163432316.1388040092.1568897205-2047152859.1568897205)
    """
    options = {'server': 'https://spherical.atlassian.net'}
    client = None

    def __init__(self, email, token):
        """
        Initialization and user authentication
        :param str email: user email to authenticate
        :param str token: API token to authenticate
        """
        if not email and not token:
            raise ValueError('You need to specify email and token')
        self.client = JIRA(self.options, basic_auth=(email, token))

    def get_issues(self):
        """
        Get issues assigned to user in JIRA
        :return: list of issues
        """
        return self.client.search_issues(
                'assignee = currentUser()',
                fields='key, summary, timetracking')
