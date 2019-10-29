from PyQt5.QtWidgets import QWidget, QApplication

from config import QSS_PATH


class CenterWindow(QWidget):
    def __init__(self):
        super().__init__()
        frame_gm = self.frameGeometry()
        screen = QApplication.desktop().screenNumber(
            QApplication.desktop().cursor().pos()
        )
        center_point = QApplication.desktop().screenGeometry(screen).center()
        frame_gm.moveCenter(center_point)
        self.move(frame_gm.topLeft())

    def set_style(self):
        with open(QSS_PATH, 'r') as qss_file:
            self.setStyleSheet(qss_file.read())
