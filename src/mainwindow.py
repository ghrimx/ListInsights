from qtpy import QtWidgets, QtCore
import json
from resources import qrc_resources
from dataviewer import DataViewer
from shortlister import ShortLister, ShortListModel

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MainWindow")
        
        self.dataviewer = DataViewer.setup("shortlist.json", "tagged.json")

        self.tab = QtWidgets.QTabWidget()
        self.tab.addTab(self.dataviewer, "DataFrame")

        shortlister = ShortLister()

        json_path = QtCore.QFileInfo(__file__).absoluteDir().filePath("shortlist.json")

        with open(json_path) as file:
            document = json.load(file)
            shortlister.model().load(document)

        self.tab.addTab(shortlister, "ShortLister")


    def initUI(self):
        if self.dataviewer is None:
            return
        
        self.tab.showMaximized()

