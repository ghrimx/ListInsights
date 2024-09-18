from PyQt6 import QtWidgets

from layout_colorwidget import Color

class DataViewer(QtWidgets.QMdiArea):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.addSubWindow(Color("red"))
        self.addSubWindow(Color("green"))
        self.addSubWindow(Color("blue"))
        self.addSubWindow(Color("yellow"))

        self.tileSubWindows()
