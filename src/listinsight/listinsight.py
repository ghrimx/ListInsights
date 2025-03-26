import logging
from pathlib import Path
from qtpy import QtCore, QtWidgets, Slot

# from .dataviewer.dataviewer import DataViewer
# from .dataviewer.dataviewer import DataSet
from dataviewer.dataviewer import DataSet # for testing
from dataviewer.dataviewer import DataViewer # for testing

from utilities.utils import writeJson, readJson

logger = logging.getLogger(__name__)


class ListInsight(QtWidgets.QWidget):
    def __init__(self, rootpath: str = "", project_name: str = "", parent = None):
        super().__init__(parent)
        self._rootpath = Path(rootpath).joinpath("ListInsight")
        self._shortlist_file: str = ""
        self._tagged_file :str = ""
        self._project_file: str = ""
        self._project = {}

        if self._rootpath == "":
            return

        if not self._rootpath.joinpath("parquets").is_dir():
            try:
                self._rootpath.joinpath("parquets").mkdir(parents=True)
            except FileExistsError:
                pass

        self.loadProject(project_name)
        self.initUI()
        self.loadShortlist()
        self.loadTagger()

    def initUI(self):
        self.vbox = QtWidgets.QVBoxLayout()
        self.setLayout(self.vbox )

        self.tab_widget = QtWidgets.QTabWidget()
        self.tab_widget.setTabPosition(QtWidgets.QTabWidget.TabPosition.South)
        self.vbox.addWidget(self.tab_widget)

         # Dataviewer
        self.dataviewer = DataViewer(self._project)

        self.tab_widget.addTab(self.dataviewer, "DataViewer")

        self.tab_widget.addTab(QtWidgets.QWidget(), "Shaper")
        self.tab_widget.addTab(QtWidgets.QWidget(), "Analyzer")

        self.dataviewer.shortlister.sigSaveToJson.connect(self.saveShortList)
        self.dataviewer.tag_pane.sigSaveToJson.connect(self.saveTags)
        self.dataviewer.sigDatasetImported.connect(self.onDatasetImported)

    def createMenubar(self):
        self.menubar = QtWidgets.QMenuBar()
        self.vbox.insertWidget(0, self.menubar)

        self.menubar.addMenu("File")

    def loadProject(self, project_name: str):
        self._project_file = self._rootpath.joinpath("project.json").as_posix()
        self._shortlist_file = self._rootpath.joinpath("shortlist.json").as_posix()
        self._tagged_file = self._rootpath.joinpath("tagged.json").as_posix()

        if not QtCore.QFileInfo(self._project_file).exists():
            self._project["project_rootpath"] = self._rootpath.as_posix()
            self._project["project_name"] = project_name
            self._project["datasets"] = {}
            self._project["project_files"] = {"shortlist": self._shortlist_file,
                                              "tagged": self._tagged_file}
            with open(self._project_file, mode='w', encoding='utf8') as file:
                writeJson(self._project_file, self._project)
        else:
            self._project, err = readJson(self._project_file)

        if not QtCore.QFileInfo(self._shortlist_file).exists():
            with open(self._shortlist_file, mode='w', encoding='utf8') as file:
                pass

        if not QtCore.QFileInfo(self._tagged_file).exists():
            with open(self._tagged_file, mode='w', encoding='utf8') as file:
                pass

    def loadShortlist(self):
        data, err = readJson(self._shortlist_file)
        self.dataviewer.shortlister.model().load(data.copy())

    def loadTagger(self):
        data, err = readJson(self._tagged_file)
        self.dataviewer.tag_pane.model().load(data.copy(), True)

    @Slot(DataSet)
    def onDatasetImported(self, dataset: DataSet):
        datasets: dict = self._project["datasets"]
        datasets.update({dataset.uid:{"parquet":dataset.parquet.as_posix(), "primary_key": ""}})
        self.saveProject()
       
    @Slot(dict)
    def saveShortList(self, data: dict):
        writeJson(self._shortlist_file, data)

    @Slot(dict)
    def saveTags(self, data: dict):
        writeJson(self._tagged_file, data)

    def saveProject(self):
        writeJson(self._project_file, self._project)





