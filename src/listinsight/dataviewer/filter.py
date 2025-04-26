from dataclasses import dataclass
from qtpy import QtCore, QtWidgets, QtGui, Slot, Signal


@dataclass
class Filter:
    expr: str
    enabled: bool
    failed: bool


class FilterModel(QtCore.QAbstractListModel):
    def __init__(self, filters: list[Filter] = []):
        super().__init__()
        self._filters: list[Filter] = filters
    
    def data(self, index, role=QtCore.Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        
        item: Filter = self._filters[index.row()]

        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            return item.expr

        if role == QtCore.Qt.ItemDataRole.CheckStateRole:
            if item.failed:
                return None

            if item.enabled:
                return QtCore.Qt.CheckState.Checked
            else:
                return QtCore.Qt.CheckState.Unchecked
        
        if role == QtCore.Qt.ItemDataRole.DecorationRole and item.failed:
            return QtGui.QIcon("")
    
    def rowCount(self, parent = QtCore.QModelIndex()):
        return len(self._filters)
    
    def setData(self, index: QtCore.QModelIndex, value: Filter, role=QtCore.Qt.ItemDataRole):
        if not index.isValid():
            return None
        
        if not role == QtCore.Qt.ItemDataRole.EditRole:
            return
        
        if role == QtCore.Qt.ItemDataRole.CheckStateRole:
            return True

        if role == QtCore.Qt.ItemDataRole.EditRole:
            return True

        return False
    
class FilterDialog(QtWidgets.QDialog):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.setWindowTitle("Create filter expression")

        formlayout = QtWidgets.QFormLayout()
        self.setLayout(formlayout)

        self.field = QtWidgets.QLineEdit()
        formlayout.addRow("Field", self.field)

        operators = ["==", "!=", ">", "<", ">=", "<=", "in", "str.contains()"]

        self.operator = QtWidgets.QComboBox()
        for op in operators:
            self.operator.addItem(op)
        formlayout.addRow("Operator", self.operator)

        self.value = QtWidgets.QLineEdit()
        formlayout.addRow("Value", self.value)

        buttons = (QtWidgets.QDialogButtonBox.StandardButton.Save | QtWidgets.QDialogButtonBox.StandardButton.Cancel)

        self.buttonBox = QtWidgets.QDialogButtonBox(buttons)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        formlayout.addWidget(self.buttonBox)

    def get_filter(self):
        return f"`{self.field.text()}` {self.operator.currentText()} {self.value.text()}"


class FilterPane(QtWidgets.QWidget):
    sigAddFilter = Signal(str)

    def __init__(self, parent = None):
        super().__init__(parent)

        button_layout = QtWidgets.QHBoxLayout()
        add_filter_btn = QtWidgets.QPushButton(QtGui.QIcon(":add-box"), "Add filter")
        button_layout.addWidget(add_filter_btn)
        delete_filter_btn = QtWidgets.QPushButton(QtGui.QIcon(":delete-bin2"), "delete filter")
        button_layout.addWidget(delete_filter_btn)

        self.filter_list = QtWidgets.QListView()
        self.filter_model = FilterModel()
        self.filter_list.setModel(self.filter_model)

        vbox = QtWidgets.QVBoxLayout()
        self.setLayout(vbox)
        vbox.addLayout(button_layout)
        vbox.addWidget(self.filter_list)

        add_filter_btn.clicked.connect(self.addFilter)

        

    @Slot()
    def addFilter(self):
        filter_dlg = FilterDialog(self)
        if filter_dlg.exec():
            filter_exp = filter_dlg.get_filter()
            print(filter_exp)

        