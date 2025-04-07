import logging
from qtpy import QtCore, QtWidgets, Signal, Slot
from utilities import config as mconf

from dataviewer.json_model import JsonModel

logger = logging.getLogger(__name__)


class TagItem(QtCore.QObject):
    def __init__(self, sname: str, lvalues: list = []):
        super().__init__()
        self._name = sname
        self._values = lvalues
 
    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, sname: str):
        self._name = sname

    @property
    def values(self):
        return self._values
    
    @values.setter
    def values(self, lvalues):
        self._values = lvalues

    def addValue(self, val):
        if not val in self._values:
            self._values.append(val) 
    
    def removeValue(self, val):
        self._values.remove(val)

    def __repr__(self):
        return repr(self._name)


class TagModel(QtCore.QAbstractListModel):
    def __init__(self):
        super().__init__()
        self._tags = []

    def tags(self) -> list[TagItem]:
        return self._tags

    def tagnames(self) -> list[str]:
        return [tag.name for tag in self._tags]

    def refresh(self, row):
        top_left = self.index(row, 0)
        self.dataChanged.emit(top_left, top_left)

    def clear(self):
        if len(self._tags) > 0:
            self.removeRows(0, len(self._tags))

    def prependItem(self, tag: TagItem):
        new_index = 0
        self.beginInsertRows(QtCore.QModelIndex(), new_index, new_index)
        # self._tags.insert(new_index, tag)
        self.endInsertRows()
        return tag

    def appendItem(self, tag: TagItem):
        new_index = len(self._tags)
        self.beginInsertRows(QtCore.QModelIndex(), new_index, new_index)
        # self._tags.append(tag)
        self.endInsertRows()
        return tag

    def insertRows(self, position, rows, parent=QtCore.QModelIndex()):
        self.beginInsertRows(parent, position, position + rows - 1)
        for _ in range(rows):
            self._tags.insert(position, TagItem(None))
        self.endInsertRows()
        return True

    def removeRows(self, position, rows, parent=QtCore.QModelIndex()):
        self.beginRemoveRows(parent, position, position + rows - 1)
        for _ in range(rows):
            del self._tags[position]
        self.endRemoveRows()
        return True

    def columnCount(self, parent=QtCore.QModelIndex()):
        return 1

    def getItem(self, index: QtCore.QModelIndex) -> TagItem|None:
        if not index.isValid():
            return None
        
        tag: TagItem = self._tags[index.row()]
        return tag if tag else None
    
    def getTagbyName(self, tagname: str) -> TagItem|None:
        for tag in self.tags():
            if tag.name == tagname:
                return tag
        
        return None

    def addTags(self, value: str, tags: list):

        ...

    
    def addToItem(self, tagname: str, value: str):
        """Add value to a tag item using its tagname"""
        for tag in self.tags():
            if tag.name == tagname:
                tag.addValue(value)

    def addTag(self, tagname: str, value: str):
        tag = TagItem(tagname)
        self.appendItem(tag)
        tag.addValue(value)

    def data(self, index, role=QtCore.Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        
        tag: TagItem = self._tags[index.row()]

        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            return tag.name
        
    def setData(self, index: QtCore.QModelIndex, tag: TagItem, role=QtCore.Qt.ItemDataRole.EditRole):
        if not index.isValid():
            return None
        
        if not role == QtCore.Qt.ItemDataRole.EditRole:
            return
        
        self._tags[index.row()] = tag
        self.dataChanged.emit(index, index)

    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.ItemFlag.NoItemFlags
        return super().flags(index)

    def headerData(self, section, orientation, role=QtCore.Qt.ItemDataRole.DisplayRole):
        return None

    def index(self, row, column, parent=QtCore.QModelIndex()):
        if self.hasIndex(row, column, parent):
            return self.createIndex(row, column, self._tags[row])
        return QtCore.QModelIndex()

    def parent(self, index):
        return QtCore.QModelIndex()

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self._tags)
        
    def load(self, document: dict, sort = True):
        """Load model from a nested dictionary

        Arguments:
            document (dict): JSON-compatible dictionary
        """

        if not isinstance(document, (dict)):
            logger.error(f"`document` must be of type dict not {type(document)}")
            return

        self.beginResetModel()

        items = sorted(document.items()) if sort else document.items()

        for key, value in items:
            tag = TagItem(key, value)
            self.appendItem(tag)

        self.endResetModel()

        return True
    
    def toJson(self) -> dict:
        """Return a JSON-compatible dictionary"""
        document = {}
        tag: TagItem
        for tag in self._tags:
            document[tag.name] = tag.values
        
        return document


class TagListview(QtWidgets.QListView):
    def __init__(self, parent=None):
        super().__init__(parent)


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
            print("here")
            self.sigAdd2tag.emit(tag)


class Tagger(QtWidgets.QWidget):
    sigSaveToJson = Signal(dict)

    def __init__(self, parent = None):
        super().__init__(parent)
        # self._model = TagModel()
        self._model = JsonModel()
        self._model.dataChanged.connect(self.saveTagged)
        self._model.rowsInserted.connect(self.saveTagged)
        self.initUI()
    
    def initUI(self):
        vbox = QtWidgets.QVBoxLayout()
        self.setLayout(vbox)

        # Tag listview
        # self.tag_listview = TagListview()
        self.tag_listview = QtWidgets.QTreeView()
        self.tag_listview.setModel(self._model)
        self.tag_listview.hideColumn(1)

        vbox.addWidget(self.tag_listview)

    def model(self) -> TagModel:
        return self._model
    
    @Slot()
    def saveTagged(self):
        doc = self.model().to_json()
        self.sigSaveToJson.emit(doc)


