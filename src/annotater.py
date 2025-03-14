from qtpy import QtCore, QtWidgets, QtGui
      

class NoteCustomItemDelegate(QtWidgets.QStyledItemDelegate):
    def createEditor(self, parent, options, index: QtCore.QModelIndex):
        return QtWidgets.QTextEdit(parent)

    def setEditorData(self, editor: QtWidgets.QWidget, index: QtCore.QModelIndex):
        editor.setText(index.data())

    def setModelData(self, editor: QtWidgets.QTextEdit, model, index: QtCore.QModelIndex):
        model.setData(index, editor.toPlainText(), QtCore.Qt.ItemDataRole.EditRole)

class Annotation(QtCore.QObject):
    def __init__(self, text: str, stitle: str, ltags: list = []):
        super().__init__()
        self._note = text
        self._title = stitle
        self._tags = ltags

    @property
    def note(self):
        return self._note

    @note.setter
    def note(self, text: str):
        self._note = text

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

class AnnotationModel(QtCore.QAbstractItemModel):
    def __init__(self, view: QtWidgets.QListView):
        super().__init__()
        self.view = view
        self.note_items = []

        style = f"QListView:item::active {{ color: white; }} QListView:item {{ height: 100 }}"
        self.view.setStyleSheet(style)

    def noteItems(self):
        return self.note_items

    def refresh(self, row):
        top_left = self.index(row, 0)
        self.dataChanged.emit(top_left, top_left)

    def clear(self):
        if len(self.note_items) > 0:
            self.removeRows(0, len(self.note_items))

    def prependItem(self, note: Annotation):
        new_index = 0
        self.beginInsertRows(QtCore.QModelIndex(), new_index, new_index)
        item = note
        self.note_items.insert(new_index, item)
        self.endInsertRows()
        return item

    def appendItem(self, note: Annotation):
        new_index = len(self.note_items)
        self.beginInsertRows(QtCore.QModelIndex(), new_index, new_index)
        item = note
        self.note_items.append(item)
        self.endInsertRows()
        return item

    def noteDateChanged(self, item):
        for i, current_item in enumerate(self.note_items):
            if current_item == item:
                self.refresh(i)
                break

    def insertRows(self, position, rows, parent=QtCore.QModelIndex()):
        self.beginInsertRows(parent, position, position + rows - 1)
        for _ in range(rows):
            self.note_items.insert(position, Annotation(None))
        self.endInsertRows()
        return True

    def removeRows(self, position, rows, parent=QtCore.QModelIndex()):
        self.beginRemoveRows(parent, position, position + rows - 1)
        for _ in range(rows):
            del self.note_items[position]
        self.endRemoveRows()
        return True

    def columnCount(self, parent=QtCore.QModelIndex()):
        return 1

    def noteFromIndex(self, index:QtCore.QModelIndex):
        if not index.isValid():
            return None
        item: Annotation = index.internalPointer()
        return item if item else None

    def data(self, index, role=QtCore.Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        
        item: Annotation = index.internalPointer()

        if not index.isValid() or role != QtCore.Qt.ItemDataRole.DisplayRole:
            return QtCore.QVariant()
        return self.note_items[index.row()]

    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.ItemFlag.NoItemFlags
        return super().flags(index)

    def headerData(self, section, orientation, role=QtCore.Qt.ItemDataRole.DisplayRole):
        return None

    def index(self, row, column, parent=QtCore.QModelIndex()):
        if self.hasIndex(row, column, parent):
            return self.createIndex(row, column, self.note_items[row])
        return QtCore.QModelIndex()

    def parent(self, index):
        return QtCore.QModelIndex()

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.note_items)
    
    def load(self, document: dict, sort = True):
        """Load model from a nested dictionary returned by json.loads()

        Arguments:
            document (dict): JSON-compatible dictionary
        """

        assert isinstance(document, (dict)), f"`document` must be of type dict not {type(document)}"

        self.beginResetModel()

        items = sorted(document.items()) if sort else document.items()

        for key, value in items:
            annotation = Annotation(value["note"], key, value["tags"])
            self.note_items.append(annotation)

        self.endResetModel()

        return True


class AnnotationDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, view: QtWidgets.QListView, proxy_model: QtCore.QSortFilterProxyModel= None):
        super().__init__(view)
        self.view = view
        self.proxy_model = view.model()

    def get_star_rect(self, option: QtWidgets.QStyleOption):
        return QtCore.QRect(option.rect.x() + option.rect.width() - 35,
                     option.rect.y() + option.rect.height() // 2 - 12,
                     25, 25)

    def editorEvent(self, event, model, option: QtWidgets.QStyleOption, index: QtCore.QModelIndex):
        if event.type() == QtCore.QEvent.Type.MouseButtonRelease:
            if event.button() == QtCore.Qt.MouseButton.LeftButton:
                checkbox_rect = self.get_star_rect(option)
                mouse_point = event.pos()
                if checkbox_rect.contains(mouse_point):
                    # real_index = self.proxy_model.mapToSource(index)
                    real_index = index
                    item = real_index.internalPointer()
                    return True
                else:
                    self.view.setCurrentIndex(index)
        return super().editorEvent(event, model, option, index)

    def paint(self, painter, option, index):
        if index.column() == 0:
            real_index = index
            item: Annotation = real_index.internalPointer()

            background = option.palette.highlight() if option.state & QtWidgets.QStyle.StateFlag.State_Selected else option.palette.base()
            painter.fillRect(option.rect, background)

            pen_color = option.palette.highlightedText().color() if option.state & QtWidgets.QStyle.StateFlag.State_Selected else option.palette.text().color()
            painter.setPen(pen_color)

            title_rect = option.rect.adjusted(5, 0, -5, 0)
            font = painter.font()
            font.setPointSize(10)
            font.setWeight(QtGui.QFont.Weight.Bold)
            painter.setFont(font)
            painter.drawText(QtCore.QPoint(option.rect.x() + 10, option.rect.y() + 23), item.title)

            font.setWeight(QtGui.QFont.Weight.Normal)
            painter.setFont(font)
            painter.drawText(QtCore.QPoint(option.rect.x() + 10, option.rect.y() + 43), ", ".join(item.tags))

            excerpt = item.note
            if len(excerpt) > 50:
                excerpt = excerpt[:50] + "..."
            excerpt = " ".join(excerpt.replace("\n", " ").split())
            excerpt_rect = option.rect.adjusted(10, 50, -50, 0)
            painter.drawText(excerpt_rect, 0, excerpt)
        else:
            super().paint(painter, option, index)

    def sizeHint(self, option, index):
        return QtCore.QSize(200, 100)