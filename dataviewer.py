from pathlib import Path
from PyQt6 import QtWidgets, QtCore
from layout_colorwidget import Color
import pandas as pd

class PandasModel(QtCore.QAbstractTableModel):
    def __init__(self, dataframe: pd.DataFrame, parent=None):
        super(PandasModel, self).__init__(parent)
        self._dataframe = dataframe
    
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
    
    def headerData(
        self, section: int, orientation: QtCore.Qt.Orientation, role: QtCore.Qt.ItemDataRole):
        """Override method from QAbstractTableModel

        Return dataframe index as vertical header data and columns as horizontal header data.
        """
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            if orientation == QtCore.Qt.Orientation.Horizontal:
                return str(self._dataframe.columns[section])

            if orientation == QtCore.Qt.Orientation.Vertical:
                return str(self._dataframe.index[section])

        return None

class DataViewer(QtWidgets.QMdiArea):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._sources: list[str] = []
 
        self.tileSubWindows()


    def loadData(self, df: pd.DataFrame):
 
        if df is not None:
            _model = PandasModel(df)
            _table = QtWidgets.QTableView()
            _table.setModel(_model)

            subwindow = self.addSubWindow(_table)

    def setSubwindowsTitle(self):
        for subwindow in self.subWindowList(QtWidgets.QMdiArea.WindowOrder.CreationOrder):
            for file in self._sources:
                subwindow.setWindowTitle(Path(file).stem)

    def selectFiles(self, dir=None, filter=None):
        files = QtWidgets.QFileDialog.getOpenFileNames(caption="Select files", directory=dir, filter=filter)

        if len(files[0]) > 0:
            self._sources = files[0]

        for file in self._sources:
            df = self.readFile(file)
            self.loadData(df)
    
    def readFile(self, file: str) -> pd.DataFrame | None:
        p = Path(file)
        df = None
        codecs = ["utf-8", "latin-1"]

        if p.suffix == '.csv':
            for codec in codecs:
                try:
                    df = pd.read_csv(p, encoding=codec)
                except UnicodeDecodeError:
                    continue
                else:
                    break
        elif p.suffix == '.xlsx':
            df = pd.read_excel(p)

        return df
