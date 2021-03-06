from PyQt5.QtWidgets import QComboBox
from PyQt5 import QtCore


class MyQComboBox(QComboBox):
    def __init__(self, scroll_widget=None, *args, **kwargs):
        super(MyQComboBox, self).__init__(*args, **kwargs)
        self.scroll_widget = scroll_widget
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

    def wheelEvent(self, *args, **kwargs):
        '''Remove possibility to change combobox items
        by wheel
        '''
        if self.hasFocus():
            return QComboBox.wheelEvent(self, *args, **kwargs)
        else:
            return self.scroll_widget.wheelEvent(*args, **kwargs)
