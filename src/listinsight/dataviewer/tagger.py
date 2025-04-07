import logging
from qtpy import QtCore, QtWidgets, Signal, Slot
from utilities import config as mconf

from dataviewer.json_model import JsonModel, TreeItem

logger = logging.getLogger(__name__)


class TagModel(JsonModel):
    def __init__(self):
        super().__init__()
        self._tags = []

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


