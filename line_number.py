from PySide6.QtCore import QRectF, QRect, Qt, QSize
from PySide6.QtGui import QResizeEvent, QTextCursor, QPaintEvent, QPainter, QColor
from PySide6.QtWidgets import QTextEdit, QWidget


class LineNumberArea(QWidget):
    def __init__(self, editor):
        QWidget.__init__(self, editor)
        self.codeEditor = editor

    def sizeHint(self) -> QSize:
        return QSize(self.codeEditor.lineNumberAreaWidth(), 0)

    def paintEvent(self, event):
        self.codeEditor.lineNumberAreaPaintEvent(event)

class QTextEditHighlighter(QTextEdit):
    def __init__(self):
        # Line numbers
        QTextEdit.__init__(self)
        self.lineNumberArea = LineNumberArea(self)

        self.document().blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.verticalScrollBar().valueChanged.connect(self.updateLineNumberArea)
        self.textChanged.connect(self.updateLineNumberArea)
        self.cursorPositionChanged.connect(self.updateLineNumberArea)

        self.updateLineNumberAreaWidth(0)

    def insertFromMimeData(self, source):
        self.insertPlainText(source.text())

    def lineNumberAreaWidth(self):
        digits = 1
        m = max(1, self.document().blockCount())
        while m >= 10:
            m /= 10
            digits += 1
        space = 13 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def updateLineNumberAreaWidth(self, newBlockCount: int):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def updateLineNumberAreaRect(self, rect_f: QRectF):
        self.updateLineNumberArea()

    def updateLineNumberAreaInt(self, slider_pos: int):
        self.updateLineNumberArea()

    def updateLineNumberArea(self):
        """        
        When the signal is emitted, the sliderPosition has been adjusted according to the action,
        but the value has not yet been propagated (meaning the valueChanged() signal was not yet emitted),
        and the visual display has not been updated. In slots connected to self signal you can thus safely
        adjust any action by calling setSliderPosition() yourself, based on both the action and the
        slider's value.
        """
        
        # Make sure the sliderPosition triggers one last time the valueChanged() signal with the actual value !!!!
        self.verticalScrollBar().setSliderPosition(self.verticalScrollBar().sliderPosition())
    
        # Since "QTextEdit" does not have an "updateRequest(...)" signal, we chose
        # to grab the imformations from "sliderPosition()" and "contentsRect()".
        # See the necessary connections used (Class constructor implementation part).
    
        rect = self.contentsRect()

        self.lineNumberArea.update(0, rect.y(), self.lineNumberArea.width(), rect.height())
        self.updateLineNumberAreaWidth(0)
        
        dy = self.verticalScrollBar().sliderPosition()
        if dy > -1:
            self.lineNumberArea.scroll(0, dy)
    
        # Addjust slider to alway see the number of the currently being edited line...
        first_block_id = self.getFirstVisibleBlockId()
        if first_block_id == 0 or self.textCursor().block().blockNumber() == first_block_id-1:
            self.verticalScrollBar().setSliderPosition(dy-self.document().documentMargin())
    
    #    # Snap to first line (TODO...)
    #    if first_block_id > 0:
    #        slider_pos = self.verticalScrollBar().sliderPosition()
    #        prev_block_height = (int) self.document().documentLayout().blockBoundingRect(self.document().findBlockByNumber(first_block_id-1)).height()
    #        if (dy <= self.document().documentMargin() + prev_block_height)
    #            self.verticalScrollBar().setSliderPosition(slider_pos - (self.document().documentMargin() + prev_block_height))

    def resizeEvent(self, event: QResizeEvent):
        QTextEdit.resizeEvent(self, event)

        cr = self.contentsRect()
        self.lineNumberArea.setGeometry(QRect(cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height()))

    def getFirstVisibleBlockId(self) -> int:
        # Detect the first block for which bounding rect - once translated
        # in absolute coordinated - is contained by the editor's text area
    
        # Costly way of doing but since "blockBoundingGeometry(...)" doesn't
        # exists for "QTextEdit"...
    
        curs = QTextCursor(self.document())
        curs.movePosition(QTextCursor.Start)
        for i in range(self.document().blockCount()):
            block = curs.block()
    
            r1 = self.viewport().geometry()
            r2 = self.document().documentLayout().blockBoundingRect(block).translated(
                    self.viewport().geometry().x(), self.viewport().geometry().y() - (
                        self.verticalScrollBar().sliderPosition()
                        )).toRect()
    
            if r1.contains(r2, True):
                return i
    
            curs.movePosition(QTextCursor.NextBlock)
        return 0
    
    def lineNumberAreaPaintEvent(self, event: QPaintEvent):
        self.verticalScrollBar().setSliderPosition(self.verticalScrollBar().sliderPosition())
    
        painter = QPainter(self.lineNumberArea)
        painter.fillRect(event.rect(), Qt.lightGray)
        blockNumber = self.getFirstVisibleBlockId()
    
        block = self.document().findBlockByNumber(blockNumber)

        if blockNumber > 0:
            prev_block = self.document().findBlockByNumber(blockNumber - 1)
        else:
            prev_block = block

        if blockNumber > 0:
            translate_y = -self.verticalScrollBar().sliderPosition()
        else:
            translate_y = 0
    
        top = self.viewport().geometry().top()
    
        # Adjust text position according to the previous "non entirely visible" block
        # if applicable. Also takes in consideration the document's margin offset.

        if blockNumber == 0:
            # Simply adjust to document's margin
            additional_margin = self.document().documentMargin() -1 - self.verticalScrollBar().sliderPosition()
        else:
            # Getting the height of the visible part of the previous "non entirely visible" block
            additional_margin = self.document().documentLayout().blockBoundingRect(prev_block) \
                    .translated(0, translate_y).intersected(self.viewport().geometry()).height()
    
        # Shift the starting point
        top += additional_margin
    
        bottom = top + int(self.document().documentLayout().blockBoundingRect(block).height())
    
        col_1 = QColor(20, 154, 21)      # Current line (custom green)
        col_0 = QColor(0, 0, 0)    # Other lines  (custom darkgrey)
    
        # Draw the numbers (displaying the current line number in green)
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = f"{blockNumber + 1}"
                painter.setPen(QColor(120, 120, 120))

                if self.textCursor().blockNumber() == blockNumber:
                    painter.setPen(col_1)
                else:
                    painter.setPen(col_0)

                painter.drawText(-5, top,
                                 self.lineNumberArea.width(), self.fontMetrics().height(),
                                 Qt.AlignRight, number)

            block = block.next()
            top = bottom
            bottom = top + int(self.document().documentLayout().blockBoundingRect(block).height())
            blockNumber += 1

