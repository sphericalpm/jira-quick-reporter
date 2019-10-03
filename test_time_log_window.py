from jiraclient import JiraClient
import sys
import unittest
from types import SimpleNamespace as sn


class Test(unittest.TestCase):
    def test_get_remaining_estimate_empty(self):
        issue = sn(
            fields=sn(
                timetracking=sn(
                    raw={}
                )
            )
        )
        self.assertEqual(JiraClient.get_remaining_estimate(issue), '0m')

    def test_get_remaining_estimate(self):
        issue = sn(
            fields=sn(
                timetracking=sn(
                    raw={'remainingEstimate': '1h'}
                )
            )
        )
        self.assertEqual(JiraClient.get_remaining_estimate(issue), '1h')


if __name__ == '__main__':
    unittest.main()
