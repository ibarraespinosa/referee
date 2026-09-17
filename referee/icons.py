"""
Vector icon generator for ReviewerPDF toolbar and action buttons.
Renders crisp icons using QPainter with no external image asset dependencies.
"""
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QPen, QBrush, QPainterPath, QFont
from PyQt5.QtCore import Qt, QRectF, QPointF

def _create_base_pixmap(size=24):
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)
    return pix

def get_icon(name: str, color="#e0e0e0", accent="#E95420") -> QIcon:
    """Generate a clean vector QIcon by name."""
    pix = _create_base_pixmap(24)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.Antialiasing)
    
    pen = QPen(QColor(color), 1.8, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    painter.setPen(pen)
    
    if name == "select":
        # Mouse pointer arrow
        path = QPainterPath()
        path.moveTo(6, 4)
        path.lineTo(6, 18)
        path.lineTo(10, 14)
        path.lineTo(13.5, 20)
        path.lineTo(15.5, 19)
        path.lineTo(12, 13)
        path.lineTo(17, 13)
        path.closeSubpath()
        painter.setBrush(QBrush(QColor(color)))
        painter.drawPath(path)
        
    elif name == "hand":
        # Hand pan tool
        painter.drawRoundedRect(QRectF(7, 7, 10, 12), 3, 3)
        painter.drawLine(9, 4, 9, 7)
        painter.drawLine(12, 3, 12, 7)
        painter.drawLine(15, 5, 15, 7)
        
    elif name == "highlight":
        # Highlighter pen with colored swatch
        path = QPainterPath()
        path.moveTo(6, 17)
        path.lineTo(13, 6)
        path.lineTo(17, 9)
        path.lineTo(10, 20)
        path.closeSubpath()
        painter.setBrush(QBrush(QColor("#404040")))
        painter.drawPath(path)
        # Tip
        tip = QPainterPath()
        tip.moveTo(6, 17)
        tip.lineTo(4, 21)
        tip.lineTo(9, 21)
        tip.lineTo(10, 20)
        tip.closeSubpath()
        painter.setBrush(QBrush(QColor(accent)))
        painter.setPen(Qt.NoPen)
        painter.drawPath(tip)
        # Highlighted swatch underneath
        painter.setBrush(QBrush(QColor(255, 235, 59, 180)))
        painter.drawRoundedRect(QRectF(3, 21, 18, 3), 1, 1)

    elif name == "underline":
        # 'U' with underline
        font = QFont("Ubuntu", 11, QFont.Bold)
        painter.setFont(font)
        painter.drawText(QRectF(0, 2, 24, 16), Qt.AlignCenter, "U")
        painter.setPen(QPen(QColor(accent), 2, Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(5, 20, 19, 20)

    elif name == "strikeout":
        # 'S' with strikethrough
        font = QFont("Ubuntu", 11, QFont.Bold)
        painter.setFont(font)
        painter.drawText(QRectF(0, 3, 24, 16), Qt.AlignCenter, "S")
        painter.setPen(QPen(QColor("#ff5252"), 2, Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(4, 12, 20, 12)

    elif name == "note":
        # Sticky note / Comment bubble
        path = QPainterPath()
        path.moveTo(4, 5)
        path.lineTo(20, 5)
        path.lineTo(20, 15)
        path.lineTo(12, 15)
        path.lineTo(7, 19)
        path.lineTo(7, 15)
        path.lineTo(4, 15)
        path.closeSubpath()
        painter.setBrush(QBrush(QColor("#3d3d3d")))
        painter.drawPath(path)
        # Lines inside note
        painter.setPen(QPen(QColor(accent), 1.5, Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(7, 9, 17, 9)
        painter.drawLine(7, 12, 14, 12)

    elif name == "freetext":
        # Text box tool 'T'
        painter.setPen(QPen(QColor("#666666"), 1, Qt.DashLine))
        painter.drawRect(QRectF(3, 3, 18, 18))
        font = QFont("Ubuntu", 12, QFont.Bold)
        painter.setFont(font)
        painter.setPen(QPen(QColor(color)))
        painter.drawText(QRectF(3, 3, 18, 18), Qt.AlignCenter, "T")

    elif name == "pen":
        # Freehand pen / pencil
        path = QPainterPath()
        path.moveTo(17, 4)
        path.lineTo(20, 7)
        path.lineTo(9, 18)
        path.lineTo(5, 19)
        path.lineTo(6, 15)
        path.closeSubpath()
        painter.setBrush(QBrush(QColor(color)))
        painter.drawPath(path)

    elif name == "rectangle":
        # Geometric box / shape
        painter.setPen(QPen(QColor(accent), 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawRoundedRect(QRectF(4, 5, 16, 14), 2, 2)

    elif name == "eraser" or name == "delete":
        # Trash bin / Delete
        painter.drawLine(5, 7, 19, 7)
        painter.drawLine(9, 5, 15, 5)
        path = QPainterPath()
        path.moveTo(6, 7)
        path.lineTo(7, 19)
        path.lineTo(17, 19)
        path.lineTo(18, 7)
        painter.drawPath(path)
        painter.drawLine(10, 10, 10, 16)
        painter.drawLine(14, 10, 14, 16)

    elif name == "open":
        # Folder open
        path = QPainterPath()
        path.moveTo(4, 8)
        path.lineTo(9, 8)
        path.lineTo(11, 10)
        path.lineTo(20, 10)
        path.lineTo(20, 18)
        path.lineTo(4, 18)
        path.closeSubpath()
        painter.drawPath(path)

    elif name == "save":
        # Floppy disk save
        path = QPainterPath()
        path.moveTo(5, 4)
        path.lineTo(16, 4)
        path.lineTo(19, 7)
        path.lineTo(19, 20)
        path.lineTo(5, 20)
        path.closeSubpath()
        painter.drawPath(path)
        painter.drawRect(QRectF(8, 4, 8, 5))
        painter.drawRect(QRectF(8, 13, 8, 7))

    elif name == "undo":
        # Undo curved arrow
        path = QPainterPath()
        path.moveTo(18, 16)
        path.cubicTo(18, 9, 11, 9, 8, 11)
        painter.drawPath(path)
        # Arrow head
        tip = QPainterPath()
        tip.moveTo(9, 7)
        tip.lineTo(5, 11)
        tip.lineTo(10, 14)
        painter.drawPath(tip)

    elif name == "redo":
        # Redo curved arrow
        path = QPainterPath()
        path.moveTo(6, 16)
        path.cubicTo(6, 9, 13, 9, 16, 11)
        painter.drawPath(path)
        tip = QPainterPath()
        tip.moveTo(15, 7)
        tip.lineTo(19, 11)
        tip.lineTo(14, 14)
        painter.drawPath(tip)

    elif name == "zoom_in":
        # Magnifier with +
        painter.drawEllipse(QRectF(4, 4, 12, 12))
        painter.drawLine(13, 13, 20, 20)
        painter.drawLine(7, 10, 13, 10)
        painter.drawLine(10, 7, 10, 13)

    elif name == "zoom_out":
        # Magnifier with -
        painter.drawEllipse(QRectF(4, 4, 12, 12))
        painter.drawLine(13, 13, 20, 20)
        painter.drawLine(7, 10, 13, 10)

    elif name == "fit_width":
        # Horizontal arrows with document edges
        painter.drawLine(4, 4, 4, 20)
        painter.drawLine(20, 4, 20, 20)
        painter.drawLine(7, 12, 17, 12)
        painter.drawLine(7, 12, 10, 9)
        painter.drawLine(7, 12, 10, 15)
        painter.drawLine(17, 12, 14, 9)
        painter.drawLine(17, 12, 14, 15)

    elif name == "fit_page":
        # Page boundary with 4 corners
        painter.drawRect(QRectF(6, 4, 12, 16))
        painter.drawLine(9, 8, 15, 8)
        painter.drawLine(9, 12, 15, 12)
        painter.drawLine(9, 16, 13, 16)

    elif name == "search":
        # Search magnifying glass
        painter.drawEllipse(QRectF(5, 5, 11, 11))
        painter.drawLine(14, 14, 20, 20)

    elif name == "export":
        # Document with export arrow
        painter.drawRect(QRectF(4, 4, 11, 16))
        painter.setPen(QPen(QColor(accent), 2, Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(12, 12, 20, 12)
        painter.drawLine(17, 9, 20, 12)
        painter.drawLine(17, 15, 20, 12)

    elif name == "prev":
        # Left arrow
        painter.drawLine(15, 6, 9, 12)
        painter.drawLine(9, 12, 15, 18)

    elif name == "next":
        # Right arrow
        painter.drawLine(9, 6, 15, 12)
        painter.drawLine(15, 12, 9, 18)

    elif name == "first":
        # First page |<
        painter.drawLine(7, 6, 7, 18)
        painter.drawLine(16, 6, 10, 12)
        painter.drawLine(10, 12, 16, 18)

    elif name == "last":
        # Last page >|
        painter.drawLine(17, 6, 17, 18)
        painter.drawLine(8, 6, 14, 12)
        painter.drawLine(14, 12, 8, 18)

    elif name == "sidebar":
        # Sidebar toggle icon
        painter.drawRect(QRectF(4, 4, 16, 16))
        painter.drawLine(10, 4, 10, 20)
        painter.setBrush(QBrush(QColor("#4d4d4d")))
        painter.drawRect(QRectF(4, 4, 6, 16))

    else:
        # Default placeholder circle
        painter.drawEllipse(QRectF(6, 6, 12, 12))

    painter.end()
    return QIcon(pix)
