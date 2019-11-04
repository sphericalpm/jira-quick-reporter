import os

BASEDIR = os.path.abspath(os.path.dirname(__file__))
STATICDIR = os.path.join(BASEDIR, 'static')
QSS_PATH = os.path.join(STATICDIR, 'qss', 'style.qss')
CREDENTIALS_PATH = os.path.join(BASEDIR, 'my_credentials.txt')
POMODORO_MARK_PATH = os.path.join(STATICDIR, 'tomato.png')
RING_SOUND_PATH = os.path.join(STATICDIR, 'ring.wav')
LOGO_PATH = os.path.join(STATICDIR, 'logo.png')
LOGGED_TIME_DIR = os.path.join(BASEDIR, 'log')

with open(QSS_PATH, 'r') as qss_file:
    QSS = qss_file.read()

# ms * min = 1 hour
LOG_TIME = 60000 * 60
# 1 minute
REFRESH_TIME = 60000
ISSUES_COUNT = 10

MAX_RETRIES = 0  # we need it because without it our app will not be
# available (for 15 sec) in case of bad connection or IP blocking
FILTERS_PATH = os.path.join(BASEDIR, 'filters.ini')
SEARCH_ITEM_NAME = 'search issues'
MY_ISSUES_ITEM_NAME = 'my open issues'
FILTERS_DEFAULT_SECTION_NAME = 'Filters'
DEFAULT_FILTERS = {SEARCH_ITEM_NAME: 'order by created desc',
                   MY_ISSUES_ITEM_NAME: 'assignee = currentuser() '
                                     'and resolution = unresolved'
                   }
FILTER_FIELD_HELP_URL = 'https://confluence.atlassian.com/display/JIRASOFTWARECLOUD/Advanced+searching'

SERVER = 'https://spherical.atlassian.net'
