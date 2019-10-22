from PyQt5.QtWidgets import QMessageBox, QApplication
from PyQt5.QtCore import Qt
import requests
import functools


def catch_timeout_exception(function):
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            value = function(*args, **kwargs)
        except (requests.exceptions.ConnectionError,
                requests.exceptions.ReadTimeout):
            QApplication.restoreOverrideCursor()
            QMessageBox.warning(
                None,
                'Connection error',
                'Check your internet connection and try again'
            )
            return
        QApplication.restoreOverrideCursor()
        return value
    return wrapper
