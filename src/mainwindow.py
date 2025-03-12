from qtpy import QtWidgets

from resources import qrc_resources
from dataviewer import DataViewer

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MainWindow")

        self.dataviewer = DataViewer('src/datastore.json')

    def initUI(self):
        self.dataviewer.showMaximized()
