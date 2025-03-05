import io
import pandas as pd
from pathlib import Path
from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtCore import pyqtSlot as Slot

class PandasModel(QtCore.QAbstractTableModel):
    def __init__(self, dataframe: pd.DataFrame, sourcefile: Path, parent=None):
        super(PandasModel, self).__init__(parent)
        self.dataframe = dataframe
        self.sourcefile = sourcefile

    @property
    def dataframe(self):
        return self._dataframe
    
    @dataframe.setter
    def dataframe(self, df: pd.DataFrame):
        self._dataframe = df
    
    def data(self, index: QtCore.QModelIndex, role: QtCore.Qt.ItemDataRole):
        if not index.isValid():
            return None

        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            return str(self._dataframe.iloc[index.row(), index.column()])

        return None
    
    def rowCount(self, index) -> int:
        if index == QtCore.QModelIndex():
            return len(self._dataframe)

        return 0

    def columnCount(self, index) -> int:
        if index == QtCore.QModelIndex():
            return len(self._dataframe.columns)

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
        df = pd.read_parquet(self.sourcefile.with_suffix('.parquet').as_posix(), filters=[('CASE_ID', '=', int(s))])
        self.beginResetModel()
        self._dataframe = df.copy()
        self.endResetModel()

    def refresh(self):
        df = pd.read_parquet(self.sourcefile.with_suffix('.parquet').as_posix())
        self.beginResetModel()
        self._dataframe = df.copy()
        self.endResetModel()

    
class DataView(QtWidgets.QTableView):
    def __init__(self, parent=None):
        super().__init__(parent)

class DataViewer(QtWidgets.QWidget):
    def __init__(self, storefile: str, parent=None):
        super().__init__(parent)
        self.initUI(storefile)

    def initUI(self, storefile):
        self.setWindowTitle("DataViewer")
        self.setWindowFlags(QtCore.Qt.WindowType.Window)

        self._storefile = storefile
        
        vbox = QtWidgets.QVBoxLayout(self)
        self.setLayout(vbox)

        # Menubar
        menubar = QtWidgets.QMenuBar(self)
        vbox.addWidget(menubar)
        
        filemenu = QtWidgets.QMenu("File", self)
        filemenu.addAction(QtGui.QAction("Open file", self, triggered=lambda: self.selectFiles(filter="*.csv *.xlsx")))

        viewmenu = QtWidgets.QMenu("View", self)
        viewmenu.addAction(QtGui.QAction("Cascade", self, triggered=self.setCascadeSubWindows))
        viewmenu.addAction(QtGui.QAction("Tile", self, triggered=self.setTileSubWindows))
        viewmenu.addAction(QtGui.QAction("Tabbed", self, triggered=self.setTabbedView))

        menubar.addMenu(filemenu)
        menubar.addMenu(viewmenu)

        # Toolbar
        toolbar = QtWidgets.QToolBar(self)
        toolbar.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonIconOnly)
        toolbar.setIconSize(QtCore.QSize(32, 32))
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
        
        vbox.addWidget(self.mdi)

        self.readDataStore()

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
            table.setModel(pandas_model)
            table.resizeColumnsToContents()
            table.setSortingEnabled(True)

            table.selectionModel().selectionChanged.connect(self.syncSelectionFilter)

            subwindow = self.mdi.addSubWindow(table)

            subwindow.setWindowTitle(sourcefile.stem.upper())
            subwindow.show()

    def selectFiles(self, dir=None, filter=None):
        files = QtWidgets.QFileDialog.getOpenFileNames(caption="Select files", directory=dir, filter=filter)

        if len(files[0]) > 0:
            self._sources = files[0]

            for file in self._sources:
                filepath = Path(file)
                df = self.readFile(filepath)

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
            print(f"Opening Error: {IOError(self.jsonfile.errorString())}")
            return
        
        file_bytes = self.jsonfile.readAll()
        self.jsonfile.close()

        json_error = QtCore.QJsonParseError()
        self.json_document = QtCore.QJsonDocument.fromJson(file_bytes, json_error)

        if json_error.error != QtCore.QJsonParseError.ParseError.NoError:
            print(f"Parser Error: {json_error.errorString()}")
        
        self.json_object: dict = self.json_document.object()

    def writeDataStore(self):
        """Write JSON file"""
        self.json_document.setObject(self.json_object)
        jsonbytes = self.json_document.toJson(QtCore.QJsonDocument.JsonFormat.Indented)

        if self.jsonfile.open(QtCore.QIODeviceBase.OpenModeFlag.WriteOnly | QtCore.QIODeviceBase.OpenModeFlag.Text | QtCore.QIODeviceBase.OpenModeFlag.Truncate):
            textstream = QtCore.QTextStream(self.jsonfile)
            textstream.setEncoding(QtCore.QStringConverter.Encoding.Utf8)
            textstream << jsonbytes
            self.jsonfile.close()
        else:
            print("file open failed")
            return

    @Slot()
    def getInfo(self):
        active_subwindow = self.mdi.activeSubWindow()

        if active_subwindow is None:
            return

        buffer = io.StringIO()
        active_subwindow.widget().model().dataframe.info(buf=buffer)
        s = buffer.getvalue()
        msg = QtWidgets.QMessageBox(self)
        msg.setText(s)
        msg.show()


    @Slot(QtCore.QItemSelection, QtCore.QItemSelection)
    def syncSelectionFilter(self, selected: QtCore.QItemSelection, deselected: QtCore.QItemSelection):
        if self.syncSelectionFilterAction.isChecked():
            indexes = selected.indexes()
            index: QtCore.QModelIndex = indexes[0]
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
        

