from PyQt6 import QtWidgets, QtAds

from resources import qrc_resources
from dataviewer import DataViewer

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MainWindow")

        self.dataviewer = DataViewer()

    def initUI(self):
        self.dataviewer.showMaximized()
        # self.dataviewer.selectFiles()