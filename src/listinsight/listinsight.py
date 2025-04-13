import logging
from pathlib import Path
from qtpy import QtCore, QtWidgets, Slot, QtGui

from dataviewer.dataviewer import DataViewer, Metadata # for testing
from dataviewer.json_model import JsonModel # for testing

from utilities.utils import writeJson, readJson


logger = logging.getLogger(__name__)


class ProjectInfo(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Project Info")
        self.model = JsonModel()
        self.view = QtWidgets.QTreeView()
        self.view.setModel(self.model)
        
        vbox = QtWidgets.QVBoxLayout()
        self.setLayout(vbox)
        vbox.addWidget(self.view)

    def load(self, data: dict):
        self.model.load(data)
        self.view.expandAll()
        self.view.resizeColumnToContents(0)
        self.view.resizeColumnToContents(1)
        self.resize(self.view.width(), self.view.height())

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
        # self.vbox = QtWidgets.QHBoxLayout()
        self.vbox = QtWidgets.QGridLayout()
        self.vbox.setSpacing(0)
        self.vbox.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.vbox )

        self.tab_widget = QtWidgets.QTabWidget()
        self.tab_widget.setTabPosition(QtWidgets.QTabWidget.TabPosition.South)
        self.vbox.addWidget(self.tab_widget, 0, 1)

         # Dataviewer
        self.dataviewer = DataViewer()

        self.tab_widget.addTab(self.dataviewer, "DataViewer")

        self.tab_widget.addTab(QtWidgets.QWidget(), "Shaper")
        self.tab_widget.addTab(QtWidgets.QWidget(), "Analyzer")

        self.dataviewer.shortlister.sigSaveToJson.connect(self.saveShortList)
        self.dataviewer.tag_pane.sigSaveToJson.connect(self.saveTags)
        self.dataviewer.sigPrimaryKeyChanged.connect(self.onMetadataChanged)
        self.dataviewer.sigDatasetImported.connect(self.onMetadataChanged)
        self.dataviewer.sigMessage.connect(self.updateStatusbarMessage)
        self.dataviewer.sigLoadingProgress.connect(self.updateProgessbar)
        self.dataviewer.sigLoadingStarted.connect(self.setProgessbar)
        self.dataviewer.sigLoadingEnded.connect(self.updateStatusbarMessage)

        self.createMenubar()
        self.createStatusbar()
        self.initDialogs()

    def createMenubar(self):
        self.toolbar = QtWidgets.QToolBar()
        self.toolbar.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.toolbar.setOrientation(QtCore.Qt.Orientation.Vertical)
        self.vbox.addWidget(self.toolbar,0,0)
        
        self.action_new_project = QtGui.QAction(QtGui.QIcon(":archive-2-line"),
                                                "New project",
                                                self,
                                                triggered=self.createProject)
        self.action_select_project = QtGui.QAction(QtGui.QIcon(":inbox-archive-line"),
                                                   "Select project",
                                                   self,
                                                   triggered=self.selectProject)
        self.action_load_project = QtGui.QAction(QtGui.QIcon(":archive-stack-line"),
                                                 "Load project",
                                                 self,
                                                 triggered=self.loadProject)
        self.action_import_data = QtGui.QAction(QtGui.QIcon(":import-line"),"Import new dataset",
                                                self,
                                                triggered=self.loadFiles)
        self.action_import_data.setDisabled(True)
        self.action_projectInfo = QtGui.QAction(QtGui.QIcon(":information-2-line"), "Info", self, triggered=self.projectInfo)

        self.toolbar.addAction(self.action_new_project)
        self.toolbar.addAction(self.action_select_project)
        self.toolbar.addAction(self.action_load_project)
        self.toolbar.addAction(self.action_import_data)
        self.toolbar.addAction(self.action_projectInfo)

        spacer = QtWidgets.QWidget()
        spacer.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Preferred)
        self.toolbar.addWidget(spacer)

    def createStatusbar(self):
        self.statusbar = QtWidgets.QStatusBar(self)
        self.vbox.addWidget(self.statusbar, 1, 1, QtCore.Qt.AlignmentFlag.AlignLeft)
        self.status_label = QtWidgets.QLabel()
        self.status_label.setMinimumWidth(150)
        self.statusbar.addPermanentWidget(self.status_label)

    @Slot(str)
    def updateStatusbarMessage(self, msg: str):
        self.status_label.setText(msg)
    
    @Slot(int,str)
    def setProgessbar(self, i: int, m: str):
        self.progress = QtWidgets.QProgressBar()
        self.progress.setMinimum(0)
        self.progress.setMaximum(i)
        self.progress.setFixedHeight(self.status_label.height())
        self.statusbar.addWidget(self.progress)
        self.status_label.setText(m)

    @Slot(int)
    def updateProgessbar(self, i: int):
        self.progress.setValue(i)
        if self.progress.maximum() == i:
            self.statusbar.removeWidget(self.progress)
    
    def initDialogs(self):
        self.info_dialog: ProjectInfo = None

    def projectInfo(self):
        if self.info_dialog is None:
            self.info_dialog = ProjectInfo()

        self.info_dialog.load(self._project)
        self.info_dialog.exec()

    def selectFiles(self, dir: str = "", filter: str = "*.*") -> list:
        files = QtWidgets.QFileDialog.getOpenFileNames(caption="Select files",
                                                       directory=dir,
                                                       filter=filter)
        return files[0]
 
    def selectProject(self):
        file = QtWidgets.QFileDialog.getOpenFileName(caption="Select Project file",
                                                     directory=self._rootpath.as_posix(),
                                                     filter="project.json")
        if not file[0]:
            return

        self._project_file = Path(file[0])
        self._rootpath = self._project_file.parent
        self.dataviewer.mdi.closeAllSubWindows()

        QtCore.QTimer.singleShot(200, self.loadProject)

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
        project["datasets"] = []
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
        if not isinstance(self._project["datasets"], list):
            return False
        if not "project_files" in self._project:
            return False
        if Path(self._project["project_rootpath"]) != self._rootpath:
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
        self.updateActionState()

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

    def loadFiles(self):
        files = self.selectFiles(self._rootpath.as_posix(), filter="*.csv *.xlsx *.parquet")
        self.dataviewer.loadFiles(files)

    @Slot(Metadata)
    def onMetadataChanged(self, metadata: Metadata):
        metadata_list: list = self._project.get("datasets")
        if metadata_list is None:
            return

        metadata_dict: dict
        for i in range(len(metadata_list)):
            metadata_dict = metadata_list[i]
            if metadata_dict.get("dataset_id") == metadata.dataset_id:
                metadata_list[i] = metadata.to_dict()
                break
        else:
            metadata_list.append(metadata.to_dict())
        self.saveProject()

    @Slot()
    def updateActionState(self):
        if "project_rootpath" in self._project:
            self.action_import_data.setEnabled(True)
        else:
            self.action_import_data.setEnabled(False)
       
    @Slot(dict)
    def saveShortList(self, data: dict):
        writeJson(self._shortlist_file.as_posix(), data)

    @Slot(dict)
    def saveTags(self, data: dict):
        writeJson(self._tagged_file.as_posix(), data)

    def saveProject(self):
        writeJson(self._project_file.as_posix(), self._project)





