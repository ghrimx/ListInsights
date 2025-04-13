import logging
from qtpy import QtCore, QtWidgets, QtGui, Slot, Signal
from utilities import config as mconf

logger = logging.getLogger(__name__)


class ShortListProxyModel(QtCore.QSortFilterProxyModel):
    def __init__(self, model):
        super().__init__()

        self.setSourceModel(model)

        self.user_filter = QtCore.QRegularExpression()
        self.pattern_filter = ""

    def setPatternFilter(self, pattern: str):
        self.pattern_filter = pattern
    
    def filterAcceptsRow(self, source_row: int, source_parent: QtCore.QModelIndex) -> bool:
        model: ShortListModel = self.sourceModel()
        index = model.index(source_row, 0)

        if not index.isValid():
            return

        item: ShortListItem = model.getItem(index)

        if self.pattern_filter in item.title:
            return True
        elif self.pattern_filter in item.body:
            return True
        elif self.pattern_filter in item.tags:
            return True
        else:
            return False

class ShortListItem(QtCore.QObject):
    def __init__(self, text: str, stitle: str, ltags: list = [], finding: bool = False):
        super().__init__()
        self._body = text
        self._title = stitle
        self._tags = ltags
        self._finding = finding

    @property
    def body(self):
        return self._body

    @body.setter
    def body(self, text: str):
        self._body = text

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, stitle: str):
        self._title = stitle

    @property
    def tags(self):
        return self._tags
    
    @tags.setter
    def tags(self, ltags: list):
        self._tags = ltags

    @property
    def finding(self):
        return self._finding
    
    @finding.setter
    def finding(self, finding: bool):
        self._finding = finding


class ShortListModel(QtCore.QAbstractItemModel):
    def __init__(self):
        super().__init__()
        self._items = []

    def items(self):
        return self._items

    def refresh(self, row):
        top_left = self.index(row, 0)
        self.dataChanged.emit(top_left, top_left)

    def clear(self):
        if len(self._items) > 0:
            self.removeRows(0, len(self._items))

    def prependItem(self, item: ShortListItem):
        new_index = 0
        self.beginInsertRows(QtCore.QModelIndex(), new_index, new_index)
        self._items.insert(new_index, item)
        self.endInsertRows()
        return item

    def appendItem(self, item: ShortListItem):
        new_index = len(self._items)
        self.beginInsertRows(QtCore.QModelIndex(), new_index, new_index)
        self._items.append(item)
        self.endInsertRows()
        return item

    def insertRows(self, position, rows, parent=QtCore.QModelIndex()):
        self.beginInsertRows(parent, position, position + rows - 1)
        for _ in range(rows):
            self._items.insert(position, ShortListItem(None))
        self.endInsertRows()
        return True

    def removeRows(self, position, rows, parent=QtCore.QModelIndex()):
        self.beginRemoveRows(parent, position, position + rows - 1)
        for _ in range(rows):
            del self._items[position]
        self.endRemoveRows()
        return True

    def columnCount(self, parent=QtCore.QModelIndex()):
        return 1

    def getItem(self, index: QtCore.QModelIndex) -> ShortListItem:
        if not index.isValid():
            return None
        
        item: ShortListItem = self._items[index.row()]
        return item if item else None

    def data(self, index, role=QtCore.Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        
        item: ShortListItem = self._items[index.row()]

        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            return item
        
    def setData(self, index: QtCore.QModelIndex, item: ShortListItem, role=QtCore.Qt.ItemDataRole.EditRole):
        if not index.isValid():
            return None
        
        if not role == QtCore.Qt.ItemDataRole.EditRole:
            return
        
        self._items[index.row()] = item
        self.dataChanged.emit(index, index)

    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.ItemFlag.NoItemFlags
        return super().flags(index)

    def headerData(self, section, orientation, role=QtCore.Qt.ItemDataRole.DisplayRole):
        return None

    def index(self, row, column, parent=QtCore.QModelIndex()):
        if self.hasIndex(row, column, parent):
            return self.createIndex(row, column, self._items[row])
        return QtCore.QModelIndex()

    def parent(self, index):
        return QtCore.QModelIndex()

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self._items)
        
    def load(self, document: dict, sort = True):
        """Load model from a nested dictionary

        Arguments:
            document (dict): JSON-compatible dictionary
        """

        if not isinstance(document, (dict)):
            logger.error(f"`document` must be of type dict not {type(document)}")
            return

        items = sorted(document.items()) if sort else document.items()
        
        self.beginResetModel()
        self.clear()

        for key, value in items:
            shortlist_item = ShortListItem(value["body"], key, value["tags"], value["finding"])
            self.appendItem(shortlist_item)

        self.endResetModel()

        return True
    
    def toJson(self) -> dict:
        """Return a JSON-compatible dictionary"""
        document = {}
        item: ShortListItem
        for item in self._items:
            document[item.title] = {"finding":item.finding,
                                    "tags":item.tags,
                                    "body":item.body}
        
        return document


class ShortListDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self):
        super().__init__()
        self.margins: QtCore.QMargins = QtCore.QMargins()
        self.icon_size: QtCore.QSize =  QtCore.QSize()
        self.spacing_horizontal: int = 0
        self.spacing_vertical: int = 0

    def setIconSize(self, width: int, height: int):
        self.icon_size = QtCore.QSize(width, height)

    def setContentsMargins(self, left: int, top: int, right: int, bottom: int):
        self.margins = QtCore.QMargins(left, top, right, bottom)
    
    def setHorizontalSpacing(self, spacing: int):
        self.spacing_horizontal = spacing

    def setVerticalSpacing(self, spacing: int):
        self.spacing_vertical = spacing

    def paint(self, painter, option: QtWidgets.QStyleOptionViewItem, index: QtCore.QModelIndex):
        item: ShortListItem = index.data(QtCore.Qt.ItemDataRole.DisplayRole)

        # Selection behaviour
        if option.state & QtWidgets.QStyle.StateFlag.State_Selected:
            painter.setPen(QtGui.QColorConstants.Black)
            painter.fillRect(option.rect, QtGui.QColorConstants.Svg.aliceblue)
        else:
            painter.setPen(QtGui.QColorConstants.Black)
            painter.fillRect(option.rect, option.palette.base())

        rect: QtCore.QRect = option.rect

        item_rect = rect.adjusted(self.margins.left(),
                                  self.margins.top(),
                                  -self.margins.right(),
                                  -self.margins.bottom())
        
        painter.save()
        painter.setClipping(True)
        painter.setClipRect(rect)

        # Draw Item icon
        if item.finding:
            option.icon = QtGui.QIcon(":alert-fill-red")
        else:
            option.icon = QtGui.QIcon()

        hasIcon = not option.icon.isNull()
        if hasIcon:
            painter.drawPixmap(item_rect.left(),
                               item_rect.top(),
                               option.icon.pixmap(self.icon_size))

        # Title
        font = painter.font()
        font.setPointSize(10)
        font.setWeight(QtGui.QFont.Weight.Bold)
        painter.setFont(font)
        title_rect = item_rect.adjusted(30, 0, -10, 0)
        painter.drawText(title_rect, QtCore.Qt.AlignmentFlag.AlignLeft, item.title)

        # Tags
        font.setWeight(QtGui.QFont.Weight.Normal)
        painter.setFont(font)
        painter.setPen(QtGui.QColorConstants.Svg.dodgerblue)
        tag_rect = item_rect.adjusted(30, 23, -10, 0)
        painter.drawText(tag_rect, QtCore.Qt.AlignmentFlag.AlignRight, ", ".join(item.tags))

        # Body content
        if not item.body.strip() == "":
            painter.setPen(QtGui.QColorConstants.Black)
            excerpt_rect = item_rect.adjusted(30, 53, -10, 0)
            flags = QtCore.Qt.AlignmentFlag.AlignLeft|QtCore.Qt.TextFlag.TextWordWrap
            fontm = painter.fontMetrics()
            excerpt = fontm.elidedText(item.body, QtCore.Qt.TextElideMode.ElideRight, excerpt_rect.width() * 2)
            painter.drawText(excerpt_rect, flags, excerpt)

        # Bottom border line
        painter.setPen(QtCore.Qt.GlobalColor.gray)
        painter.drawLine(option.rect.bottomLeft(), option.rect.bottomRight())

        painter.restore()

    def sizeHint(self, option, index):
        return QtCore.QSize(200, 100)
    
class ShortListView(QtWidgets.QListView):
    def __init__(self):
        super(ShortListView, self).__init__()


class ShortListEditor(QtWidgets.QDialog):
    def __init__(self, item: ShortListItem, parent = None):
        super().__init__(parent)
        self._item = item

        self.setWindowTitle("ShortLister - Editor")
        self.setMinimumWidth(450)

        buttons = (QtWidgets.QDialogButtonBox.StandardButton.Save | QtWidgets.QDialogButtonBox.StandardButton.Cancel)

        self.buttonBox = QtWidgets.QDialogButtonBox(buttons)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        vbox = QtWidgets.QVBoxLayout()
        self.setLayout(vbox)

        self.title_lineedit = QtWidgets.QLineEdit()
        self.title_lineedit.setPlaceholderText("title...")
        self.title_lineedit.setText(self._item.title)
        self.tags_lineedit = QtWidgets.QLineEdit()
        self.tags_lineedit.setPlaceholderText("Tags...")
        self.tags_lineedit.setText(",".join(self._item.tags))
        self.body_editor = QtWidgets.QTextEdit()
        self.body_editor.setMarkdown(self._item.body)

        vbox.addWidget(self.title_lineedit)
        vbox.addWidget(self.tags_lineedit)
        vbox.addWidget(self.body_editor)
        vbox.addWidget(self.buttonBox)
        self.body_editor.setFocus()
        cursor = self.body_editor.textCursor()
        cursor.movePosition(QtGui.QTextCursor.MoveOperation.End)
        self.body_editor.setTextCursor(cursor)

    def accept(self):
        self._item.body = self.body_editor.toMarkdown()
        self._item.title = self.title_lineedit.text()
        self._item.tags = self.tags_lineedit.text().split(",")
        return super().accept()
        
    def item(self):
        return self._item
    
class ShortLister(QtWidgets.QWidget):
    sigSaveToJson = Signal(dict)
    sigTagsEdited = Signal(str,str)

    def __init__(self, parent = None):
        super().__init__(parent)
        self._model = ShortListModel()
        self._proxymodel = ShortListProxyModel(self._model)
        self._proxymodel.setDynamicSortFilter(False)       
        self.initUI()
                
    def initUI(self):
        vbox = QtWidgets.QVBoxLayout()
        self.setLayout(vbox)

        # Buttons layout
        hbox = QtWidgets.QHBoxLayout()
        vbox.addLayout(hbox)

        # Search tool
        self.search_tool = QtWidgets.QLineEdit()
        self.search_tool.setPlaceholderText("Search...")
        self.search_tool.textChanged.connect(self.searchfor)
        tags: list = mconf.settings.value("tags", [], list)
        completer = QtWidgets.QCompleter(tags)
        completer.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        self.search_tool.setCompleter(completer)
        hbox.addWidget(self.search_tool)

        # Add/Remove buttons
        add_btn = QtWidgets.QToolButton()
        add_btn.setIcon(QtGui.QIcon(":add-box"))
        add_btn.clicked.connect(self.newShortlistItem)
        remove_btn = QtWidgets.QToolButton()
        remove_btn.setIcon(QtGui.QIcon(":delete-bin2"))
        remove_btn.clicked.connect(self.removeShortlistItem)
        hbox.addWidget(add_btn)
        hbox.addWidget(remove_btn)

        # ShortList listview
        self._shortlist_view = ShortListView()
        self._shortlist_view.setModel(self._proxymodel)
        self._shortlist_view.doubleClicked.connect(self.editShortlistItem)

        # ShortList Delegate
        delegate = ShortListDelegate()
        delegate.setContentsMargins(8, 8, 8, 8)
        delegate.setIconSize(24, 24)
        delegate.setHorizontalSpacing(8)
        delegate.setVerticalSpacing(4)
        self._shortlist_view.setItemDelegate(delegate)

        vbox.addWidget(self._shortlist_view)
        
    def model(self) -> ShortListModel:
        return self._model
    
    def shortlist_view(self) -> QtWidgets.QListView:
        return self._shortlist_view

    @Slot(QtCore.QModelIndex)
    def editShortlistItem(self, index: QtCore.QModelIndex):
        src_index = self._proxymodel.mapToSource(index)
        item = self.model().getItem(src_index)
        self.editor = ShortListEditor(item, self)

        if self.editor.exec():
            body_modified = self.editor.body_editor.document().isModified()
            title_modified = self.editor.title_lineedit.isModified()
            tags_modified = self.editor.tags_lineedit.isModified()
            isModified = body_modified or title_modified or tags_modified
            notEmpty = self.editor.body_editor.toPlainText() != "" and self.editor.title_lineedit.text() != ""

            if isModified and notEmpty:
                item = self.editor.item()
                self.model().setData(src_index, item, QtCore.Qt.ItemDataRole.EditRole)
                self.saveShortList()
            
                #TODO: Append or Remove tags
                if tags_modified and self.editor.tags_lineedit.text().strip() != "":
                    self.sigTagsEdited.emit(self.editor.title_lineedit.text().strip(), self.editor.tags_lineedit.text().strip())

    @Slot()
    def newShortlistItem(self):
        self.addShortlistItem()

    @Slot(str, str)
    def addShortlistItem(self, title: str = "", tags: str = ""):
        item = ShortListItem("", title, tags.split(","))
        self.editor = ShortListEditor(item, self)

        if self.editor.exec():
            if self.editor.title_lineedit.text().strip() != "":
                item = self.editor.item()
                self.model().appendItem(item)
                self.saveShortList()
            
                #TODO: Append or Remove tags
                if self.editor.tags_lineedit.isModified() and self.editor.tags_lineedit.text().strip() != "":
                    self.sigTagsEdited.emit(self.editor.title_lineedit.text().strip(), self.editor.tags_lineedit.text().strip())

    @Slot()
    def removeShortlistItem(self):
        index = self._shortlist_view.selectionModel().currentIndex()
        src_index = self._proxymodel.mapToSource(index)

        if self.model().removeRows(src_index.row(), 1):
            self.saveShortList()

    @Slot()
    def searchfor(self):
        pattern = self.search_tool.text()
        self._proxymodel.setPatternFilter(pattern)
        self._proxymodel.invalidateFilter()

    def saveShortList(self):
        doc = self.model().toJson()
        self.sigSaveToJson.emit(doc)

