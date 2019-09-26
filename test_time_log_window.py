from PyQt5.QtWidgets import QApplication

from time_log_window import TimeLogWindow
from jiraclient import JiraClient
from my_jira_token import my_token, email
import sys

from types import SimpleNamespace as sn

app = QApplication(sys.argv)
jira = JiraClient(email, my_token)
issues = jira.get_issues()


def test_check_remaining_estimate():
    w = TimeLogWindow(issues[0], jira)

    w.issue = sn(
        fields=sn(
            timetracking=sn(
                raw={}
            )
        )
    )
    assert w.check_remaining_estimate() == '0m'

    w.issue = sn(
        fields=sn(
            timetracking=sn(
                raw={'remainingEstimate': '1h'}
            )
        )
    )
    assert w.check_remaining_estimate() == '1h'
