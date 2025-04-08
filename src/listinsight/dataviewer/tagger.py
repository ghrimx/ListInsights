import logging
from qtpy import QtCore, QtWidgets, Signal, Slot
from typing import Any
from utilities import config as mconf

logger = logging.getLogger(__name__)


class TreeItem:
    """A Json item corresponding to a line in QTreeView"""

    def __init__(self, parent: "TreeItem" = None):
        self._parent = parent
        self._value = ""
        self._value_type = None
        self._children = []

    def appendChild(self, item: "TreeItem"):
        """Add item as a child"""
        self._children.append(item)

    def child(self, row: int) -> "TreeItem":
        """Return the child of the current item from the given row"""
        return self._children[row]

    def parent(self) -> "TreeItem":
        """Return the parent of the current item"""
        return self._parent

    def childCount(self) -> int:
        """Return the number of children of the current item"""
        return len(self._children)

    def row(self) -> int:
        """Return the row where the current item occupies in the parent"""
        return self._parent._children.index(self) if self._parent else 0
    
    @property
    def value(self) -> str:
        """Return the value name of the current item"""
        return self._value

    @value.setter
    def value(self, value: str):
        """Set value name of the current item"""
        self._value = value

    @property
    def value_type(self):
        """Return the python type of the item's value."""
        return self._value_type

    @value_type.setter
    def value_type(self, value):
        """Set the python type of the item's value."""
        self._value_type = value

    @classmethod
    def load(
        cls, value: list | dict, parent: "TreeItem" = None, sort=True) -> "TreeItem":

        rootItem = TreeItem(parent)

        if isinstance(value, dict):
            items = sorted(value.items()) if sort else value.items()

            for key, value in items:
                child = cls.load(value, rootItem)
                child.value = key
                child.value_type = type(value)
                rootItem.appendChild(child)

        elif isinstance(value, list):
            for index, value in enumerate(value):
                child = cls.load(value, rootItem)
                child.value_type = type(value)
                rootItem.appendChild(child)

        else:
            rootItem.value = value
            rootItem.value_type = type(value)

        return rootItem


class TagModel(QtCore.QAbstractItemModel):
    """ An editable model of Json data """
  
    def __init__(self, parent: QtCore.QObject = None):
        super().__init__(parent)
        self._rootItem = TreeItem()
        self._headers = ["Name"]

    def clear(self):
        """ Clear data from the model """
        self.load({})

    def load(self, document: dict):
        """Load model from a nested dictionary returned by json.loads()

        Arguments:
            document (dict): JSON-compatible dictionary
        """

        assert isinstance(
            document, (dict, list, tuple)
        ), "`document` must be of dict, list or tuple, " f"not {type(document)}"

        self.beginResetModel()

        self._rootItem = TreeItem.load(document)
        self._rootItem.value_type = type(document)

        self.endResetModel()

        return True

    def data(self, index: QtCore.QModelIndex, role: QtCore.Qt.ItemDataRole):
        """Override from QAbstractItemModel

        Return data from a json item according index and role

        """
        if not index.isValid():
            return None

        if role != QtCore.Qt.ItemDataRole.DisplayRole and role != QtCore.Qt.ItemDataRole.EditRole:
            return None
        
        item: TreeItem = index.internalPointer()
        return item.value

    def setData(self, index: QtCore.QModelIndex, value: Any, role: QtCore.Qt.ItemDataRole):
        """Override from QAbstractItemModel

        Set json item according index and role

        Args:
            index (QtCore.QModelIndex)
            value (Any)
            role (QtCore.Qt.ItemDataRole)

        """
        if role == QtCore.Qt.ItemDataRole.EditRole:
            item: TreeItem = index.internalPointer()
            item.value = str(value)

            self.dataChanged.emit(index, index, [QtCore.Qt.ItemDataRole.EditRole])

            return True

        return False

    def headerData(self, section: int, orientation: QtCore.Qt.Orientation, role: QtCore.Qt.ItemDataRole):
        """Override from QAbstractItemModel

        For the JsonModel, it returns only data for columns (orientation = Horizontal)

        """
        if role != QtCore.Qt.ItemDataRole.DisplayRole:
            return None

        if orientation == QtCore.Qt.Orientation.Horizontal:
            return self._headers[section]

    def index(self, row: int, column: int, parent=QtCore.QModelIndex()) -> QtCore.QModelIndex:
        """Override from QAbstractItemModel

        Return index according row, column and parent

        """
        if not self.hasIndex(row, column, parent):
            return QtCore.QModelIndex()

        if not parent.isValid():
            parentItem = self._rootItem
        else:
            parentItem = parent.internalPointer()

        childItem = parentItem.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QtCore.QModelIndex()

    def parent(self, index: QtCore.QModelIndex) -> QtCore.QModelIndex:
        """Override from QAbstractItemModel

        Return parent index of index

        """

        if not index.isValid():
            return QtCore.QModelIndex()

        childItem: TreeItem = index.internalPointer()
        parentItem = childItem.parent()

        if parentItem == self._rootItem:
            return QtCore.QModelIndex()

        return self.createIndex(parentItem.row(), 0, parentItem)

    def rowCount(self, parent=QtCore.QModelIndex()) -> int:
        """Override from QAbstractItemModel

        Return row count from parent index
        """
        if parent.column() > 0:
            return 0

        if not parent.isValid():
            parentItem = self._rootItem
        else:
            parentItem = parent.internalPointer()

        return parentItem.childCount()

    def columnCount(self, parent=QtCore.QModelIndex()) -> int:
        """Override from QAbstractItemModel

        Return column number. For the model, it always return 2 columns
        """
        return 1

    def flags(self, index: QtCore.QModelIndex) -> QtCore.Qt.ItemFlag:
        """Override from QAbstractItemModel

        Return flags of index
        """
        if not index.isValid():
            return QtCore.Qt.ItemFlag.NoItemFlags

        return QtCore.Qt.ItemFlag.ItemIsEditable | QtCore.QAbstractItemModel.flags(self, index)

    def to_json(self, item=None):

        if item is None:
            item = self._rootItem

        nchild = item.childCount()

        if item.value_type is dict:
            document = {}
            for i in range(nchild):
                ch = item.child(i)
                document[ch.value] = self.to_json(ch)
            return document

        elif item.value_type == list:
            document = []
            for i in range(nchild):
                ch = item.child(i)
                document.append(self.to_json(ch))
            return document

        else:
            return item.value
        
    def append2Tag(self, values: list, parent_item: TreeItem, parent_index: QtCore.QModelIndex):
        self.beginInsertRows(parent_index, parent_item.childCount(), parent_item.childCount() + len(values) - 1)
        for value in values:
            child_item = TreeItem(parent_item)
            child_item.value = value
            child_item.value_type = None
            parent_item.appendChild(child_item)
        self.endInsertRows()
        
    def addNewTag(self, values: list, tagname: str):
        new_tag = TreeItem(self._rootItem)
        new_tag.value = tagname
        new_tag.value_type = type([])
        self.beginInsertRows(QtCore.QModelIndex(), self._rootItem.childCount(), self._rootItem.childCount() + 1)
        self._rootItem.appendChild(new_tag)
        self.endInsertRows()
        
        index = self.index(self._rootItem.childCount(), 0)
        self.append2Tag(values, new_tag, index)

    @Slot(list, str)
    def add2Tag(self, values: list, tagname: str):
        nchild = self._rootItem.childCount()

        for i in range(nchild):
            ch = self._rootItem.child(i)
            if tagname == ch.value:
                self.append2Tag(values, ch, self.index(i, 0))
                return
                 
        self.addNewTag(values, tagname)


class TagDialog(QtWidgets.QDialog):
    sigAdd2tag = Signal(str)
    sigRemoveTag = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        tags: list = mconf.settings.value("tags", [], list)
        self.completer = QtWidgets.QCompleter(tags)
        self.completer.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)

        self.setWindowTitle("Tag Manager")

        vbox = QtWidgets.QVBoxLayout()
        self.setLayout(vbox)

        # Buttons widgets
        add_widget_hbox = QtWidgets.QHBoxLayout()
        self.tag_input = QtWidgets.QLineEdit()
        self.tag_input.setCompleter(self.completer)

        add_button = QtWidgets.QPushButton("Add", self)
        add_button.clicked.connect(self.addTag)
        add_widget_hbox.addWidget(self.tag_input)
        add_widget_hbox.addWidget(add_button)

        vbox.addLayout(add_widget_hbox)

        # Tag list
        self.tag_list_model = QtCore.QStringListModel()
        self.tag_list = QtWidgets.QListView()
        self.tag_list.setModel(self.tag_list_model)
        vbox.addWidget(self.tag_list)
        remove_button = QtWidgets.QPushButton("Remove", self)
        vbox.addWidget(remove_button)

        # Standard buttons
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
            self.sigAdd2tag.emit(tag)


class Tagger(QtWidgets.QWidget):
    sigSaveToJson = Signal(dict)

    def __init__(self, parent = None):
        super().__init__(parent)
        self._model = TagModel()
        self._model.dataChanged.connect(self.saveTagged)
        self._model.rowsInserted.connect(self.saveTagged)
        self.initUI()
    
    def initUI(self):
        vbox = QtWidgets.QVBoxLayout()
        self.setLayout(vbox)

        # Tag treeview
        self.tagview = QtWidgets.QTreeView()
        self.tagview.setModel(self._model)
        self.tagview.hideColumn(1)

        vbox.addWidget(self.tagview)

    def model(self) -> TagModel:
        return self._model
    
    @Slot()
    def saveTagged(self):
        doc = self.model().to_json()
        self.sigSaveToJson.emit(doc)


