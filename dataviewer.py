import pandas as pd
import json
from pathlib import Path
from PyQt6 import QtWidgets, QtCore, QtGui

class PandasModel(QtCore.QAbstractTableModel):
    def __init__(self, dataframe: pd.DataFrame, parent=None):
        super(PandasModel, self).__init__(parent)
        self.dataframe = dataframe

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
    
class DataView(QtWidgets.QTableView):
    def __init__(self, parent=None):
        super().__init__(parent)

class DataViewer(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        vbox = QtWidgets.QVBoxLayout(self)
        self.setLayout(vbox)

        self.toolbar = QtWidgets.QToolBar(self)
        self.toolbar.addAction(QtGui.QAction(QtGui.QIcon(':bold'), "Load", self, triggered=lambda: self.selectFiles()))
        self.toolbar.addAction(QtGui.QAction(QtGui.QIcon(), "tabbed", self , triggered= self.setTabbedView))
        self.toolbar.addAction(QtGui.QAction(QtGui.QIcon(), "subWindowView", self, triggered= self.setSubWindowView))
        self.toolbar.addAction(QtGui.QAction(QtGui.QIcon(), "cascade", self,  triggered=self.setCascadeSubWindows))
        self.toolbar.addAction(QtGui.QAction(QtGui.QIcon(), "tile", self,  triggered=self.setTileSubWindows))
        self.mdi = QtWidgets.QMdiArea()
        
        vbox.addWidget(self.toolbar)
        vbox.addWidget(self.mdi)

        self.readDataStore()

    def setTabbedView(self):
        self.mdi.setViewMode(QtWidgets.QMdiArea.ViewMode.TabbedView)

    def setSubWindowView(self):
        self.mdi.setViewMode(QtWidgets.QMdiArea.ViewMode.SubWindowView)

    def setCascadeSubWindows(self):
        self.mdi.cascadeSubWindows()
    
    def setTileSubWindows(self):
        self.mdi.tileSubWindows()

    def loadData(self, file: str):
        df:  pd.DataFrame = self.readFile(file)
 
        if df is not None:
            pandas_model = PandasModel(df)
            table = DataView()
            table.setModel(pandas_model)
            table.resizeColumnsToContents()
            table.setSortingEnabled(True)

            subwindow = self.mdi.addSubWindow(table)

            subwindow.setWindowTitle(Path(file).stem)
            subwindow.show()

    def selectFiles(self, dir=None, filter=None):
        files = QtWidgets.QFileDialog.getOpenFileNames(caption="Select files", directory=dir, filter=filter)

        if len(files[0]) > 0:
            self._sources = files[0]

            for file in self._sources:
                self.loadData(file)
    
    def readFile(self, file: str) -> pd.DataFrame | None:
        p = Path(file)
        df = None

        if p.suffix == '.csv':
            codecs = ["utf-8", "latin-1"]
            seps = [",", ";"]
            i = 0
            j = 0
            reading = True
            while reading:
                try:
                    df = pd.read_csv(p, encoding=codecs[i], sep=seps[j])
                except UnicodeDecodeError:
                    i += 1
                except pd.errors.ParserError:
                    j += 1
                except Exception as e:
                    reading = False
                    break
                else:
                    break
        elif p.suffix == '.xlsx':
            df = pd.read_excel(p)
        elif p.suffix == '.parquet':
            df = pd.read_parquet(p)

        if df is not None and p.suffix != '.parquet':
            df.to_parquet(p.with_suffix('.parquet').as_posix(), index=False)

        return df
    
    def saveFile(self):
        ...
    
    def readDataStore(self):
        self.jsonfile = QtCore.QFile("datastore.json")
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

