import os

basedir = os.path.abspath(os.path.dirname(__file__))
staticdir = os.path.join(basedir, 'static')
QSS_PATH = os.path.join(staticdir, 'qss', 'style.qss')
CREDENTIALS_PATH = os.path.join(basedir, 'my_credentials.txt')
POMODORO_MARK_PATH = os.path.join(staticdir, 'tomato.png')
RINGING_SOUND_PATH = os.path.join(staticdir, 'ring.wav')
LOGO_PATH = os.path.join(staticdir, 'logo.png')
