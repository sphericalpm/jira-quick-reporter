from controllers.main_controller import MainController
from types import SimpleNamespace as sn


def test_posiible_workflows():
    issue = sn(
        fields=sn(
            status=sn(
                name='Selected for development'
            )
        )
    )
    issues = {}
    issues['issue_obj'] = issue
    issues['workflow'] = {
        'Return to Backlog': '131',
        'Selected for development': '51',
        'Declare done': '171',
        'Flag': '181'
    }

    assert MainController(None).get_possible_workflows(issues) == [
        'Selected for development',
        'Return to Backlog',
        'Selected for development',
        'Declare done',
        'Flag'
    ]


def test_posiible_workflows_with_backlog():
    issue = sn(
        fields=sn(
            status=sn(
                name='Backlog'
            )
        )
    )
    issues = {}
    issues['issue_obj'] = issue
    issues['workflow'] = {
        'Return to Backlog': '131',
        'Selected for development': '51',
        'Declare done': '171',
        'Flag': '181'
    }

    assert MainController(None).get_possible_workflows(issues) == [
        'Return to Backlog',
        'Selected for development',
        'Declare done',
        'Flag'
    ]
