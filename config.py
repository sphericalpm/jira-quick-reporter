import os

basedir = os.path.abspath(os.path.dirname(__file__))
staticdir = os.path.join(basedir, 'static')
QSS_PATH = os.path.join(staticdir, 'qss', 'style.qss')
CREDENTIALS_PATH = os.path.join(basedir, 'my_credentials.txt')
LOGO_PATH = os.path.join(staticdir, 'logo.png')
