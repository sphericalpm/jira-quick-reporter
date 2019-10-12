from PyQt5.QtWidgets import QWidget, QApplication


class CenterWindow(QWidget):
    def __init__(self):
        super().__init__()

    def center(self):
        frame_gm = self.frameGeometry()
        screen = QApplication.desktop().screenNumber(
            QApplication.desktop().cursor().pos()
        )
        center_point = QApplication.desktop().screenGeometry(screen).center()
        frame_gm.moveCenter(center_point)
        self.move(frame_gm.topLeft())
