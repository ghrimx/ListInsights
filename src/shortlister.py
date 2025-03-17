from qtpy import QtCore, QtWidgets, QtGui, Slot
from widgets.basetab import BaseTab

class NoteCustomItemDelegate(QtWidgets.QStyledItemDelegate):
    def createEditor(self, parent, options, index: QtCore.QModelIndex):
        return QtWidgets.QTextEdit(parent)

    def setEditorData(self, editor: QtWidgets.QWidget, index: QtCore.QModelIndex):
        editor.setText(index.data())

    def setModelData(self, editor: QtWidgets.QTextEdit, model, index: QtCore.QModelIndex):
        model.setData(index, editor.toPlainText(), QtCore.Qt.ItemDataRole.EditRole)

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
        super(ShortListModel, self).__init__()
        self._items = []

    def items(self):
        return self._items

    def refresh(self, row):
        top_left = self.index(row, 0)
        self.dataChanged.emit(top_left, top_left)

    def clear(self):
        if len(self._items) > 0:
            self.removeRows(0, len(self._items))

    def prependItem(self, note: ShortListItem):
        new_index = 0
        self.beginInsertRows(QtCore.QModelIndex(), new_index, new_index)
        item = note
        self._items.insert(new_index, item)
        self.endInsertRows()
        return item

    def appendItem(self, item: ShortListItem):
        new_index = len(self._items)
        self.beginInsertRows(QtCore.QModelIndex(), new_index, new_index)
        self._items.append(item)
        self.endInsertRows()
        return item

    def noteDateChanged(self, item):
        for i, current_item in enumerate(self._items):
            if current_item == item:
                self.refresh(i)
                break

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

    def getItem(self, index: QtCore.QModelIndex):
        if not index.isValid():
            return None
        # item: ShortListItem = index.internalPointer()
        item: ShortListItem = self._items[index.row()]
        return item if item else None

    def data(self, index, role=QtCore.Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        
        item: ShortListItem = self._items[index.row()]

        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            return item
        
    def setData(self, index: QtCore.QModelIndex, item: ShortListItem, role=QtCore.Qt.ItemDataRole.EditRole):
        self._items[index.row()] = item
        self.dataChanged.emit(index, index, role)

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
        """Load model from a nested dictionary returned by json.loads()

        Arguments:
            document (dict): JSON-compatible dictionary
        """

        assert isinstance(document, (dict)), f"`document` must be of type dict not {type(document)}"

        self.beginResetModel()

        items = sorted(document.items()) if sort else document.items()

        for key, value in items:
            annotation = ShortListItem(value["body"], key, value["tags"], value["finding"])
            self.appendItem(annotation)

        self.endResetModel()

        return True


class ShortListDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, view: QtWidgets.QListView, proxy_model: QtCore.QSortFilterProxyModel= None):
        super().__init__(view)
        self.view = view
        self.proxy_model = view.model()

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
        tag_rect = item_rect.adjusted(30, 23, -10, 0)
        painter.drawText(tag_rect, QtCore.Qt.AlignmentFlag.AlignRight, ", ".join(item.tags))

        # Body content
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

class TextEdit(QtWidgets.QTextEdit):
    def __init__(self):
        super(TextEdit, self).__init__()
        self.setViewportMargins(20, 20, 20, 20)
        self.setStyleSheet("""QTextEdit {
                                background: #fff;
                                color: #333;
                            }""")
        font = QtGui.QFont()
        font.setPixelSize(16)
        document = self.document()
        document.setDefaultFont(font)
    
class ShortLister(BaseTab):
    def __init__(self, parent = None):
        super().__init__(parent)

        self._model = ShortListModel()
        self.initUI()
    
    def initUI(self):
        # ShortList listview
        self._shortlist_view = ShortListView()
        self._shortlist_view.setModel(self._model)
        self._shortlist_view.selectionModel().currentChanged.connect(self.onShortListItemSelected)

        # ShortList Delegate
        delegate = ShortListDelegate(self._shortlist_view)
        delegate.setContentsMargins(8, 8, 8, 8)
        delegate.setIconSize(24, 24)
        delegate.setHorizontalSpacing(8)
        delegate.setVerticalSpacing(4)
        self._shortlist_view.setItemDelegate(delegate)

        # QTextedit
        self.textedit = TextEdit()

        self.splitter.addWidget(self._shortlist_view)
        self.splitter.addWidget(self.textedit)

    def model(self) -> ShortListModel:
        return self._model
    
    def shortlist_view(self) -> QtWidgets.QListView:
        return self._shortlist_view
    
    @Slot(QtCore.QModelIndex)
    def onShortListItemSelected(self, index: QtCore.QModelIndex):
        body = self._shortlist_view.model().getItem(index).body
        self.textedit.setPlainText(body)