from PyQt5.QtWidgets import QMessageBox, QApplication
from PyQt5.QtCore import Qt
from requests.exceptions import ConnectionError, ReadTimeout
import functools


def catch_timeout_exception(function):
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        try:
            value = function(*args, **kwargs)
        except (ConnectionError,
                ReadTimeout):
            QMessageBox.warning(
                None,
                'Connection error',
                'Check your internet connection and try again'
            )
            return
        return value
    return wrapper
