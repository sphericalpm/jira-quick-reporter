import PyInstaller.__main__

PyInstaller.__main__.run([
    '--name=JQR',
    '--onedir',
    '--windowed',
    '--add-data=static:static',
    '--icon=static/logo.pg',
    'app.py',
])
