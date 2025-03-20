import logging
from qtpy import QtCore, QtWidgets, Slot

from dataviewer import DataViewer

from utilities.utils import writeJson, readJson

logger = logging.getLogger(__name__)


class ListInsight(QtWidgets.QTabWidget):
    def __init__(self, rootpath: str = "", parent = None):
        super().__init__(parent)
        self._rootpath = rootpath
        self._shortlist_file: str = ""
        self._tagged_file :str = ""

        if not QtCore.QFileInfo(self._rootpath).isDir():
            self._rootpath = QtCore.QFileInfo(__file__).absolutePath()

        # Dataviewer
        self.dataviewer = DataViewer()
        self.addTab(self.dataviewer, "DataViewer")

        # self.addTab(QtWidgets.QWidget(), "Shaper")
        # self.addTab(QtWidgets.QWidget(), "Analyzer")

        self.dataviewer.shortlister.sigSaveToJson.connect(self.saveShortList)
        self.dataviewer.tag_pane.sigSaveToJson.connect(self.saveTags)
        
        self.setShortlistfile(QtCore.QDir(self._rootpath).filePath("shortlist.json"))
        self.setTaggedFile(QtCore.QDir(self._rootpath).filePath("tagged.json"))

    def setShortlistfile(self, file_path: str):
        self._shortlist_file = QtCore.QFileInfo(__file__).absoluteDir().filePath(file_path)

        if not QtCore.QFileInfo(self._shortlist_file).exists():
            with open(self._shortlist_file, mode='w', encoding='utf8') as file:
                pass

        self.loadShortlist()

    def loadShortlist(self):
        data, err = readJson(self._shortlist_file)
        self.dataviewer.shortlister.model().load(data.copy())

    def setTaggedFile(self, file_path: str):
        self._tagged_file = QtCore.QFileInfo(__file__).absoluteDir().filePath(file_path)

        if not QtCore.QFileInfo(self._tagged_file).exists():
            with open(self._tagged_file, mode='w', encoding='utf8') as file:
                pass

        self.loadTagger()

    def loadTagger(self):
        data, err = readJson(self._tagged_file)
        self.dataviewer.tag_pane.model().load(data.copy(), True)

    @Slot(dict)
    def saveShortList(self, data: dict):
        writeJson(self._shortlist_file, data)

    @Slot(dict)
    def saveTags(self, data: dict):
        writeJson(self._tagged_file, data)





