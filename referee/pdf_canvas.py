"""
Interactive PDF Canvas for ReviewerPDF.
Handles page rendering, fractional zooming, panning, text selection,
live drawing previews, and interactive annotation creation/selection.
"""
import pymupdf
from PyQt5.QtWidgets import (
    QWidget, QScrollArea, QInputDialog, QMenu, QMessageBox, 
    QToolTip, QDialog, QVBoxLayout, QTextEdit, QDialogButtonBox, QLabel
)
from PyQt5.QtGui import (
    QPainter, QColor, QPen, QBrush, QPixmap, QCursor, QFont, 
    QPainterPath, QMouseEvent, QKeyEvent, QPaintEvent
)
from PyQt5.QtCore import Qt, QRectF, QPointF, pyqtSignal, QPoint
from typing import Optional, List, Tuple, Dict, Any

class CommentDialog(QDialog):
    """Clean popup dialog to enter reviewer notes / comments."""
    def __init__(self, parent=None, title="Reviewer Note", initial_text="", header=""):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(380)
        self.setMinimumHeight(200)
        
        layout = QVBoxLayout(self)
        if header:
            lbl = QLabel(f"<b>{header}</b>")
            lbl.setWordWrap(True)
            layout.addWidget(lbl)
            
        layout.addWidget(QLabel("Enter your review comment:"))
        self.text_edit = QTextEdit(self)
        self.text_edit.setPlainText(initial_text)
        self.text_edit.setPlaceholderText("Type feedback, critique, or question...")
        layout.addWidget(self.text_edit)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
    def get_text(self) -> str:
        return self.text_edit.toPlainText().strip()


class PDFCanvas(QWidget):
    """
    Renders the active PDF page and manages user interactions
    (highlighting, drawing, commenting, selecting).
    """
    annotation_added = pyqtSignal(int, str)      # page_idx, annot_id
    annotation_deleted = pyqtSignal(int, str)    # page_idx, annot_id
    annotation_selected = pyqtSignal(dict)       # annot dict
    zoom_changed = pyqtSignal(float)
    status_message = pyqtSignal(str)

    def __init__(self, doc_model, parent=None):
        super().__init__(parent)
        self.doc_model = doc_model
        self.current_page: int = 0
        self.zoom: float = 1.25  # default 125% zoom for comfortable reading
        
        # Current active tool: select, hand, highlight, underline, strikeout, note, freetext, pen, rectangle, eraser
        self.active_tool: str = "select"
        self.active_color_rgb: Tuple[float, float, float] = (1.0, 0.92, 0.23) # Yellow default
        self.active_color_hex: str = "#FFEB3B"
        self.pen_width: float = 2.0

        # Interaction state
        self._is_mouse_pressed: bool = False
        self._drag_start_screen: Optional[QPointF] = None
        self._drag_current_screen: Optional[QPointF] = None
        self._ink_current_stroke: List[Tuple[float, float]] = [] # in PDF points
        self._selected_words: List[Tuple] = []
        self._selected_annot_id: Optional[str] = None
        
        # Pan tool state
        self._pan_start_pos: Optional[QPoint] = None

        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self._update_cursor()

    def set_page(self, page_idx: int):
        """Set current page to display."""
        if 0 <= page_idx < self.doc_model.page_count:
            self.current_page = page_idx
            self._selected_annot_id = None
            self._clear_selection()
            self._update_geometry()
            self.update()

    def set_zoom(self, zoom: float):
        """Set zoom factor (e.g. 1.0 = 100%, 1.5 = 150%)."""
        clamped_zoom = max(0.25, min(zoom, 4.0))
        if abs(self.zoom - clamped_zoom) > 0.001:
            self.zoom = clamped_zoom
            self.doc_model.invalidate_page_cache(self.current_page)
            self._update_geometry()
            self.zoom_changed.emit(self.zoom)
            self.update()

    def set_tool(self, tool_name: str):
        """Set the active review/annotation tool."""
        self.active_tool = tool_name
        self._clear_selection()
        self._update_cursor()
        self.status_message.emit(f"Active tool: {tool_name.capitalize()}")
        self.update()

    def set_color(self, hex_color: str, rgb_tuple: Tuple[float, float, float]):
        self.active_color_hex = hex_color
        self.active_color_rgb = rgb_tuple
        self.update()

    def _update_cursor(self):
        if self.active_tool in ("select", "highlight", "underline", "strikeout"):
            self.setCursor(Qt.IBeamCursor)
        elif self.active_tool == "hand":
            self.setCursor(Qt.OpenHandCursor)
        elif self.active_tool in ("pen", "rectangle"):
            self.setCursor(Qt.CrossCursor)
        elif self.active_tool in ("note", "freetext"):
            self.setCursor(Qt.PointingHandCursor)
        elif self.active_tool in ("eraser", "delete"):
            self.setCursor(Qt.ForbiddenCursor)
        else:
            self.setCursor(Qt.ArrowCursor)

    def _update_geometry(self):
        """Update widget size according to current page and zoom."""
        if not self.doc_model.is_open:
            self.resize(800, 1000)
            return
        
        w, h = self.doc_model.get_page_size(self.current_page)
        screen_w = int(w * self.zoom)
        screen_h = int(h * self.zoom)
        
        # Add margin for shadow/aesthetic centering
        self.setMinimumSize(screen_w + 40, screen_h + 40)
        self.resize(screen_w + 40, screen_h + 40)

    def _get_page_origin(self) -> QPointF:
        """Returns top-left point of page within canvas widget."""
        w, h = self.doc_model.get_page_size(self.current_page)
        screen_w = w * self.zoom
        screen_h = h * self.zoom
        
        # Centered with at least 20px padding
        origin_x = max(20.0, (self.width() - screen_w) / 2.0)
        origin_y = max(20.0, (self.height() - screen_h) / 2.0)
        return QPointF(origin_x, origin_y)

    def _screen_to_pdf_point(self, screen_pt: QPointF) -> QPointF:
        origin = self._get_page_origin()
        pdf_x = (screen_pt.x() - origin.x()) / self.zoom
        pdf_y = (screen_pt.y() - origin.y()) / self.zoom
        return QPointF(pdf_x, pdf_y)

    def _pdf_to_screen_rect(self, pdf_rect: Tuple[float, float, float, float]) -> QRectF:
        origin = self._get_page_origin()
        x0, y0, x1, y1 = pdf_rect
        return QRectF(
            origin.x() + x0 * self.zoom,
            origin.y() + y0 * self.zoom,
            (x1 - x0) * self.zoom,
            (y1 - y0) * self.zoom
        )

    def _clear_selection(self):
        self._selected_words.clear()
        self._drag_start_screen = None
        self._drag_current_screen = None
        self._ink_current_stroke.clear()

    # ==================== PAINT EVENT ====================

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        # Background canvas
        painter.fillRect(self.rect(), QColor("#1e1e1e"))

        if not self.doc_model.is_open:
            painter.setPen(QColor("#888888"))
            painter.setFont(QFont("Ubuntu", 14))
            painter.drawText(self.rect(), Qt.AlignCenter, "No PDF document open.\nUse File -> Open or drag a PDF here.")
            return

        origin = self._get_page_origin()
        w, h = self.doc_model.get_page_size(self.current_page)
        screen_w = w * self.zoom
        screen_h = h * self.zoom
        page_rect = QRectF(origin.x(), origin.y(), screen_w, screen_h)

        # Draw drop shadow behind page
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(0, 0, 0, 100))
        painter.drawRoundedRect(page_rect.translated(4, 4), 3, 3)

        # Draw rendered page pixmap
        qpix = self.doc_model.render_page_pixmap(self.current_page, self.zoom)
        if qpix:
            painter.drawPixmap(int(origin.x()), int(origin.y()), qpix)
        else:
            painter.fillRect(page_rect, Qt.white)

        # Draw border around page
        painter.setPen(QPen(QColor("#404040"), 1))
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(page_rect)

        # Highlight search matches if any
        # (Rendered by search dialog if active)

        # Draw text selection boxes (semi-transparent blue/accent)
        if self._selected_words:
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(52, 152, 219, 90)) # Selection tint
            for w_item in self._selected_words:
                s_rect = self._pdf_to_screen_rect(w_item[:4])
                painter.drawRect(s_rect)

        # Draw selection rectangle while dragging
        if self._drag_start_screen and self._drag_current_screen:
            drag_box = QRectF(self._drag_start_screen, self._drag_current_screen).normalized()
            
            if self.active_tool == "rectangle":
                pen = QPen(QColor(self.active_color_hex), 2, Qt.DashLine)
                painter.setPen(pen)
                painter.setBrush(QColor(int(self.active_color_rgb[0]*255), 
                                        int(self.active_color_rgb[1]*255), 
                                        int(self.active_color_rgb[2]*255), 40))
                painter.drawRect(drag_box)
            elif self.active_tool in ("highlight", "underline", "strikeout", "select"):
                painter.setPen(QPen(QColor(52, 152, 219, 180), 1, Qt.DashLine))
                painter.setBrush(QColor(52, 152, 219, 40))
                painter.drawRect(drag_box)

        # Draw live ink strokes while drawing
        if self._ink_current_stroke and len(self._ink_current_stroke) > 1:
            pen = QPen(QColor(self.active_color_hex), self.pen_width * self.zoom, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            path = QPainterPath()
            p0 = self._ink_current_stroke[0]
            path.moveTo(origin.x() + p0[0] * self.zoom, origin.y() + p0[1] * self.zoom)
            for pt in self._ink_current_stroke[1:]:
                path.lineTo(origin.x() + pt[0] * self.zoom, origin.y() + pt[1] * self.zoom)
            painter.drawPath(path)

        # Draw indicator outline for selected annotation
        if self._selected_annot_id:
            annots = self.doc_model.get_annotations(self.current_page)
            for a in annots:
                if a["id"] == self._selected_annot_id:
                    s_rect = self._pdf_to_screen_rect(a["rect"]).adjusted(-2, -2, 2, 2)
                    painter.setPen(QPen(QColor("#E95420"), 2, Qt.DashLine))
                    painter.setBrush(Qt.NoBrush)
                    painter.drawRect(s_rect)
                    break

    # ==================== MOUSE EVENTS ====================

    def mousePressEvent(self, event: QMouseEvent):
        if not self.doc_model.is_open:
            return

        if event.button() == Qt.LeftButton:
            self._is_mouse_pressed = True
            pos = event.pos()
            self._drag_start_screen = QPointF(pos)
            self._drag_current_screen = QPointF(pos)
            pdf_pt = self._screen_to_pdf_point(self._drag_start_screen)

            if self.active_tool == "hand":
                self.setCursor(Qt.ClosedHandCursor)
                self._pan_start_pos = pos

            elif self.active_tool == "pen":
                self._ink_current_stroke = [(pdf_pt.x(), pdf_pt.y())]

            elif self.active_tool == "note":
                # Drop note on click
                self._create_sticky_note(pdf_pt)
                self._is_mouse_pressed = False

            elif self.active_tool == "freetext":
                # Create text box on click
                self._create_freetext(pdf_pt)
                self._is_mouse_pressed = False

            elif self.active_tool in ("eraser", "delete"):
                self._erase_annotation_at(pdf_pt)
                self._is_mouse_pressed = False

            elif self.active_tool == "select":
                # Check if user clicked an existing annotation
                clicked_annot = self._find_annot_at(pdf_pt)
                if clicked_annot:
                    self._selected_annot_id = clicked_annot["id"]
                    self.annotation_selected.emit(clicked_annot)
                    self.update()
                else:
                    self._selected_annot_id = None
                    self._clear_selection()
                    self.update()

        elif event.button() == Qt.RightButton:
            # Context menu
            pdf_pt = self._screen_to_pdf_point(event.pos())
            annot = self._find_annot_at(pdf_pt)
            self._show_context_menu(event.pos(), annot)

    def mouseMoveEvent(self, event: QMouseEvent):
        if not self.doc_model.is_open:
            return

        pos = event.pos()
        pdf_pt = self._screen_to_pdf_point(pos)

        # Pan tool drag
        if self.active_tool == "hand" and self._is_mouse_pressed and self._pan_start_pos:
            delta = pos - self._pan_start_pos
            self._pan_start_pos = pos
            scroll_area = self.parent()
            while scroll_area and not isinstance(scroll_area, QScrollArea):
                scroll_area = scroll_area.parent()
            if scroll_area:
                scroll_area.horizontalScrollBar().setValue(scroll_area.horizontalScrollBar().value() - delta.x())
                scroll_area.verticalScrollBar().setValue(scroll_area.verticalScrollBar().value() - delta.y())
            return

        # Active dragging for text markup or shapes
        if self._is_mouse_pressed:
            self._drag_current_screen = QPointF(pos)

            if self.active_tool == "pen":
                self._ink_current_stroke.append((pdf_pt.x(), pdf_pt.y()))
                self.update()

            elif self.active_tool in ("select", "highlight", "underline", "strikeout"):
                # Detect words overlapping drag area
                drag_box = QRectF(self._drag_start_screen, self._drag_current_screen).normalized()
                pdf_box = pymupdf.Rect(
                    self._screen_to_pdf_point(drag_box.topLeft()).x(),
                    self._screen_to_pdf_point(drag_box.topLeft()).y(),
                    self._screen_to_pdf_point(drag_box.bottomRight()).x(),
                    self._screen_to_pdf_point(drag_box.bottomRight()).y()
                )
                words = self.doc_model.get_words(self.current_page)
                self._selected_words = [w for w in words if pymupdf.Rect(w[:4]).intersects(pdf_box)]
                self.update()

            elif self.active_tool == "rectangle":
                self.update()

        else:
            # Hover detection for tooltips on annotations
            annot = self._find_annot_at(pdf_pt)
            if annot:
                tip = f"<b>{annot.get('type_name')}</b> by {annot.get('author') or 'Reviewer'}"
                if annot.get("content"):
                    tip += f"<br>{annot.get('content')}"
                QToolTip.showText(self.mapToGlobal(pos), tip, self)
            else:
                QToolTip.hideText()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if not self.doc_model.is_open or not self._is_mouse_pressed:
            return

        self._is_mouse_pressed = False
        pos = event.pos()
        self._drag_current_screen = QPointF(pos)

        if self.active_tool == "hand":
            self.setCursor(Qt.OpenHandCursor)
            return

        if self.active_tool == "pen":
            if len(self._ink_current_stroke) > 1:
                annot_id = self.doc_model.add_ink(
                    self.current_page,
                    [self._ink_current_stroke],
                    color=self.active_color_rgb,
                    width=self.pen_width
                )
                if annot_id:
                    self.annotation_added.emit(self.current_page, annot_id)
            self._ink_current_stroke.clear()
            self.update()

        elif self.active_tool == "rectangle":
            if self._drag_start_screen:
                p1 = self._screen_to_pdf_point(self._drag_start_screen)
                p2 = self._screen_to_pdf_point(self._drag_current_screen)
                rx0, rx1 = min(p1.x(), p2.x()), max(p1.x(), p2.x())
                ry0, ry1 = min(p1.y(), p2.y()), max(p1.y(), p2.y())
                if (rx1 - rx0) > 5 and (ry1 - ry0) > 5:
                    annot_id = self.doc_model.add_rect(
                        self.current_page,
                        (rx0, ry0, rx1, ry1),
                        color=self.active_color_rgb,
                        width=2.0
                    )
                    if annot_id:
                        self.annotation_added.emit(self.current_page, annot_id)
            self._drag_start_screen = None
            self._drag_current_screen = None
            self.update()

        elif self.active_tool in ("highlight", "underline", "strikeout"):
            # Apply markup to selected words
            if self._selected_words:
                self._apply_text_markup(self.active_tool, self._selected_words)
            self._clear_selection()
            self.update()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in (Qt.Key_Delete, Qt.Key_Backspace):
            if self._selected_annot_id:
                self.doc_model.delete_annotation(self.current_page, self._selected_annot_id)
                self.annotation_deleted.emit(self.current_page, self._selected_annot_id)
                self._selected_annot_id = None
                self.update()
        elif event.key() == Qt.Key_Escape:
            self._clear_selection()
            self._selected_annot_id = None
            self.update()
        else:
            super().keyPressEvent(event)

    # ==================== ANNOTATION HELPERS ====================

    def _find_annot_at(self, pdf_pt: QPointF) -> Optional[Dict[str, Any]]:
        annots = self.doc_model.get_annotations(self.current_page)
        pt = pymupdf.Point(pdf_pt.x(), pdf_pt.y())
        for a in reversed(annots): # top-most first
            rect = pymupdf.Rect(*a["rect"])
            # Add small tolerance around small icons
            if rect.width < 15 or rect.height < 15:
                rect.x0 -= 5
                rect.y0 -= 5
                rect.x1 += 5
                rect.y1 += 5
            if pt in rect:
                return a
        return None

    def _erase_annotation_at(self, pdf_pt: QPointF):
        annot = self._find_annot_at(pdf_pt)
        if annot:
            self.doc_model.delete_annotation(self.current_page, annot["id"])
            self.annotation_deleted.emit(self.current_page, annot["id"])
            self.status_message.emit("Annotation deleted.")
            self.update()

    def _create_sticky_note(self, pdf_pt: QPointF):
        dialog = CommentDialog(self, title="New Reviewer Sticky Note", header="Add Sticky Note Comment")
        if dialog.exec_() == QDialog.Accepted:
            text = dialog.get_text()
            if text:
                annot_id = self.doc_model.add_sticky_note(
                    self.current_page,
                    (pdf_pt.x(), pdf_pt.y()),
                    text,
                    color=self.active_color_rgb
                )
                if annot_id:
                    self.annotation_added.emit(self.current_page, annot_id)
                    self.status_message.emit("Sticky note placed.")
                    self.update()

    def _create_freetext(self, pdf_pt: QPointF):
        dialog = CommentDialog(self, title="New Margin Text Box", header="Add Margin Note")
        if dialog.exec_() == QDialog.Accepted:
            text = dialog.get_text()
            if text:
                # Estimate box width/height based on text length
                lines = text.split("\n")
                box_w = max(120, max(len(l) for l in lines) * 7 + 16)
                box_h = max(30, len(lines) * 16 + 10)
                rect = (pdf_pt.x(), pdf_pt.y(), pdf_pt.x() + box_w, pdf_pt.y() + box_h)
                
                annot_id = self.doc_model.add_freetext(
                    self.current_page,
                    rect,
                    text
                )
                if annot_id:
                    self.annotation_added.emit(self.current_page, annot_id)
                    self.status_message.emit("Text box added.")
                    self.update()

    def _apply_text_markup(self, markup_type: str, words: List[Tuple]):
        """Group words into line rects and create highlight/underline/strikeout."""
        lines: Dict[Tuple[int, int], List[Tuple]] = {}
        for w in words:
            key = (w[5], w[6])
            if key not in lines:
                lines[key] = []
            lines[key].append(w)

        rects = []
        for key, lwords in lines.items():
            r = pymupdf.Rect(lwords[0][:4])
            for w in lwords[1:]:
                r.include_rect(pymupdf.Rect(w[:4]))
            rects.append(r)

        quoted_text = " ".join(w[4] for w in words)
        annot_id = None
        
        if markup_type == "highlight":
            annot_id = self.doc_model.add_highlight(
                self.current_page, rects, color=self.active_color_rgb, quoted_text=quoted_text
            )
        elif markup_type == "underline":
            annot_id = self.doc_model.add_underline(
                self.current_page, rects, color=self.active_color_rgb, quoted_text=quoted_text
            )
        elif markup_type == "strikeout":
            annot_id = self.doc_model.add_strikeout(
                self.current_page, rects, color=self.active_color_rgb, quoted_text=quoted_text
            )

        if annot_id:
            self.annotation_added.emit(self.current_page, annot_id)
            self.status_message.emit(f"Added {markup_type}: '{quoted_text[:40]}...'")

    def _show_context_menu(self, pos: QPoint, annot: Optional[Dict[str, Any]]):
        menu = QMenu(self)
        if annot:
            act_edit = menu.addAction("Edit Review Comment...")
            act_copy = menu.addAction("Copy Comment / Text")
            act_del = menu.addAction("Delete Annotation")
            
            selected = menu.exec_(self.mapToGlobal(pos))
            if selected == act_edit:
                dialog = CommentDialog(self, title="Edit Comment", initial_text=annot.get("content", ""))
                if dialog.exec_() == QDialog.Accepted:
                    new_text = dialog.get_text()
                    self.doc_model.update_annotation_content(self.current_page, annot["id"], new_text)
                    self.annotation_added.emit(self.current_page, annot["id"])
                    self.update()
            elif selected == act_copy:
                from PyQt5.QtWidgets import QApplication
                QApplication.clipboard().setText(annot.get("content", ""))
            elif selected == act_del:
                self.doc_model.delete_annotation(self.current_page, annot["id"])
                self.annotation_deleted.emit(self.current_page, annot["id"])
                self.update()
        else:
            act_note = menu.addAction("Add Sticky Note here")
            act_text = menu.addAction("Add Text Box here")
            selected = menu.exec_(self.mapToGlobal(pos))
            pdf_pt = self._screen_to_pdf_point(pos)
            if selected == act_note:
                self._create_sticky_note(pdf_pt)
            elif selected == act_text:
                self._create_freetext(pdf_pt)
