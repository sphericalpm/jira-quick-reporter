from jira import JIRA
from config import MAX_RETRIES


class JiraClient:
    def __init__(self, email, token, server='https://spherical.atlassian.net'):
        if not email or not token:
            raise ValueError('You need to specify email and token')
        self.client = JIRA(
            server=server,
            basic_auth=(email, token),
            max_retries=MAX_RETRIES,
            timeout=4,
        )

    def get_issues(self, start_at=0, query=''):
        return self.client.search_issues(
                query,
                fields='key, summary, timetracking, status',
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

    @staticmethod
    def get_remaining_estimate(issue):
        try:
            existing_estimate = issue.fields.timetracking.raw['remainingEstimate']
        except (AttributeError, TypeError, KeyError):
            existing_estimate = "0m"
        return existing_estimate

    def issue(self, key):
        return self.client.issue(key)
