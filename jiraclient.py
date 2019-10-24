from jira import JIRA
from config import MAX_RETRIES, ISSUES_COUNT


class JiraClient:
    def __init__(self, email, token, server='https://spherical.atlassian.net'):
        if not email or not token:
            raise ValueError('You need to specify email and token')
        self.client = JIRA(
            server=server,
            basic_auth=(email, token),
            max_retries=MAX_RETRIES,
            timeout=4
        )

    def get_issues(self, start_at):
        return self.client.search_issues(
                'assignee = currentUser()',
                fields='key, summary, timetracking, status',
                startAt=start_at,
                maxResults=ISSUES_COUNT
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
            existing_estimate = issue.fields.timetracking.raw[
                'remainingEstimate'
            ]
        except (AttributeError, TypeError, KeyError):
            existing_estimate = "0m"
        return existing_estimate

    def issue(self, key):
        return self.client.issue(key)

    def get_possible_workflows(self, issue):
        workflow = self.client.transitions(issue)
        current_workflow = issue.fields.status
        possible_workflows = [status['name'] for status in workflow]

        if current_workflow.name != 'Backlog':  # when it's 'Backlog' status,
            # JIRA API provides possibility to change it to 'Return to backlog'.
            # Cause it's the same that we already have we won't show it one more time
            possible_workflows.insert(0, current_workflow.name)  # insert because of
            # setCurrentIndex() can have only positive value

        return possible_workflows
