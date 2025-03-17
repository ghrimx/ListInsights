from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QPainter, QFont
from PyQt6.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem

class Delegate(QStyledItemDelegate):
    def __init__(self, margins, iconSize, spacingHorizontal, spacingVertical, parent=None):
        super().__init__(parent)
        self.margins = margins
        self.iconSize = iconSize
        self.spacingHorizontal = spacingHorizontal
        self.spacingVertical = spacingVertical

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index):
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)

        palette = opt.palette
        rect = opt.rect
        contentRect = rect.adjusted(
            self.margins.left(), self.margins.top(),
            -self.margins.right(), -self.margins.bottom()
        )
        lastIndex = (index.model().rowCount() - 1) == index.row()
        hasIcon = not opt.icon.isNull()
        bottomEdge = rect.bottom()

        # Adjust font size for timestamp
        font = opt.font
        font.setPointSize(self.timestampFontPointSize(opt.font))

        painter.save()
        painter.setClipping(True)
        painter.setClipRect(rect)
        painter.setFont(opt.font)

        # Draw background
        backgroundColor = (
            palette.highlight().color() if option.state & QStyleOptionViewItem.State_Selected
            else palette.light().color()
        )
        painter.fillRect(rect, backgroundColor)

        # Draw bottom line
        lineColor = palette.dark().color() if lastIndex else palette.mid().color()
        painter.setPen(lineColor)
        painter.drawLine(
            rect.left() if lastIndex else self.margins.left(),
            bottomEdge, rect.right(), bottomEdge
        )

        # Draw message icon
        if hasIcon:
            painter.drawPixmap(
                contentRect.left(), contentRect.top(),
                opt.icon.pixmap(self.iconSize)
            )

        # Draw timestamp
        timestampRect = self.timestampBox(opt, index)
        timestampRect.moveTo(
            self.margins.left() + self.iconSize.width() + self.spacingHorizontal,
            contentRect.top()
        )
        painter.setFont(font)
        painter.setPen(palette.text().color())
        painter.drawText(
            timestampRect, Qt.TextFlag.TextSingleLine,
            index.data(Qt.ItemDataRole.UserRole)
        )

        # Draw message text
        messageRect = self.messageBox(opt)
        messageRect.moveTo(
            timestampRect.left(), timestampRect.bottom() + self.spacingVertical
        )
        painter.setFont(opt.font)
        painter.setPen(palette.windowText().color())
        painter.drawText(
            messageRect, Qt.TextFlag.TextSingleLine,
            opt.text
        )

        painter.restore()

    def timestampFontPointSize(self, font):
        # Customize the timestamp font size if needed
        return font.pointSize()

    def timestampBox(self, opt, index):
        # Customize the timestamp box rectangle
        return QRect(0, 0, 100, 20)  # Example size

    def messageBox(self, opt):
        # Customize the message box rectangle
        return QRect(0, 0, 300, 50)  # Example size
