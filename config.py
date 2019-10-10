import os

BASEDIR = os.path.abspath(os.path.dirname(__file__))
STATICDIR = os.path.join(BASEDIR, 'static')
QSS_PATH = os.path.join(STATICDIR, 'qss', 'style.qss')
CREDENTIALS_PATH = os.path.join(BASEDIR, 'my_credentials.txt')
POMODORO_MARK_PATH = os.path.join(STATICDIR, 'tomato.png')
RINGING_SOUND_PATH = os.path.join(STATICDIR, 'ring.wav')
LOGO_PATH = os.path.join(STATICDIR, 'logo.png')
