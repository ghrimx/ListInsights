from dataclasses import dataclass, asdict
from qtpy import QtCore, QtWidgets, QtGui, Slot, Signal


@dataclass
class Filter:
    attr: str
    oper: str
    value: str
    enabled: bool = False
    failed: bool = False

    def expr(cls):
        return f"`{cls.attr}` {cls.oper} '{cls.value}'"
    
    def to_dict(self):
        return asdict(self)


class FilterModel(QtCore.QAbstractListModel):
    sigToggleFilter = Signal(int)

    def __init__(self):
        super().__init__()
        self._filters: list[Filter] = []

    def flags(self, index):
        return (QtCore.Qt.ItemFlag.ItemIsEnabled |
                QtCore.Qt.ItemFlag.ItemIsSelectable |
                QtCore.Qt.ItemFlag.ItemIsUserCheckable)
    
    def filter(self, index: QtCore.QModelIndex) -> Filter:
        if not index.isValid():
            return None

        row = index.row()
        return self._filters[row]
    
    def data(self, index: QtCore.QModelIndex, role=QtCore.Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        
        item: Filter = self._filters[index.row()]

        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            return item.expr()

        if role == QtCore.Qt.ItemDataRole.CheckStateRole:
            if item.failed:
                return None

            if item.enabled:
                return QtCore.Qt.CheckState.Checked
            else:
                return QtCore.Qt.CheckState.Unchecked
        
        if role == QtCore.Qt.ItemDataRole.DecorationRole and item.failed:
            return QtGui.QIcon(":alert-fill-red")
    
    def rowCount(self, parent = QtCore.QModelIndex()):
        return len(self._filters)
    
    def setData(self, index: QtCore.QModelIndex, value: Filter, role=QtCore.Qt.ItemDataRole):
        row = index.row()

        if not index.isValid():
            return False
                
        if role == QtCore.Qt.ItemDataRole.CheckStateRole:
            self.sigToggleFilter.emit(row)
            return True

        if role == QtCore.Qt.ItemDataRole.EditRole:
            return True

        return False
    
    def load(self, filters: list[Filter]):
        self.beginResetModel()
        self._filters = filters
        self.endResetModel()
    
class FilterDialog(QtWidgets.QDialog):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.setWindowTitle("Create filter expression")

        formlayout = QtWidgets.QFormLayout()
        self.setLayout(formlayout)

        self.attr = QtWidgets.QLineEdit()
        formlayout.addRow("Attribut", self.attr)

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
        return f"`{self.attr.text()}` {self.operator.currentText()} {self.value.text()}"


class FilterPane(QtWidgets.QWidget):
    sigAddFilter = Signal(str)
    sigToggleFilter = Signal(int)

    def __init__(self, parent = None):
        super().__init__(parent)

        button_layout = QtWidgets.QHBoxLayout()
        add_filter_btn = QtWidgets.QPushButton(QtGui.QIcon(":add-box"), "Add filter")
        button_layout.addWidget(add_filter_btn)
        delete_filter_btn = QtWidgets.QPushButton(QtGui.QIcon(":delete-bin2"), "Delete filter")
        button_layout.addWidget(delete_filter_btn)
        edit_filter_btn = QtWidgets.QPushButton(QtGui.QIcon(":pencil"), "Edit filter")
        button_layout.addWidget(edit_filter_btn)

        self.filter_list = QtWidgets.QListView()
        self.filter_models: dict[FilterModel] = {} # {dataset_id : model}
        # self.filter_model = FilterModel()
        # self.filter_list.setModel(self.filter_model)

        vbox = QtWidgets.QVBoxLayout()
        self.setLayout(vbox)
        vbox.addLayout(button_layout)
        vbox.addWidget(self.filter_list)

        add_filter_btn.clicked.connect(self.addFilter)
        edit_filter_btn.clicked.connect(self.editFilter)

    def createModel(self, dataset_id: str, filters: list[Filter]):
        model = FilterModel()
        model.load(filters)
        self.filter_models[dataset_id] = model
        self.filter_list.setModel(model)

        model.sigToggleFilter.connect(self.sigToggleFilter)
    
    @Slot(str)
    def setCurrentModel(self, dataset_id):
        model = self.filter_models.get(dataset_id)
        
        if model is None:
            return
        
        self.filter_list.setModel(model)
  
    @Slot()
    def addFilter(self):
        filter_dlg = FilterDialog(self)
        if filter_dlg.exec():
            filter_exp = filter_dlg.get_filter()
            print(filter_exp)

    @Slot()
    def editFilter(self):
        index = self.filter_list.selectionModel().currentIndex()
        model: FilterModel = self.filter_list.model()
        filter: Filter = model.filter(index)
        filter_dlg = FilterDialog(self)
        filter_dlg.attr.setText(filter.attr)
        filter_dlg.operator.setCurrentText(filter.oper)
        filter_dlg.value.setText(filter.value)
        if filter_dlg.exec():
            filter.attr = filter_dlg.attr.text()
            filter.oper = filter_dlg.operator.currentText()
            filter.value = filter_dlg.value.text()



        