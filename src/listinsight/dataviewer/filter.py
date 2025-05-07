from dataclasses import dataclass, asdict
from qtpy import QtCore, QtWidgets, QtGui, Slot, Signal


@dataclass
class Filter:
    attr: str
    oper: str
    value: str
    enabled: bool = False
    failed: bool = False
    expr: str = ""       
    
    def to_dict(self):
        return asdict(self)


class FilterModel(QtCore.QAbstractListModel):
    sigToggleFilter = Signal(int)

    def __init__(self, attrs: dict = {}):
        super().__init__()
        self._filters: list[Filter] = []
        self._attrs = attrs

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
        
        filter: Filter = self._filters[index.row()]

        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            return f"{filter.attr} {filter.oper} {filter.value}"

        if role == QtCore.Qt.ItemDataRole.CheckStateRole:
            if filter.failed:
                return None

            if filter.enabled:
                return QtCore.Qt.CheckState.Checked
            else:
                return QtCore.Qt.CheckState.Unchecked
        
        if role == QtCore.Qt.ItemDataRole.DecorationRole and filter.failed:
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

    def addFilter(self, filter):
        new_index = len(self._filters)
        self.beginInsertRows(QtCore.QModelIndex(), new_index, new_index)
        self._filters.append(filter)
        self.endInsertRows()

    def removeFilter(self, position, rows, parent=QtCore.QModelIndex()):
        self.beginRemoveRows(parent, position, position + rows - 1)
        for _ in range(rows):
            del self._filters[position]
        self.endRemoveRows()
        return True
    
class FilterDialog(QtWidgets.QDialog):
    def __init__(self, attrs: dict = {}, parent = None):
        super().__init__(parent)
        self.setWindowTitle("Create filter expression")
        self.attrs = attrs

        formlayout = QtWidgets.QFormLayout()
        self.setLayout(formlayout)

        self.attrs_box = QtWidgets.QComboBox()
        for attr_name, dtype in self.attrs.items():
            self.attrs_box.addItem(attr_name, dtype)

        formlayout.addRow("Attribut", self.attrs_box)

        operators = ["==", "!=", ">", "<", ">=", "<=", "in", "contains", "startswith", "endswith"]

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

    def getFilter(self) -> Filter:
        filter = Filter(self.attrs_box.currentText(),
                        self.operator.currentText(),
                        self.value.text())
        filter.expr = self.validate()
        return filter
    
    def validate(self) -> str:
        attr = f'`{self.attrs_box.currentText()}`'
        oper = self.operator.currentText()
        value = self.value.text()

        if self.attrs_box.currentData(QtCore.Qt.ItemDataRole.UserRole) == 'int64':
            if oper in ["contains", "endswith", "startswith"]:
                expr = f'{attr}.astype("str").str.{oper}("{value}", na=False)'
            else:
                expr = f'{attr} {oper} {value}'
        else:
            if oper == "in":
                value = [x.strip() for x in value.split(',')]
                expr = f"{attr} {oper} {value}"
            elif oper in ["contains", "endswith", "startswith"]:
                expr = f'{attr}.str.{oper}("{value}", na=False)'
            else:
                expr = f'{attr} {oper} "{value}"'
        
        return expr

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

        vbox = QtWidgets.QVBoxLayout()
        self.setLayout(vbox)
        vbox.addLayout(button_layout)
        vbox.addWidget(self.filter_list)

        add_filter_btn.clicked.connect(self.addFilter)
        edit_filter_btn.clicked.connect(self.editFilter)
        delete_filter_btn.clicked.connect(self.removeFilter)

    def createModel(self, dataset_id: str, filters: list[Filter], attrs: dict = {}):
        model = FilterModel(attrs)
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
    def removeFilter(self):
        if self.filter_list.selectionModel() is None:
            return
        
        index = self.filter_list.selectionModel().currentIndex()

        if not index.isValid():
            return

        model: FilterModel = self.filter_list.model()
        model.removeFilter(index.row(), 1)
  
    @Slot()
    def addFilter(self):
        model: FilterModel = self.filter_list.model()
        if model is None:
            return

        filter_dlg = FilterDialog(model._attrs, self)
        if filter_dlg.exec():
            filter = filter_dlg.getFilter()
            model.addFilter(filter)

    @Slot()
    def editFilter(self):
        if self.filter_list.selectionModel() is None:
            return
        
        index = self.filter_list.selectionModel().currentIndex()
        model: FilterModel = self.filter_list.model()

        filter: Filter = model.filter(index)
        if filter is None:
            return

        filter_dlg = FilterDialog(model._attrs, self)
        filter_dlg.attrs = model._attrs
        filter_dlg.attrs_box.setCurrentText(filter.attr)
        filter_dlg.operator.setCurrentText(filter.oper)
        filter_dlg.value.setText(filter.value)
        if filter_dlg.exec():
            filter.attr = filter_dlg.attrs_box.currentText()
            filter.oper = filter_dlg.operator.currentText()
            filter.value = filter_dlg.value.text()
            filter.expr = filter_dlg.validate()
            print(filter.expr)



        