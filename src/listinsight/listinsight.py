import logging
from pathlib import Path
from qtpy import QtCore, QtWidgets, Slot

# from .dataviewer.dataviewer import DataViewer
# from .dataviewer.dataviewer import DataSet
from dataviewer.dataviewer import DataSet # for testing
from dataviewer.dataviewer import DataViewer, Metadata # for testing

from utilities.utils import writeJson, readJson

logger = logging.getLogger(__name__)


class ListInsight(QtWidgets.QWidget):
    def __init__(self, rootpath: str = "", project_name: str = "", parent = None):
        super().__init__(parent)
        self._rootpath: Path = Path(rootpath)
        self._project_file: Path = self._rootpath.joinpath("project.json")
        self._shortlist_file: Path = self._rootpath.joinpath("shortlist.json")
        self._tagged_file: Path = self._rootpath.joinpath("tagged.json")
        self._project = {}
        self._project_name = project_name
        self.initUI()

    def initUI(self):
        self.vbox = QtWidgets.QVBoxLayout()
        self.vbox.setSpacing(0)
        self.vbox.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.vbox )

        self.tab_widget = QtWidgets.QTabWidget()
        self.tab_widget.setTabPosition(QtWidgets.QTabWidget.TabPosition.South)
        self.vbox.addWidget(self.tab_widget)

         # Dataviewer
        self.dataviewer = DataViewer()

        self.tab_widget.addTab(self.dataviewer, "DataViewer")

        self.tab_widget.addTab(QtWidgets.QWidget(), "Shaper")
        self.tab_widget.addTab(QtWidgets.QWidget(), "Analyzer")

        self.dataviewer.shortlister.sigSaveToJson.connect(self.saveShortList)
        self.dataviewer.tag_pane.sigSaveToJson.connect(self.saveTags)
        self.dataviewer.sigDatasetImported.connect(self.onMetadataChanged)
        self.dataviewer.sigPrimaryKeyChanged.connect(self.onMetadataChanged)
        self.dataviewer.sigLoadProject.connect(self.loadProject)
        self.dataviewer.sigNewProject.connect(self.createProject)

    def createMenubar(self):
        self.menubar = QtWidgets.QMenuBar()
        self.vbox.insertWidget(0, self.menubar)

        self.menubar.addMenu("File")

    def selectProject(self):
        file = QtWidgets.QFileDialog.getOpenFileName(caption="Select Project file",
                                                     directory=self._rootpath.as_posix(),
                                                     filter="project.json")
        if not file[0]:
            return False

        self._project_file = Path(file[0])
        self._rootpath = self._project_file.parent

        return True

    def createProject(self) -> bool:
        project_name, ok = QtWidgets.QInputDialog().getText(self, 
                                                    "Project Name",
                                                    "Project name:", QtWidgets.QLineEdit.EchoMode.Normal)
        if not ok:
            return

        folder = QtWidgets.QFileDialog.getExistingDirectory(self,
                                                            caption="Select Project folder",
                                                            directory=self._rootpath.as_posix(),
                                                            options=QtWidgets.QFileDialog.Option.ShowDirsOnly)

        if folder == "":
            return
        
        if not self.makeProjectFile(folder, project_name):
            return        
        
        self._rootpath = Path(folder)
        self._project_file = self._rootpath.joinpath("project.json")
        self._shortlist_file: Path = self._rootpath.joinpath("shortlist.json")
        self._tagged_file: Path = self._rootpath.joinpath("tagged.json")

        self.dataviewer.mdi.closeAllSubWindows()
        self.loadProject()
    
    @classmethod
    def makeProjectFile(cls, folder: str, project_name: str) -> bool:
        rootpath = Path(folder)

        if not rootpath.exists():
            return False

        project_file = rootpath.joinpath("project.json")
        shortlist_file: Path = rootpath.joinpath("shortlist.json")
        tagged_file: Path = rootpath.joinpath("tagged.json")

        project = {}
        project["project_rootpath"] = rootpath.as_posix()
        project["project_name"] = project_name
        project["datasets"] = {}
        project["project_files"] = {"shortlist": shortlist_file.as_posix(),
                                        "tagged": tagged_file.as_posix()}
        
        with open(project_file, mode='w', encoding='utf8') as file:
            ok, err = writeJson(project_file.as_posix(), project)
        
        if not ok:
            return False

        return True
    
    def validateProjectJson(self):
        if len(self._project) == 0:
            return False
        if not "project_rootpath" in self._project:
            return False
        if not "project_name" in self._project:
            return False
        if not "datasets" in self._project:
            return False
        if not "project_files" in self._project:
            return False
        
        return True

    def loadProject(self):
        if not self._project_file.exists():
            return

        self._project, err = readJson(self._project_file.as_posix())

        if err != "":
            return
        
        if not self.validateProjectJson():
            return
        
        self.dataviewer.project = self._project
        self._shortlist_file = Path(self._project["project_files"]["shortlist"])
        self._tagged_file = Path(self._project["project_files"]["tagged"])

        self.dataviewer.loadProjectData()
        self.loadShortlist()
        self.loadTagger()
        self.dataviewer.action_import_data.setDisabled(False)

    def loadShortlist(self):
        if not self._shortlist_file.exists():
            with open(self._shortlist_file, mode='w', encoding='utf8') as file:
                pass

        data, err = readJson(self._shortlist_file.as_posix())
        self.dataviewer.shortlister.model().load(data.copy())

    def loadTagger(self):
        if not self._tagged_file.exists():
            with open(self._tagged_file, mode='w', encoding='utf8') as file:
                pass

        data, err = readJson(self._tagged_file.as_posix())
        self.dataviewer.tag_pane.model().load(data.copy())

    @Slot(Metadata)
    def onMetadataChanged(self, metadata: Metadata):
        datasets_info: dict = self._project["datasets"]
        datasets_info.update({metadata.dataset_id:{"parquet": metadata.parquet, "primary_key": metadata.primary_key_name}})
        self.saveProject()
       
    @Slot(dict)
    def saveShortList(self, data: dict):
        writeJson(self._shortlist_file.as_posix(), data)

    @Slot(dict)
    def saveTags(self, data: dict):
        writeJson(self._tagged_file.as_posix(), data)

    def saveProject(self):
        writeJson(self._project_file.as_posix(), self._project)





