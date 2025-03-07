import io
import logging
import pandas as pd
from pathlib import Path
from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtCore import pyqtSlot as Slot, pyqtSignal as Signal

from utilities import config as mconf

logger = logging.getLogger(__name__)


class PandasModel(QtCore.QAbstractTableModel):
    def __init__(self, dataframe: pd.DataFrame, sourcefile: Path, parent=None):
        super(PandasModel, self).__init__(parent)
        self._primary_column_name = ""
        self._primary_column_index = -1
        self._dataframe: pd.DataFrame = dataframe
        self.sourcefile: Path = sourcefile

    @property
    def dataframe(self):
        return self._dataframe
    
    @dataframe.setter
    def dataframe(self, df: pd.DataFrame):
        self._dataframe = df

    @property
    def primary_column_name(self):
        return self._primary_column_name
    
    @primary_column_name.setter
    def primary_column_name(self, s: str):
        self._primary_column_name = s

    @property
    def primary_column_index(self):
        return self._primary_column_index
    
    @primary_column_index.setter
    def primary_column_index(self, i: int):
        self._primary_column_index = i
    
    def data(self, index: QtCore.QModelIndex, role: QtCore.Qt.ItemDataRole):
        if not index.isValid():
            return None

        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            return str(self._dataframe.iloc[index.row(), index.column()])

        return None

    def setData(self, index: QtCore.QModelIndex, value, role: int) -> bool:
        if role != QtCore.Qt.ItemDataRole.EditRole:
            return False

        if isinstance(value, list):
            value = ','.join(value)

        self.dataframe.iloc[index.row(), index.column()] = value
        self.dataChanged.emit(index, index,
                                [QtCore.Qt.ItemDataRole.DisplayRole, QtCore.Qt.ItemDataRole.EditRole])
        return True          
    
    def rowCount(self, index) -> int:
        if index == QtCore.QModelIndex():
            return len(self.dataframe)

        return 0

    def columnCount(self, index) -> int:
        if index == QtCore.QModelIndex():
            return len(self.dataframe.columns)

        return 0
    
    def headerData(self, section: int, orientation: QtCore.Qt.Orientation, role: QtCore.Qt.ItemDataRole):
        """Override method from QAbstractTableModel

        Return dataframe index as vertical header data and columns as horizontal header data.
        """
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            if orientation == QtCore.Qt.Orientation.Horizontal:
                return str(self._dataframe.columns[section])

            if orientation == QtCore.Qt.Orientation.Vertical:
                return str(self._dataframe.index[section])

        return None

    def filter(self, s: str):
        if self.primary_column_name == "":
            return
        
        df = pd.read_parquet(self.sourcefile.with_suffix('.parquet').as_posix(), filters=[(self.primary_column_name, '=', int(s))])
        self.beginResetModel()
        self._dataframe = df.copy()
        self.endResetModel()

    def refresh(self):
        df = pd.read_parquet(self.sourcefile.with_suffix('.parquet').as_posix())
        self.beginResetModel()
        self._dataframe = df.copy()
        self.endResetModel()

    @Slot(str, int)
    def onSetPrimaryIndex(self, name, idx):
        self.primary_column_name = name
        self.primary_column_index = idx

class IndexMenu(QtWidgets.QMenu):
    sigIndexSetAsPrimaryKey = Signal(str, int)

    def __init__(self, index_name = "", primary_name = "", primary_idx = -1, parent=None):
        super().__init__(parent)
        self._index_name = index_name
        self._primary_idx = primary_idx

        index_title = QtGui.QAction(index_name, self)
        index_title.setDisabled(True)
        self.addAction(index_title)

        primary = QtGui.QAction("make primary key", self)
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


class TagDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        tags: list = mconf.settings.value("tags", [], list)
        self.completer = QtWidgets.QCompleter(tags)
        self.completer.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)

        self.setWindowTitle("Tag Manager")

        vbox = QtWidgets.QVBoxLayout()
        self.setLayout(vbox)

        add_widget = QtWidgets.QWidget()
        add_widget_hbox = QtWidgets.QHBoxLayout()
        add_widget.setLayout(add_widget_hbox)

        self.tag_input = QtWidgets.QLineEdit()
        self.tag_input.setCompleter(self.completer)

        add_button = QtWidgets.QPushButton("Add", self)
        add_button.clicked.connect(self.addTag)
        add_widget_hbox.addWidget(self.tag_input)
        add_widget_hbox.addWidget(add_button)

        vbox.addWidget(add_widget)
        self.tag_list_model = QtCore.QStringListModel()
        self.tag_list = QtWidgets.QListView()
        self.tag_list.setModel(self.tag_list_model)
        vbox.addWidget(self.tag_list)
        remove_button = QtWidgets.QPushButton("Remove", self)
        vbox.addWidget(remove_button)

        buttons = (QtWidgets.QDialogButtonBox.StandardButton.Save | QtWidgets.QDialogButtonBox.StandardButton.Cancel)

        self.buttonBox = QtWidgets.QDialogButtonBox(buttons)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        vbox.addWidget(self.buttonBox)
    
    def addTag(self):
        tag = self.tag_input.text()

        if tag.strip() == "":
            return

        completer_list: list = self.completer.model().stringList()

        # Save tag to QSettings
        if tag not in completer_list:
            completer_list.append(tag)
            self.completer.model().setStringList(completer_list)
            mconf.settings.setValue("Tags", completer_list)

        # Add tag to the data tag list
        data_tags = self.tag_list_model.stringList()
        if tag not in data_tags:
            data_tags.append(tag)
            self.tag_list_model.setStringList(data_tags)


class TagModel(QtCore.QAbstractListModel):
    def __init__(self, data = [], parent=None):
        super().__init__(parent)
        self._data = data

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self._data)

    def data(self, index, role):
        if not index.isValid():
            return None

        if index.row() >= len(self._data):
            return None

        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            return self._data[index.row()]
        else:
            return None


class TagPane(QtWidgets.QListView):
    def __init__(self, parent=None):
        super().__init__(parent)
      

class DataView(QtWidgets.QTableView):
    sigOpenTagManager = Signal(QtCore.QModelIndex)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._table_name = ""

        # Context Menu
        self.context_menu = QtWidgets.QMenu(self)
        self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.contextMenuEvent)

        self.tag_action = QtGui.QAction(QtGui.QIcon(":tags"), "Manage Tag", self, triggered=self.onTagActionTriggered)
        self.show_indexmenu_action = QtGui.QAction("Show Index Menu", self, triggered=self.showIndexMenu)

    @property
    def table_name(self):
        return self._table_name
    
    @table_name.setter
    def table_name(self, s: str):
        self._table_name = s

    def contextMenuEvent(self, event: QtGui.QMouseEvent):
        """Creating a context menu"""
        self.context_menu.addAction(self.tag_action)
        self.context_menu.addAction(self.show_indexmenu_action)
        self.context_menu.exec(QtGui.QCursor().pos())

    def onTagActionTriggered(self):
        index = self.selectionModel().currentIndex()
        self.sigOpenTagManager.emit(index)

    def showIndexMenu(self):
        index = self.selectionModel().currentIndex()
        index_name = self.model().headerData(index.column(),
                                             QtCore.Qt.Orientation.Horizontal,
                                             QtCore.Qt.ItemDataRole.DisplayRole)
        menu = IndexMenu(index_name, self.model().primary_column_name,index.column(), self)
        menu.sigIndexSetAsPrimaryKey.connect(self.model().onSetPrimaryIndex)
        menu.popup(QtGui.QCursor().pos())


class DataViewer(QtWidgets.QWidget):
    def __init__(self, storefile: str, parent=None):
        super().__init__(parent)
        self.tagged = {}
        self.initUI(storefile)
        self.initDialogs()
        self.connectSignals()

    def initUI(self, storefile):
        self.setWindowTitle("DataViewer")
        self.setWindowFlags(QtCore.Qt.WindowType.Window)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose)

        self._storefile = storefile
        
        vbox = QtWidgets.QVBoxLayout(self)
        self.setLayout(vbox)

        # Menubar
        menubar = QtWidgets.QMenuBar(self)
        self.layout().setMenuBar(menubar)
        
        filemenu = QtWidgets.QMenu("File", self)
        filemenu.addAction(QtGui.QAction("Open file", self, triggered=lambda: self.selectFiles(filter="*.csv *.xlsx *.parquet")))

        viewmenu = QtWidgets.QMenu("View", self)
        viewmenu.addAction(QtGui.QAction("Cascade", self, triggered=self.setCascadeSubWindows))
        viewmenu.addAction(QtGui.QAction("Tile", self, triggered=self.setTileSubWindows))
        viewmenu.addAction(QtGui.QAction("Tabbed", self, triggered=self.setTabbedView))

        menubar.addMenu(filemenu)
        menubar.addMenu(viewmenu)

        # Toolbar
        toolbar = QtWidgets.QToolBar(self)
        toolbar.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonIconOnly)
        vbox.addWidget(toolbar)

        # Get info
        getInfoAction = QtGui.QAction(QtGui.QIcon(":information-2-line"), "Info", self, triggered=self.getInfo)
        toolbar.addAction(getInfoAction)

        # Sync Selection
        self.syncSelectionFilterAction = QtGui.QAction(QtGui.QIcon(":loop-right-line"),"Sync Selection", self)
        self.syncSelectionFilterAction.setCheckable(True)
        toolbar.addAction(self.syncSelectionFilterAction)

        # Reset Filter
        self.resetFiltersAction = QtGui.QAction(QtGui.QIcon(":filter-off-line"), "Reset filters", self)
        self.resetFiltersAction.triggered.connect(self.resetFilters)
        toolbar.addAction(self.resetFiltersAction)

        # MdiArea
        self.mdi = QtWidgets.QMdiArea()
        self.mdi.setTabsMovable(True)
        self.mdi.setTabsClosable(True)
    
        # LeftPane
        self.tag_model = TagModel()
        self.tag_pane = TagPane()
        self.tag_pane.setModel(self.tag_model)

        self.splitter = QtWidgets.QSplitter()
        self.splitter.addWidget(self.tag_pane)
        self.splitter.addWidget(self.mdi)
        vbox.addWidget(self.splitter)

        self.readDataStore()

    def initDialogs(self):
        self.tag_dialog: TagDialog = None

    def connectSignals(self):
        ...

    def setTabbedView(self):
        self.mdi.setViewMode(QtWidgets.QMdiArea.ViewMode.TabbedView)

    def setCascadeSubWindows(self):
        self.mdi.setViewMode(QtWidgets.QMdiArea.ViewMode.SubWindowView)
        self.mdi.cascadeSubWindows()
    
    def setTileSubWindows(self):
        self.mdi.setViewMode(QtWidgets.QMdiArea.ViewMode.SubWindowView)
        self.mdi.tileSubWindows()

    def createDataView(self, df: pd.DataFrame, sourcefile: Path):
        if df is not None:
            pandas_model = PandasModel(df, sourcefile)
            table = DataView()
            table.table_name = sourcefile.stem.upper()
            table.setModel(pandas_model)
            table.resizeColumnsToContents()
            table.setSortingEnabled(True)
            table.sigOpenTagManager.connect(self.onOpenTagManager)

            table.selectionModel().selectionChanged.connect(self.syncSelectionFilter)

            subwindow = self.mdi.addSubWindow(table)

            subwindow.setWindowTitle(table.table_name)
            subwindow.show()

    def selectFiles(self, dir=None, filter=None):
        files = QtWidgets.QFileDialog.getOpenFileNames(caption="Select files", directory=dir, filter=filter)

        if len(files[0]) > 0:
            self._sources = files[0]

            for file in self._sources:
                filepath = Path(file)

                for subwindow in self.mdi.subWindowList():
                    table_name = subwindow.widget().table_name
                    if table_name == filepath.stem.upper():
                        return

                parquetfile = filepath.with_suffix('.parquet')
                if parquetfile.exists():
                    filepath = parquetfile

                df = self.readFile(filepath)
                headers: list = df.columns.values.tolist()

                if not 'Tags' in headers:
                    headers.append('Tags')
                    # df = df.reindex(columns=headers)
                    df.insert(len(df.columns), 'Tags', None)

                if df is not None and filepath.suffix != '.parquet' and not filepath.with_suffix('.parquet').exists():
                    self.save2Parquet(df, filepath)

                self.createDataView(df, filepath)
    
    def readFile(self, filepath: Path) -> pd.DataFrame:
        """Read file (*.xlsx, *.csv, *.parquet) and return a pandas dataframe"""

        df = None

        if filepath.suffix == '.csv':
            codecs = ["utf-8", "latin-1"]
            seps = [",", ";"]
            i = 0
            j = 0
            reading = True
            while reading:
                try:
                    df = pd.read_csv(filepath, encoding=codecs[i], sep=seps[j])
                except UnicodeDecodeError:
                    i += 1
                except pd.errors.ParserError:
                    j += 1
                except Exception as e:
                    reading = False
                    break
                else:
                    reading = False
                    break
        elif filepath.suffix == '.xlsx':
            df = pd.read_excel(filepath)
        elif filepath.suffix == '.parquet':
            df = pd.read_parquet(filepath)
        return df
    
    def save2Parquet(self, df: pd.DataFrame, filepath: Path):
        """Save pandas dataframe to Apache Parquet file"""
        try:
            df.to_parquet(filepath.with_suffix('.parquet').as_posix())
        except Exception as e:
            return False
        else:
            return True
    
    def readDataStore(self):
        """Read JSON file"""
        self.jsonfile = QtCore.QFile(self._storefile)

        if not self.jsonfile.open(QtCore.QIODeviceBase.OpenModeFlag.ReadOnly):
            logger.error(f"Opening Error: {IOError(self.jsonfile.errorString())}")
            return
        
        file_bytes = self.jsonfile.readAll()
        self.jsonfile.close()

        json_error = QtCore.QJsonParseError()
        self.json_document = QtCore.QJsonDocument.fromJson(file_bytes, json_error)

        if self.json_document.isNull():
            logger.error(f"Parser Error: {json_error.errorString()}")
        
        self.datastore: dict = self.json_document.object()
        for key in self.datastore.keys():
            item: QtCore.QJsonValue = self.datastore.get(key)
            if item.isArray():
                self.datastore[key] = item.toArray()

    def writeDataStore(self):
        """Write JSON file"""
        self.json_document.setObject(self.datastore)
        jsonbytes = self.json_document.toJson(QtCore.QJsonDocument.JsonFormat.Indented)

        if self.jsonfile.open(QtCore.QIODeviceBase.OpenModeFlag.WriteOnly | QtCore.QIODeviceBase.OpenModeFlag.Text | QtCore.QIODeviceBase.OpenModeFlag.Truncate):
            textstream = QtCore.QTextStream(self.jsonfile)
            textstream.setEncoding(QtCore.QStringConverter.Encoding.Utf8)
            textstream << jsonbytes
            self.jsonfile.close()
        else:
            logger.error("Opening file failed")
            return

    @Slot()
    def getInfo(self):
        active_subwindow = self.mdi.activeSubWindow()

        if active_subwindow is None:
            return

        buffer = io.StringIO()
        active_subwindow.widget().model().dataframe.info(buf=buffer)
        s = buffer.getvalue()

        info_text = QtWidgets.QLabel(self)
        info_text.setTextFormat(QtCore.Qt.TextFormat.PlainText)
        info_text.setFont(QtGui.QFont("Courier New", 10))
        info_text.setAlignment(QtCore.Qt.AlignmentFlag.AlignJustify)
        info_text.setText(s.expandtabs(4))

        info_widget = QtWidgets.QWidget(self)
        info_widget.setWindowTitle("DataFrame Info")
        info_widget.setWindowFlags(QtCore.Qt.WindowType.Window | QtCore.Qt.WindowType.MSWindowsFixedSizeDialogHint)
        vbox = QtWidgets.QVBoxLayout()
        info_widget.setLayout(vbox)
        vbox.addWidget(info_text)
        info_widget.show()

    @Slot(QtCore.QItemSelection, QtCore.QItemSelection)
    def syncSelectionFilter(self, selected: QtCore.QItemSelection, deselected: QtCore.QItemSelection):
        if self.syncSelectionFilterAction.isChecked():
            indexes = selected.indexes()
            primary_column_index = self.mdi.activeSubWindow().widget().model().primary_column_index

            if primary_column_index < 0:
                return

            index: QtCore.QModelIndex = indexes[primary_column_index]
            cid = index.sibling(index.row(), 0).data(QtCore.Qt.ItemDataRole.DisplayRole)

            for subwindow in self.mdi.subWindowList():
                if subwindow == self.mdi.activeSubWindow():
                    continue

                subwindow.widget().model().filter(cid)
                subwindow.widget().resizeColumnsToContents()

    @Slot()
    def resetFilters(self):
        for subwindow in self.mdi.subWindowList():
            subwindow.widget().model().refresh()

    @Slot(QtCore.QModelIndex)
    def onOpenTagManager(self, index: QtCore.QModelIndex):
        if self.tag_dialog is None:
            self.tag_dialog = TagDialog()

        table: DataView = self.mdi.activeSubWindow().widget()

        tags: str = index.sibling(index.row(), table.model().columnCount(QtCore.QModelIndex())-1).data(QtCore.Qt.ItemDataRole.DisplayRole)
        case_id: str = index.sibling(index.row(), 0).data(QtCore.Qt.ItemDataRole.DisplayRole)

        if tags == 'None':
            self.tag_dialog.tag_list.model().setStringList([])
        else:
            self.tag_dialog.tag_list.model().setStringList(tags.split(","))

        if self.tag_dialog.exec():
            tag_list = self.tag_dialog.tag_list.model().stringList()

            if len(tag_list) > 0:
                table.model().setData(index.sibling(index.row(), table.model().columnCount(QtCore.QModelIndex())-1),
                                      tag_list,
                                      QtCore.Qt.ItemDataRole.EditRole)   

                for tag in tag_list:
                    if tag in self.datastore:
                        if case_id not in self.datastore[tag]:
                            self.datastore[tag].append(case_id)
                    else:
                        self.datastore.update({tag: [case_id]})
                
                self.writeDataStore()
    
    def closeEvent(self, a0):
        """Save dataframe to Parquet file upon closing the dataviewer"""
        for subwindow in self.mdi.subWindowList():
            model: PandasModel = subwindow.widget().model()
            self.save2Parquet(model.dataframe, model.sourcefile)
        return super().closeEvent(a0)