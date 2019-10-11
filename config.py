import os

BASEDIR = os.path.abspath(os.path.dirname(__file__))
STATICDIR = os.path.join(BASEDIR, 'static')
QSS_PATH = os.path.join(STATICDIR, 'qss', 'style.qss')
CREDENTIALS_PATH = os.path.join(BASEDIR, 'my_credentials.txt')
LOGO_PATH = os.path.join(STATICDIR, 'logo.png')

MAX_RETRIES=0
