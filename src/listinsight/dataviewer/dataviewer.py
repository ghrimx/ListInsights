import io
import logging
import pandas as pd
from pathlib import Path
from functools import partial
from qtpy import QtWidgets, QtCore, QtGui, Slot, Signal
from dataclasses import dataclass, asdict

from .shortlister import ShortLister
from .tagger import Tagger, TagDialog
from .filter import FilterPane, Filter

logger = logging.getLogger(__name__)


@dataclass
class Metadata:
    primary_key_name: str = ""
    primary_key_index: int = -1
    dataset_name: str = ""
    dataset_id: str = ""
    parquet: str = ""

    def to_dict(self):
        return asdict(self)
    

class DataSet:
    def __init__(self, df: pd.DataFrame, name: str):
        self._dataframe = df
        self._unfiltered_df = df.copy()
        self._metadata = Metadata()
        self.name = name
        self.filters: list[Filter] = []

    @property
    def dataframe(self) -> pd.DataFrame:
        return self._dataframe
    
    @dataframe.setter
    def dataframe(self, df):
        self._dataframe = df
    
    @property
    def unfiltered_df(self) -> pd.DataFrame:
        return self._unfiltered_df

    @property
    def name(self):
        return self._metadata.dataset_name
    
    @name.setter
    def name(self, sname: str):
        self._metadata.dataset_name = sname

    @property
    def parquet(self):
        return Path(self._metadata.parquet)
    
    @parquet.setter
    def parquet(self, pfile: Path):
        self._metadata.parquet = pfile.as_posix()

        try:
            self.uid = str(pfile.stat().st_birthtime_ns)
        except AttributeError as e:
            self.uid = str(pfile.stat().st_mtime)

    @property
    def uid(self):
        return self._metadata.dataset_id
    
    @uid.setter
    def uid(self, iid: str):
        self._metadata.dataset_id = iid

    @property
    def pk_name(self) -> str:
        return self._metadata.primary_key_name
    
    @pk_name.setter
    def pk_name(self, name: str):
        self._metadata.primary_key_name = name
        try:
            self._metadata.primary_key_index = self.dataframe.columns.get_loc(self.pk_name)
        except Exception as e:
            self._metadata.primary_key_index = None

    @property
    def pk_loc(self):
        return self._metadata.primary_key_index 
    
    @property
    def pk_type(self):
        return self.dataframe[self.pk_name].dtype
    
    def headers(self) -> list[str]:
        return self.dataframe.columns.values.tolist()
        
    @property
    def metadata(self) -> Metadata:
        return self._metadata
    
    @metadata.setter
    def metadata(self, meta):
        self._metadata = meta
        
    def __str__(self):
        return self.metadata

    def deserialize(self, json: dict|None):
        """Create Metadata and Filters from their JSON representation """
        if json is None:
            return

        dict_metadata: dict = json.get("metadata")
        metadata = Metadata(dict_metadata.get("primary_key_name"),
                            dict_metadata.get("primary_key_index"),
                            dict_metadata.get("dataset_name"),
                            dict_metadata.get("dataset_id"),
                            dict_metadata.get("parquet"))
        self.metadata = metadata
        
        filter_list: list[dict] = json.get("filters")
        dfilter: dict
        for dfilter in filter_list:
            filt = Filter(dfilter.get("attr"),
                          dfilter.get("oper"),
                          dfilter.get("value"),
                          dfilter.get("expr"))
            self.filters.append(filt)
        
    def serialize(self) -> dict:
        """Convert Metadata and Filters in their JSON representation"""
        info = {}
        info["metadata"] = self.metadata.to_dict()
        filters = []
        for filter in self.filters:
            filters.append(filter.to_dict())
        info["filters"] = filters
        
        return info

class PandasModel(QtCore.QAbstractTableModel):
    def __init__(self, dset: DataSet, parent=None):
        super(PandasModel, self).__init__(parent)
        self._dataset: DataSet = dset
        
    @property
    def dataset(self):
        return self._dataset
    
    def dataframe(self):
        return self._dataset.dataframe
    
    def unfiltered_df(self):
        return self._dataset.unfiltered_df
        
    def data(self, index: QtCore.QModelIndex, role: QtCore.Qt.ItemDataRole):
        if not index.isValid():
            return None

        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            return str(self.dataset.dataframe.iloc[index.row(), index.column()])

        return None

    def setData(self, index: QtCore.QModelIndex, value, role: int) -> bool:
        if role != QtCore.Qt.ItemDataRole.EditRole:
            return False

        if isinstance(value, list):
            value = ','.join(value)

        self.dataset.dataframe.iloc[index.row(), index.column()] = value
        self.dataChanged.emit(index, index,
                                [QtCore.Qt.ItemDataRole.DisplayRole, QtCore.Qt.ItemDataRole.EditRole])
        return True          
    
    def rowCount(self, index) -> int:
        if index == QtCore.QModelIndex():
            return len(self.dataset.dataframe)

        return 0

    def columnCount(self, index) -> int:
        if index == QtCore.QModelIndex():
            return len(self.dataset.headers())

        return 0
    
    def headerData(self, section: int, orientation: QtCore.Qt.Orientation, role: QtCore.Qt.ItemDataRole):
        """Override method from QAbstractTableModel

        Return dataframe index as vertical header data and columns as horizontal header data.
        """
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            if orientation == QtCore.Qt.Orientation.Horizontal:
                return str(self.dataset.dataframe.columns[section])

            if orientation == QtCore.Qt.Orientation.Vertical:
                return str(self.dataset.dataframe.index[section])

        return None

    def apply_pk_filter(self, sid: str):
        """Filter dataframe on primary key"""
        if self.dataset.pk_name == "":
            return
        
        if self.dataset.pk_type == "int64":
            try:
                sid = int(sid)
                expr = f"`{self.dataset.pk_name}` == {sid}"
            except:
                expr = f"`{self.dataset.pk_name}` == '{sid}'"
        else:
            expr = f"`{self.dataset.pk_name}` == '{sid}'"
        
        # df = pd.read_parquet(self.dataset.parquet, filters=[(self.dataset.pk_name, '=', sid)])
        df = self.dataset.unfiltered_df.query(expr)
        self.beginResetModel()
        self.dataset.dataframe = df
        self.endResetModel()
    
    #TODO
    def apply_user_filter(self):
        df = self.unfiltered_df()
        for filter in self.dataset.filters:
            if filter.enabled:
                try:
                    df = df.query(filter.expr)
                except Exception as e:
                    filter.failed = True
                    logger.exception(e)
                    return
        
        self.beginResetModel()
        self.dataset.dataframe = df
        self.endResetModel()

    def refresh(self):
        df = pd.read_parquet(self.dataset.parquet)
        self.beginResetModel()
        self.dataset.dataframe = df.copy()
        self.endResetModel()

    @Slot(str, int)
    def setPrimaryIndex(self, name):
        self.dataset.pk_name = name

class IndexMenu(QtWidgets.QMenu):
    sigIndexSetAsPrimaryKey = Signal(str, int)

    def __init__(self, index_name = "", primary_name = "", primary_idx = -1, parent=None):
        super().__init__(parent)
        self._index_name = index_name
        self._primary_idx = primary_idx

        index_title = QtGui.QAction(index_name, self)
        index_title.setDisabled(True)
        self.addAction(index_title)

        primary = QtGui.QAction("Set as primary key", self)
        primary.setCheckable(True)
        if index_name == primary_name:
            primary.setChecked(True)

        primary.triggered.connect(self.onSetPrimaryKey)
        self.addAction(primary)

    @Slot(bool)
    def onSetPrimaryKey(self, checked):
        if checked:
            self.sigIndexSetAsPrimaryKey.emit(self._index_name, self._primary_idx)
        else:
            self.sigIndexSetAsPrimaryKey.emit("", -1)
      

class DataView(QtWidgets.QTableView):
    sigOpenTagManager = Signal(QtCore.QModelIndex)
    sigAddToShortlist = Signal(str, str)
    sigDatasetInfoChanged = Signal(DataSet)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._table_name = ""
        self.setSortingEnabled(True)

        # Context Menu
        self.context_menu = QtWidgets.QMenu(self)
        self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.contextMenuEvent)

        self.action_openTagMenu = QtGui.QAction(QtGui.QIcon(":tags"), "Manage Tag", self, triggered=self.openTagMenu)
        self.action_show_indexmenu = QtGui.QAction("Show Index Menu", self, triggered=self.showIndexMenu)
        self.action_addToShortlist = QtGui.QAction("Add to Shortlist", self, triggered=self.addToShortlist)

        self.horizontalHeader().sortIndicatorChanged.connect(self.sortByColumn)

    @property
    def tablename(self):
        return self._table_name
    
    @tablename.setter
    def tablename(self, s: str):
        self._table_name = s

    def contextMenuEvent(self, event: QtGui.QMouseEvent):
        """Creating a context menu"""
        self.context_menu.addAction(self.action_openTagMenu)
        self.context_menu.addAction(self.action_show_indexmenu)
        self.context_menu.addAction(self.action_addToShortlist)
        self.context_menu.exec(QtGui.QCursor().pos())

    def updateContextMenu(self):
        model: PandasModel = self.model()
        if model.dataset.pk_name == "":
            self.action_openTagMenu.setEnabled(False)
            self.action_addToShortlist.setEnabled(False)
        else:
            self.action_openTagMenu.setEnabled(True)
            self.action_addToShortlist.setEnabled(True)
        
    @Slot()
    def openTagMenu(self):
        index = self.selectionModel().currentIndex()
        self.sigOpenTagManager.emit(index)

    @Slot()
    def showIndexMenu(self):
        index = self.selectionModel().currentIndex()
        model: PandasModel = self.model()
        index_name = model.headerData(index.column(),
                                      QtCore.Qt.Orientation.Horizontal,
                                      QtCore.Qt.ItemDataRole.DisplayRole)
        menu = IndexMenu(index_name, model.dataset.pk_name, index.column(), self)
        menu.sigIndexSetAsPrimaryKey.connect(model.setPrimaryIndex)
        menu.sigIndexSetAsPrimaryKey.connect(self.updateContextMenu)    
        menu.sigIndexSetAsPrimaryKey.connect(self.onPrimaryKeyChanged)    
        menu.popup(QtGui.QCursor().pos())
    
    @Slot() #TODO
    def addToShortlist(self):
        index: QtCore.QModelIndex = self.selectionModel().currentIndex()

        model: PandasModel = self.model()
        pk_value = index.sibling(index.row(), model.dataset.pk_loc).data(QtCore.Qt.ItemDataRole.DisplayRole)
        _tags = index.sibling(index.row(), model.dataframe().columns.get_loc("Tags")).data(QtCore.Qt.ItemDataRole.DisplayRole)
        
        if _tags == 'None':
            tags = ""

        self.sigAddToShortlist.emit(pk_value, tags)

    @Slot()
    def onPrimaryKeyChanged(self):
        # metadata: Metadata = self.model().dataset.metadata
        self.sigDatasetInfoChanged.emit(self.model().dataset)

    #TODO
    @Slot(int,QtCore.Qt.SortOrder)
    def sortByColumn(self, column, order):
        print(f"col:{column} - order:{order}")
        return super().sortByColumn(column, order)


class DataViewer(QtWidgets.QWidget):
    sigDatasetImported = Signal(DataSet)
    sigDatasetInfoChanged = Signal(DataSet)
    sigMessage = Signal(str)
    sigLoadingEnded = Signal(str)
    sigLoadingStarted = Signal(int, str)
    sigLoadingProgress = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.project = {}

        vbox = QtWidgets.QVBoxLayout(self)
        self.setLayout(vbox)

        # MdiArea
        self.mdi = QtWidgets.QMdiArea()
        self.mdi.setTabsMovable(True)
        self.mdi.setTabsClosable(True)

        # Actions & Toolbar
        self.createActions()
        self.createToolbar()
        
        self.tab = QtWidgets.QTabWidget()

        # LeftPane
        self.tag_pane = Tagger()
        self.shortlister = ShortLister()
        self.filter_pane = FilterPane()

        self.tab.addTab(self.tag_pane, "Tags")
        self.tab.addTab(self.shortlister, "ShortLister")
        self.tab.addTab(self.filter_pane, "Filter")

        self.splitter = QtWidgets.QSplitter()
        self.splitter.addWidget(self.tab)
        self.splitter.addWidget(self.mdi)
        
        vbox.addWidget(self.toolbar)
        vbox.addWidget(self.splitter)

        self.initDialogs()
        self.connectSignals()

    def createActions(self):      
        # Get info
        self.action_getInfo = QtGui.QAction(QtGui.QIcon(":information-2-line"), "Info", self, triggered=self.getInfo)

        # Sync Selection
        self.action_syncSelectionFilter = QtGui.QAction(QtGui.QIcon(":loop-right-line"),"Sync Selection", self)
        self.action_syncSelectionFilter.setCheckable(True)
        self.action_syncSelectionFilter.setEnabled(False)

        # Reset Filter
        self.action_resetFilters = QtGui.QAction(QtGui.QIcon(":filter-off-line"), "Reset filters", self)
        self.action_resetFilters.triggered.connect(self.resetFilters)

        self.action_minimizeAll = QtGui.QAction(QtGui.QIcon(':folder-2-line'), "Minimize", self, triggered=self.minimizeAll)
        self.action_showNormalAll = QtGui.QAction(QtGui.QIcon(':folder-2-line'), "Normal", self, triggered=self.showNormalAll)
        self.action_showMaximizeAll = QtGui.QAction(QtGui.QIcon(':folder-2-line'), "Maximized", self, triggered=self.showMaximizeAll)
        self.action_setTileView = QtGui.QAction(QtGui.QIcon(':layout-grid-line'), "Tile", self, triggered=self.setTileView)
        self.action_setTabbedView = QtGui.QAction(QtGui.QIcon(':folder-2-line'), "Tabbed", self, triggered=self.setTabbedView)

        self.action_close = QtGui.QAction("Cl&ose", self, statusTip="Close the active window", triggered=self.close)
        self.action_closeall = QtGui.QAction("Close &All", self, statusTip="Close all the windows", triggered=self.close_all)
    
    @Slot()
    def updateActionState(self):
        pks = 0
        for subwindow in self.mdi.subWindowList():
            model: PandasModel = subwindow.widget().model()
            
            if model.dataset.pk_name != "":
                pks += 1
        
        if pks == len(self.mdi.subWindowList()):
            self.action_syncSelectionFilter.setEnabled(True)
        else:
            self.action_syncSelectionFilter.setEnabled(False)

    def createToolbar(self):
        self.toolbar = QtWidgets.QToolBar(self)
        self.toolbar.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonIconOnly)

        # View menu
        viewmenu_toolbutton = QtWidgets.QToolButton(self)
        viewmenu_toolbutton.setIcon(QtGui.QIcon(':eye-line'))
        viewmenu_toolbutton.setText("Views")
        viewmenu_toolbutton.setPopupMode(QtWidgets.QToolButton.ToolButtonPopupMode.InstantPopup)

        viewmenu = QtWidgets.QMenu("View", self)

        cascade_menu = QtWidgets.QMenu("Cascade", self)
        cascade_menu.setIcon(QtGui.QIcon(':stack-line'))
        cascade_menu.addAction(self.action_minimizeAll)
        cascade_menu.addAction(self.action_showNormalAll)
        cascade_menu.addAction(self.action_showMaximizeAll)
        viewmenu.addMenu(cascade_menu)

        viewmenu.addAction(self.action_setTileView)
        viewmenu.addAction(self.action_setTabbedView)
        viewmenu_toolbutton.setMenu(viewmenu)
        
        # Window selection menu
        self.window_menu = QtWidgets.QMenu("Window", self)

        self.windowmenu_toolbutton = QtWidgets.QToolButton(self)
        self.windowmenu_toolbutton.setIcon(QtGui.QIcon(':window-2-line'))
        self.windowmenu_toolbutton.setPopupMode(QtWidgets.QToolButton.ToolButtonPopupMode.InstantPopup)
        self.windowmenu_toolbutton.setMenu(self.window_menu)
        self.update_window_menu()
        self.window_menu.aboutToShow.connect(self.update_window_menu)

        # Add to Toolbar
        self.toolbar.addWidget(viewmenu_toolbutton)
        self.toolbar.addWidget(self.windowmenu_toolbutton)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.action_getInfo)
        self.toolbar.addAction(self.action_resetFilters)
        self.toolbar.addAction(self.action_syncSelectionFilter)
        
        spacer = QtWidgets.QWidget()
        spacer.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Preferred)
        self.toolbar.addWidget(spacer)

        # self.progress = QtWidgets.QProgressBar(self.toolbar)
        # self.progress.setMaximumWidth(100)
        # self.toolbar.addWidget(self.progress)
                
    def initDialogs(self):
        self.tag_dialog: TagDialog = None

    def connectSignals(self):
        self.mdi.subWindowActivated.connect(self.setCurrentFilterModel)
        self.filter_pane.sigToggleFilter.connect(self.toggleFilter)
        self.filter_pane.sigFilterChanged.connect(self.onFilterChanged)
        # self.shortlister.sigTagsEdited.connect(self.tag_pane.)

    def createDataView(self, dataset: DataSet):
        if dataset is not None:
            pandas_model = PandasModel(dataset)
            table = DataView()
            table.tablename = dataset.name
            table.setModel(pandas_model)
            table.updateContextMenu()
            table.resizeColumnsToContents()
            table.setSortingEnabled(True)
            
            # Signals
            table.sigOpenTagManager.connect(self.onOpenTagManager)
            table.selectionModel().selectionChanged.connect(self.syncSelectionFilter)
            table.sigDatasetInfoChanged.connect(self.updateActionState)
            table.sigDatasetInfoChanged.connect(self.sigDatasetInfoChanged)
            table.sigAddToShortlist.connect(self.shortlister.addShortlistItem)

            subwindow = self.mdi.addSubWindow(table)

            subwindow.setWindowTitle(table.tablename)
            subwindow.show()

    #TODO
    def createFilterModel(self, dataset: DataSet):
        self.filter_pane.createModel(dataset.uid, dataset.filters, dataset.dataframe.dtypes.to_dict())
    
    @Slot(QtWidgets.QMdiSubWindow)
    def setCurrentFilterModel(self, subwindow: QtWidgets.QMdiSubWindow):
        if subwindow is None:
            return
        
        table: DataView = subwindow.widget()
        model: PandasModel = table.model()
        self.filter_pane.setCurrentModel(model.dataset.uid)

    @Slot(int)
    def toggleFilter(self, index):
        active_subwindow = self.mdi.activeSubWindow()

        if active_subwindow is None:
            return

        table: DataView = active_subwindow.widget()
        model: PandasModel = table.model()
        model.dataset.filters[index].enabled = not model.dataset.filters[index].enabled
        model.apply_user_filter()
        table.resizeColumnsToContents()
    
    @Slot()
    def onFilterChanged(self):
        active_subwindow = self.mdi.activeSubWindow()

        if active_subwindow is None:
            return

        table: DataView = active_subwindow.widget()
        model: PandasModel = table.model()
        dataset = model.dataset

        self.sigDatasetInfoChanged.emit(dataset)
        
    def isDatasetLoaded(self, filepath: Path) -> bool:
        for subwindow in self.mdi.subWindowList():
            table_name = subwindow.widget().tablename
            if table_name == filepath.stem.upper():
                return True
        return False
    
    def metadataFromJson(self, dataset_id: str) -> dict|None:
        dataset_list: list = self.project.get("datasets")
        if dataset_list is None:
            return {}
        
        metadata: dict
        dataset: dict
        for dataset in dataset_list:
            metadata = dataset.get("metadata")
            if metadata.get("dataset_id") == dataset_id:
                return metadata

    #TODO : merge with loadProjectData
    def loadFiles(self, files: list, update_json: bool = True):
        if not "project_rootpath" in self.project:
            return

        rootpath = Path(self.project.get("project_rootpath"))

        if len(files) == 0:
            return
        for file in files:
            filepath = Path(file)
            
            if self.isDatasetLoaded(filepath):
                continue

            datasets = self.readFile(filepath)
            if len(datasets) == 0:
                return

            dataset: DataSet
            for dataset in datasets:
                headers: list = dataset.headers()

                if not 'Tags' in headers:
                    headers.append('Tags')
                    # df = df.reindex(columns=headers)
                    dataset.dataframe.insert(len(dataset.headers()), 'Tags', None)

                parquetfile = rootpath.joinpath("parquets", f"{dataset.name}.parquet")
                parquet_folder = QtCore.QDir(rootpath.joinpath("parquets").as_posix())
                parquet_folder.mkpath(".")
                
                if dataset is not None and filepath.parent != parquetfile.parent:
                    if not self.save2Parquet(dataset.dataframe, parquetfile):
                        return

                dataset.parquet = parquetfile

                dataset_info: dict = self.getDatasetInfoFromProject(dataset.uid)
                dataset.deserialize(dataset_info)

                self.createDataView(dataset)
                self.createFilterModel(dataset)

                if update_json:
                    self.sigDatasetImported.emit(dataset)
            
        self.updateActionState()

    @Slot()
    def loadProjectData(self):
        dataset_list: list = self.project.get("datasets")
        if dataset_list is None:
            return

        cnt = 0
        self.sigLoadingStarted.emit(len(dataset_list), "Loading datasets...")
        
        for dataset_info in dataset_list:
            parquet_str = dataset_info.get("metadata", {}).get("parquet")
            self.sigLoadingProgress.emit(cnt)
            parquet = Path(parquet_str)

            # Skip if file is missing
            if not parquet.exists():
                logger.info(f"File not found: {parquet.as_posix()}")
                continue

            # Skip if dataset already loaded
            if self.isDatasetLoaded(parquet):
                continue
            
            datasets = self.readFile(parquet)
            dataset: DataSet = datasets[0]
            dataset.deserialize(dataset_info)

            self.createDataView(dataset)
            self.createFilterModel(dataset)
            cnt += 1

        self.sigLoadingProgress.emit(len(dataset_list))
        self.updateActionState()
        self.sigLoadingEnded.emit(f"Dataset loaded ({cnt}/{len(dataset_list)})")
    
    @classmethod
    def readFile(cls, filepath: Path, **kwargs) -> list[DataSet]:
        """Read file (*.xlsx, *.xls, *.csv, *.parquet) and return a list of dataset"""
        dfs = []
        file_type = filepath.suffix.lower()

        handlers = {
            '.csv': pd.read_csv,
            '.xlsx': pd.read_excel,
            '.xls': pd.read_excel,
            '.parquet': pd.read_parquet
        }

        reader = handlers.get(file_type)
        if reader is None:
            logger.error(f"Unsupported file type: {file_type}")
            return None

        if  reader == pd.read_csv:
            codecs = ["utf-8", "latin-1"]
            seps = [",", ";"]
            i = 0
            j = 0
            reading = True
            while reading:
                try:
                    df = reader(filepath, encoding=codecs[i], sep=seps[j])
                except UnicodeDecodeError:
                    i += 1
                except pd.errors.ParserError:
                    j += 1
                except Exception as e:
                    logger.error(e)
                    reading = False
                    break
                else:
                    reading = False
                    break
            dataset = DataSet(df, filepath.stem.upper())
            dfs = [dataset]
        elif reader == pd.read_excel:
            with pd.ExcelFile(filepath) as xls:
                for sheet in xls.sheet_names:
                    df = xls.parse(sheet)
                    dataset = DataSet(df, sheet.upper())
                    dfs.append(dataset)
        else:
            df = reader(filepath, **kwargs)
            dataset = DataSet(df, filepath.stem.upper())
            dfs = [dataset]

        return dfs
    
    #TODO
    def getDatasetInfoFromProject(self, dataset_id) -> dict | None:
        json_dataset: dict
        for json_dataset in self.project.get("datasets", []):
            if json_dataset.get("metadata", {}).get("dataset_id") == dataset_id:
                return json_dataset
        
        return None
    
    @classmethod
    def save2Parquet(cls, df: pd.DataFrame, filepath: Path) -> bool:
        """Save pandas dataframe to Apache Parquet file"""
        try:
            df.to_parquet(filepath.with_suffix('.parquet').as_posix())
        except Exception as e:
            logger.error(e)
            return False
        else:
            return True
  
    @Slot()
    def getInfo(self):
        active_subwindow = self.mdi.activeSubWindow()

        if active_subwindow is None:
            return

        buffer = io.StringIO()
        table: DataView = active_subwindow.widget()
        model: PandasModel = table.model()
        model.dataframe().info(buf=buffer)
        s = buffer.getvalue()

        table_name_label = QtWidgets.QLabel(f"Table name: {table.tablename}")
        table_name_label.setFont(QtGui.QFont("Courier New", 10))
        filename_label = QtWidgets.QLabel(f"Filename: {model.dataset.parquet}")
        filename_label.setFont(QtGui.QFont("Courier New", 10))
        pk_label = QtWidgets.QLabel(f"Primary Key: {model.dataset.pk_name}")
        pk_label.setFont(QtGui.QFont("Courier New", 10))

        info_text = QtWidgets.QLabel(self)
        info_text.setTextFormat(QtCore.Qt.TextFormat.PlainText)
        info_text.setFont(QtGui.QFont("Courier New", 10))
        info_text.setAlignment(QtCore.Qt.AlignmentFlag.AlignJustify)
        info_text.setText(s.expandtabs(4))

        info_widget = QtWidgets.QDialog(self)
        info_widget.setWindowTitle("DataFrame Info")
        vbox = QtWidgets.QVBoxLayout()
        info_widget.setLayout(vbox)

        vbox.addWidget(table_name_label)
        vbox.addWidget(filename_label)
        vbox.addWidget(pk_label)
        vbox.addWidget(info_text)
        info_widget.show()

    @Slot(QtCore.QItemSelection, QtCore.QItemSelection)
    def syncSelectionFilter(self, selected: QtCore.QItemSelection, deselected: QtCore.QItemSelection):
        if self.action_syncSelectionFilter.isChecked():
            indexes = selected.indexes()
            model: PandasModel = self.mdi.activeSubWindow().widget().model()

            try:
                index: QtCore.QModelIndex = indexes[0]
            except:
                return
            
            sid = index.sibling(index.row(), model.dataset.pk_loc).data(QtCore.Qt.ItemDataRole.DisplayRole)

            for subwindow in self.mdi.subWindowList():
                if subwindow == self.mdi.activeSubWindow():
                    continue
                
                widget: DataView = subwindow.widget()
                widget.model().apply_pk_filter(sid)
                widget.resizeColumnsToContents()

    @Slot()
    def resetFilters(self):
        for subwindow in self.mdi.subWindowList():
            subwindow.widget().model().refresh()

    @Slot(QtCore.QModelIndex)
    def onOpenTagManager(self, index: QtCore.QModelIndex):
        if self.tag_dialog is None:
            self.tag_dialog = TagDialog()
            self.tag_dialog.sigAdd2tag.connect(self.add2Tag)

        table: DataView = self.mdi.activeSubWindow().widget()
        table_model: PandasModel = table.model()

        tags: str = index.sibling(index.row(), table.model().columnCount(QtCore.QModelIndex())-1).data(QtCore.Qt.ItemDataRole.DisplayRole)
       
        if tags == 'None':
            self.tag_dialog.tag_list.model().setStringList([])
        else:
            self.tag_dialog.tag_list.model().setStringList(tags.split(","))

        self.tag_dialog.exec()

    @Slot(str)
    def add2Tag(self, tagname: str):
        table: DataView = self.mdi.activeSubWindow().widget()
        table_model: PandasModel = table.model()
        index = table.selectionModel().currentIndex()

        primary_key: str = index.sibling(index.row(), table_model.dataset.pk_loc).data(QtCore.Qt.ItemDataRole.DisplayRole)
        self.tag_pane.model().add2Tag([primary_key], tagname)
         
    @Slot()
    def update_window_menu(self):
        self.window_menu.clear()
        self.window_menu.addAction(self.action_close)
        self.window_menu.addAction(self.action_closeall)
        self.window_menu.addSeparator()

        windows = self.mdi.subWindowList()
        
        for i, window in enumerate(windows):
            child: DataView = window.widget()

            f = child.tablename
            text = f'{i + 1} {f}'
            if i < 9:
                text = '&' + text

            action = self.window_menu.addAction(text)
            action.setCheckable(True)
            action.setChecked(window is self.mdi.activeSubWindow())
            slot_func = partial(self.set_active_sub_window, window=window)
            action.triggered.connect(slot_func)

    def set_active_sub_window(self, window):
        if window:
            self.mdi.setActiveSubWindow(window)

    def close(self):
        active_sub_window = self.mdi.activeSubWindow()
        
        if active_sub_window is None:
            return
        
        self.mdi.closeActiveSubWindow()
    
    def close_all(self):
        self.mdi.closeAllSubWindows()

    def setTabbedView(self):
        self.mdi.setViewMode(QtWidgets.QMdiArea.ViewMode.TabbedView)

    def setCascadeView(self):
        self.mdi.setViewMode(QtWidgets.QMdiArea.ViewMode.SubWindowView)
        self.mdi.cascadeSubWindows()
    
    def setTileView(self):
        self.mdi.setViewMode(QtWidgets.QMdiArea.ViewMode.SubWindowView)
        for subwindow in self.mdi.subWindowList():
            subwindow.showMaximized()
        self.mdi.tileSubWindows()

    def minimizeAll(self):
        self.setCascadeView()
        for subwindow in self.mdi.subWindowList():
            subwindow.showMinimized()
    
    def showNormalAll(self):
        self.setCascadeView()
        for subwindow in self.mdi.subWindowList():
            subwindow.showNormal()

    def showMaximizeAll(self):
        self.setCascadeView()
        for subwindow in self.mdi.subWindowList():
            subwindow.showMaximized()
    
    def closeEvent(self, a0): #TODO
        """Save dataframe to Parquet file upon closing the dataviewer"""
        for subwindow in self.mdi.subWindowList():
            model: PandasModel = subwindow.widget().model()
            self.save2Parquet(model.dataframe(), model.dataset.parquet)
        return super().closeEvent(a0)