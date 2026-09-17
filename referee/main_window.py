"""
Main Application Window for ReviewerPDF.
Acrobat-inspired layout with reviewer ribbon, sidebars, search, and native PDF saving.
"""
import os
import sys
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter, 
    QScrollArea, QToolBar, QAction, QActionGroup, QFileDialog, 
    QMessageBox, QComboBox, QLineEdit, QLabel, QSpinBox, 
    QTabWidget, QToolButton, QMenu, QStatusBar, QDialog, QTextEdit
)
from PyQt5.QtGui import QIcon, QKeySequence, QDragEnterEvent, QDropEvent, QColor, QPixmap
from PyQt5.QtCore import Qt, QSize, QSettings

from .pdf_document import PDFDocument
from .pdf_canvas import PDFCanvas
from .thumbnail_view import ThumbnailView
from .comments_panel import CommentsPanel
from .search_dialog import SearchBar
from .styles import DARK_THEME_QSS, REVIEWER_COLORS
from .icons import get_icon
from .review_exporter import generate_markdown_report, generate_plain_text_report

class MainWindow(QMainWindow):
    def __init__(self, initial_pdf: str = None):
        super().__init__()
        self.setWindowTitle("ReviewerPDF - Document Annotation & Review Editor")
        self.resize(1300, 850)
        
        self.doc_model = PDFDocument()
        self.settings = QSettings("OpenSourceReviewer", "ReviewerPDF")
        
        # Load saved reviewer name
        saved_name = self.settings.value("reviewer_name", "Reviewer 1")
        self.doc_model.reviewer_name = saved_name
        
        # Apply dark theme
        self.setStyleSheet(DARK_THEME_QSS)
        
        # Setup widgets and toolbars
        self._init_ui()
        self._init_menus()
        self._init_shortcuts()
        
        # Accept drag and drop
        self.setAcceptDrops(True)
        
        if initial_pdf and os.path.exists(initial_pdf):
            self.open_file(initial_pdf)
        else:
            self._update_ui_state()

    def _init_ui(self):
        # Central widget with horizontal splitter
        self.splitter = QSplitter(Qt.Horizontal, self)
        self.setCentralWidget(self.splitter)
        
        # Left Sidebar (Tabs for Thumbnails and Comments)
        self.sidebar_tabs = QTabWidget(self)
        self.sidebar_tabs.setMinimumWidth(230)
        self.sidebar_tabs.setMaximumWidth(400)
        
        self.thumbnails_view = ThumbnailView(self.doc_model, self)
        self.thumbnails_view.page_selected.connect(self.go_to_page)
        self.sidebar_tabs.addTab(self.thumbnails_view, "Pages")
        
        self.comments_panel = CommentsPanel(self.doc_model, self)
        self.comments_panel.annotation_selected.connect(self._on_comment_selected)
        self.comments_panel.annotation_updated.connect(self._on_comment_updated)
        self.sidebar_tabs.addTab(self.comments_panel, "Review Notes")
        
        self.splitter.addWidget(self.sidebar_tabs)
        
        # Right / Center Area: Canvas in ScrollArea with search overlay
        center_container = QWidget(self)
        center_layout = QVBoxLayout(center_container)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(0)
        
        # Search bar widget (initially hidden)
        self.search_bar = SearchBar(self.doc_model, self)
        self.search_bar.find_next.connect(self._on_search_match)
        self.search_bar.hide()
        center_layout.addWidget(self.search_bar)
        
        # Scroll Area for PDF Canvas
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setAlignment(Qt.AlignCenter)
        self.scroll_area.setWidgetResizable(False)
        
        self.canvas = PDFCanvas(self.doc_model, self)
        self.canvas.annotation_added.connect(self._on_annotation_added)
        self.canvas.annotation_deleted.connect(self._on_annotation_deleted)
        self.canvas.zoom_changed.connect(self._on_zoom_changed)
        self.canvas.status_message.connect(self._set_status)
        
        self.scroll_area.setWidget(self.canvas)
        center_layout.addWidget(self.scroll_area)
        
        self.splitter.addWidget(center_container)
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setSizes([260, 1040])
        
        # Build Toolbars
        self._init_main_toolbar()
        self._init_annotation_ribbon()
        
        # Status Bar
        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)
        self.lbl_status_page = QLabel("Page 0 of 0", self)
        self.lbl_status_zoom = QLabel("125%", self)
        self.lbl_status_msg = QLabel("Ready", self)
        self.status_bar.addWidget(self.lbl_status_msg, 1)
        self.status_bar.addPermanentWidget(self.lbl_status_page)
        self.status_bar.addPermanentWidget(self.lbl_status_zoom)

    def _init_main_toolbar(self):
        self.main_toolbar = QToolBar("Main Controls", self)
        self.main_toolbar.setIconSize(QSize(20, 20))
        self.main_toolbar.setMovable(False)
        self.addToolBar(Qt.TopToolBarArea, self.main_toolbar)
        
        # File Actions
        self.act_open = self.main_toolbar.addAction(get_icon("open"), "Open PDF (Ctrl+O)", self.open_file_dialog)
        self.act_save = self.main_toolbar.addAction(get_icon("save"), "Save PDF (Ctrl+S)", self.save_file)
        self.act_save_as = self.main_toolbar.addAction(get_icon("save"), "Save As... (Ctrl+Shift+S)", self.save_file_as)
        
        self.main_toolbar.addSeparator()
        
        # Undo / Redo
        self.act_undo = self.main_toolbar.addAction(get_icon("undo"), "Undo (Ctrl+Z)", self._undo)
        self.act_redo = self.main_toolbar.addAction(get_icon("redo"), "Redo (Ctrl+Y)", self._redo)
        
        self.main_toolbar.addSeparator()
        
        # Page Navigation
        self.act_first = self.main_toolbar.addAction(get_icon("first"), "First Page (Home)", lambda: self.go_to_page(0))
        self.act_prev = self.main_toolbar.addAction(get_icon("prev"), "Previous Page (PgUp)", lambda: self.go_to_page(self.canvas.current_page - 1))
        
        self.spin_page = QSpinBox(self)
        self.spin_page.setMinimum(1)
        self.spin_page.setMaximum(1)
        self.spin_page.valueChanged.connect(lambda val: self.go_to_page(val - 1))
        self.main_toolbar.addWidget(self.spin_page)
        
        self.lbl_page_total = QLabel(" / 0", self)
        self.lbl_page_total.setStyleSheet("margin-right: 6px; color: #b0b0b0;")
        self.main_toolbar.addWidget(self.lbl_page_total)
        
        self.act_next = self.main_toolbar.addAction(get_icon("next"), "Next Page (PgDn)", lambda: self.go_to_page(self.canvas.current_page + 1))
        self.act_last = self.main_toolbar.addAction(get_icon("last"), "Last Page (End)", lambda: self.go_to_page(self.doc_model.page_count - 1))
        
        self.main_toolbar.addSeparator()
        
        # Zoom Controls
        self.act_zoom_out = self.main_toolbar.addAction(get_icon("zoom_out"), "Zoom Out (Ctrl+-)", lambda: self.canvas.set_zoom(self.canvas.zoom - 0.15))
        
        self.combo_zoom = QComboBox(self)
        self.combo_zoom.addItems(["50%", "75%", "100%", "125%", "150%", "200%", "300%"])
        self.combo_zoom.setCurrentText("125%")
        self.combo_zoom.currentTextChanged.connect(self._on_combo_zoom_changed)
        self.main_toolbar.addWidget(self.combo_zoom)
        
        self.act_zoom_in = self.main_toolbar.addAction(get_icon("zoom_in"), "Zoom In (Ctrl++)", lambda: self.canvas.set_zoom(self.canvas.zoom + 0.15))
        self.act_fit_width = self.main_toolbar.addAction(get_icon("fit_width"), "Fit Width", self._fit_width)
        self.act_fit_page = self.main_toolbar.addAction(get_icon("fit_page"), "Fit Page (Ctrl+0)", self._fit_page)
        
        self.main_toolbar.addSeparator()
        
        # Search & Sidebar Toggles
        self.act_search = self.main_toolbar.addAction(get_icon("search"), "Find in Document (Ctrl+F)", self._toggle_search)
        self.act_toggle_sidebar = self.main_toolbar.addAction(get_icon("sidebar"), "Toggle Sidebar (F9)", self._toggle_sidebar)

    def _init_annotation_ribbon(self):
        self.ribbon = QToolBar("Review & Annotation Ribbon", self)
        self.ribbon.setIconSize(QSize(20, 20))
        self.ribbon.setMovable(False)
        self.addToolBar(Qt.TopToolBarArea, self.ribbon)
        
        # Tool Action Group (Exclusive selection)
        self.tool_group = QActionGroup(self)
        self.tool_group.setExclusive(True)
        
        def add_tool_action(icon_name, text, tool_id, shortcut=None):
            act = QAction(get_icon(icon_name), text, self)
            act.setCheckable(True)
            if shortcut:
                act.setShortcut(QKeySequence(shortcut))
            act.triggered.connect(lambda: self.canvas.set_tool(tool_id))
            self.tool_group.addAction(act)
            self.ribbon.addAction(act)
            return act

        self.act_tool_select = add_tool_action("select", "Select Text / Marks (V)", "select", "V")
        self.act_tool_select.setChecked(True)
        self.act_tool_hand = add_tool_action("hand", "Hand / Pan Page (H)", "hand")
        
        self.ribbon.addSeparator()
        
        # Markup Tools
        self.act_tool_hl = add_tool_action("highlight", "Highlight Text (Shift+H)", "highlight", "Shift+H")
        self.act_tool_under = add_tool_action("underline", "Underline Text (U)", "underline", "U")
        self.act_tool_strike = add_tool_action("strikeout", "Strikeout Text (S)", "strikeout", "S")
        
        self.ribbon.addSeparator()
        
        # Notes & Drawing
        self.act_tool_note = add_tool_action("note", "Sticky Note Comment (N)", "note", "N")
        self.act_tool_freetext = add_tool_action("freetext", "Margin Text Box (T)", "freetext", "T")
        self.act_tool_pen = add_tool_action("pen", "Freehand Pen (P)", "pen", "P")
        self.act_tool_rect = add_tool_action("rectangle", "Draw Box / Rectangle (R)", "rectangle", "R")
        self.act_tool_eraser = add_tool_action("eraser", "Erase / Delete Annotation", "eraser")
        
        self.ribbon.addSeparator()
        
        # Quick Color Picker Swatches
        lbl_colors = QLabel("Color: ", self)
        lbl_colors.setStyleSheet("color: #b0b0b0; font-size: 11px;")
        self.ribbon.addWidget(lbl_colors)
        
        self.color_buttons = []
        for name, (hex_code, rgb_tuple) in REVIEWER_COLORS.items():
            btn = QToolButton(self)
            btn.setToolTip(f"{name} markup")
            btn.setFixedSize(22, 22)
            btn.setStyleSheet(f"""
                QToolButton {{
                    background-color: {hex_code};
                    border: 2px solid #333333;
                    border-radius: 11px;
                }}
                QToolButton:hover {{
                    border: 2px solid #ffffff;
                }}
            """)
            btn.clicked.connect(lambda checked, h=hex_code, r=rgb_tuple: self._set_active_color(h, r))
            self.ribbon.addWidget(btn)
            self.color_buttons.append(btn)
            
        self.ribbon.addSeparator()
        
        # Reviewer Identity
        lbl_reviewer = QLabel("Reviewer: ", self)
        lbl_reviewer.setStyleSheet("color: #b0b0b0; font-size: 11px;")
        self.ribbon.addWidget(lbl_reviewer)
        
        self.edit_reviewer = QLineEdit(self.doc_model.reviewer_name, self)
        self.edit_reviewer.setToolTip("Your reviewer tag attached to annotations")
        self.edit_reviewer.setMaximumWidth(120)
        self.edit_reviewer.textChanged.connect(self._on_reviewer_name_changed)
        self.ribbon.addWidget(self.edit_reviewer)
        
        # Spacer & 1-Click Export Report
        spacer = QWidget()
        spacer.setSizePolicy(spacer.sizePolicy().Expanding, spacer.sizePolicy().Preferred)
        self.ribbon.addWidget(spacer)
        
        btn_report = QToolButton(self)
        btn_report.setIcon(get_icon("export"))
        btn_report.setText(" Export Review...")
        btn_report.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        btn_report.setStyleSheet("background-color: #E95420; color: white; font-weight: bold; border-radius: 4px; padding: 4px 10px;")
        btn_report.clicked.connect(self.comments_panel._on_export_clicked)
        self.ribbon.addWidget(btn_report)

    def _init_menus(self):
        menubar = self.menuBar()
        
        # File Menu
        menu_file = menubar.addMenu("&File")
        menu_file.addAction(get_icon("open"), "&Open...", self.open_file_dialog, QKeySequence.Open)
        menu_file.addAction(get_icon("save"), "&Save", self.save_file, QKeySequence.Save)
        menu_file.addAction(get_icon("save"), "Save &As...", self.save_file_as, QKeySequence.SaveAs)
        menu_file.addSeparator()
        menu_file.addAction(get_icon("export"), "Export Review as &Markdown...", self._export_markdown)
        menu_file.addAction(get_icon("export"), "Export Review as &Text...", self._export_text)
        menu_file.addSeparator()
        menu_file.addAction("&Close", self.close_document, QKeySequence.Close)
        menu_file.addAction("&Quit", self.close, QKeySequence.Quit)
        
        # Edit Menu
        menu_edit = menubar.addMenu("&Edit")
        menu_edit.addAction(get_icon("undo"), "&Undo", self._undo, QKeySequence.Undo)
        menu_edit.addAction(get_icon("redo"), "&Redo", self._redo, QKeySequence.Redo)
        menu_edit.addSeparator()
        menu_edit.addAction(get_icon("search"), "&Find...", self._toggle_search, QKeySequence.Find)
        
        # View Menu
        menu_view = menubar.addMenu("&View")
        menu_view.addAction(get_icon("zoom_in"), "Zoom &In", lambda: self.canvas.set_zoom(self.canvas.zoom + 0.15), QKeySequence.ZoomIn)
        menu_view.addAction(get_icon("zoom_out"), "Zoom &Out", lambda: self.canvas.set_zoom(self.canvas.zoom - 0.15), QKeySequence.ZoomOut)
        menu_view.addAction(get_icon("fit_page"), "Fit &Page", self._fit_page, QKeySequence("Ctrl+0"))
        menu_view.addAction(get_icon("fit_width"), "Fit &Width", self._fit_width)
        menu_view.addSeparator()
        menu_view.addAction("Toggle &Sidebar", self._toggle_sidebar, QKeySequence("F9"))
        
        # Help Menu
        menu_help = menubar.addMenu("&Help")
        menu_help.addAction("&Keyboard Shortcuts", self._show_shortcuts)
        menu_help.addAction("&About ReviewerPDF", self._show_about)

    def _init_shortcuts(self):
        # Quick zoom shortcuts
        QAction("Fit Width", self, shortcut=QKeySequence("Ctrl+W"), triggered=self._fit_width)
        QAction("Page Down", self, shortcut=QKeySequence(Qt.Key_PageDown), triggered=lambda: self.go_to_page(self.canvas.current_page + 1))
        QAction("Page Up", self, shortcut=QKeySequence(Qt.Key_PageUp), triggered=lambda: self.go_to_page(self.canvas.current_page - 1))

    # ==================== FILE HANDLING ====================

    def open_file_dialog(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Open PDF Document", "", "PDF Files (*.pdf)")
        if filepath:
            self.open_file(filepath)

    def open_file(self, filepath: str):
        if self.doc_model.is_modified:
            resp = QMessageBox.question(
                self, "Unsaved Changes", "You have unsaved review marks. Do you want to save first?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
            )
            if resp == QMessageBox.Save:
                self.save_file()
            elif resp == QMessageBox.Cancel:
                return

        if self.doc_model.open(filepath):
            self.setWindowTitle(f"{self.doc_model.filename} - ReviewerPDF")
            self.spin_page.setMaximum(self.doc_model.page_count)
            self.lbl_page_total.setText(f" / {self.doc_model.page_count}")
            self.thumbnails_view.reload_thumbnails()
            self.comments_panel.reload_comments()
            self.go_to_page(0)
            self._fit_width()
            self._update_ui_state()
            self._set_status(f"Opened {self.doc_model.filename}")
        else:
            QMessageBox.critical(self, "Error", f"Failed to open PDF document:\n{filepath}")

    def save_file(self):
        if not self.doc_model.is_open:
            return
        if self.doc_model.save():
            self.setWindowTitle(f"{self.doc_model.filename} - ReviewerPDF")
            self._set_status("Document saved successfully with ISO 32000 annotations.")
            QMessageBox.information(self, "Saved", "Document and annotations saved successfully!")
        else:
            self.save_file_as()

    def save_file_as(self):
        if not self.doc_model.is_open:
            return
        filepath, _ = QFileDialog.getSaveFileName(self, "Save PDF Document As", f"reviewed_{self.doc_model.filename}", "PDF Files (*.pdf)")
        if filepath:
            if self.doc_model.save(filepath):
                self.setWindowTitle(f"{self.doc_model.filename} - ReviewerPDF")
                self._set_status(f"Saved copy to {filepath}")
                QMessageBox.information(self, "Saved", f"Review copy saved to:\n{filepath}")
            else:
                QMessageBox.critical(self, "Error", "Failed to save PDF.")

    def close_document(self):
        if self.doc_model.is_open:
            self.doc_model.close()
            self.canvas.update()
            self.thumbnails_view.reload_thumbnails()
            self.comments_panel.reload_comments()
            self.setWindowTitle("ReviewerPDF")
            self._update_ui_state()

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.toLocalFile().lower().endswith(".pdf"):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            local_path = url.toLocalFile()
            if local_path.lower().endswith(".pdf"):
                self.open_file(local_path)
                event.acceptProposedAction()
                return

    # ==================== NAVIGATION & ZOOM ====================

    def go_to_page(self, page_idx: int):
        if not self.doc_model.is_open:
            return
        clamped = max(0, min(page_idx, self.doc_model.page_count - 1))
        self.canvas.set_page(clamped)
        self.spin_page.blockSignals(True)
        self.spin_page.setValue(clamped + 1)
        self.spin_page.blockSignals(False)
        self.thumbnails_view.set_current_page(clamped)
        self.lbl_status_page.setText(f"Page {clamped + 1} of {self.doc_model.page_count}")

    def _fit_width(self):
        if not self.doc_model.is_open:
            return
        pw, _ = self.doc_model.get_page_size(self.canvas.current_page)
        if pw > 0:
            area_w = self.scroll_area.viewport().width() - 50
            zoom = max(0.4, area_w / pw)
            self.canvas.set_zoom(zoom)

    def _fit_page(self):
        if not self.doc_model.is_open:
            return
        pw, ph = self.doc_model.get_page_size(self.canvas.current_page)
        if pw > 0 and ph > 0:
            area_w = self.scroll_area.viewport().width() - 50
            area_h = self.scroll_area.viewport().height() - 50
            zoom = max(0.3, min(area_w / pw, area_h / ph))
            self.canvas.set_zoom(zoom)

    def _on_zoom_changed(self, zoom: float):
        pct = f"{int(zoom * 100)}%"
        self.combo_zoom.blockSignals(True)
        self.combo_zoom.setCurrentText(pct)
        self.combo_zoom.blockSignals(False)
        self.lbl_status_zoom.setText(pct)

    def _on_combo_zoom_changed(self, text: str):
        try:
            val = float(text.replace("%", "").strip()) / 100.0
            self.canvas.set_zoom(val)
        except ValueError:
            pass

    # ==================== ANNOTATIONS & SIDEBAR ====================

    def _set_active_color(self, hex_code: str, rgb_tuple: tuple):
        self.canvas.set_color(hex_code, rgb_tuple)
        self._set_status(f"Selected color: {hex_code}")

    def _on_reviewer_name_changed(self, text: str):
        name = text.strip() or "Reviewer"
        self.doc_model.reviewer_name = name
        self.settings.setValue("reviewer_name", name)

    def _on_annotation_added(self, page_idx: int, annot_id: str):
        self.comments_panel.reload_comments()
        self.thumbnails_view.reload_thumbnails()
        self.setWindowTitle(f"*{self.doc_model.filename} - ReviewerPDF")

    def _on_annotation_deleted(self, page_idx: int, annot_id: str):
        self.comments_panel.reload_comments()
        self.thumbnails_view.reload_thumbnails()
        self.setWindowTitle(f"*{self.doc_model.filename} - ReviewerPDF")

    def _on_comment_selected(self, page_idx: int, annot_id: str):
        self.go_to_page(page_idx)
        self.canvas._selected_annot_id = annot_id
        self.canvas.update()

    def _on_comment_updated(self):
        self.canvas.update()
        self.setWindowTitle(f"*{self.doc_model.filename} - ReviewerPDF")

    def _undo(self):
        page = self.doc_model.undo()
        if page is not None:
            self.canvas.update()
            self.comments_panel.reload_comments()
            self._set_status("Undid last annotation.")

    def _redo(self):
        # Could be implemented if redo stack has re-addition
        pass

    def _toggle_sidebar(self):
        self.sidebar_tabs.setVisible(not self.sidebar_tabs.isVisible())

    def _toggle_search(self):
        if self.search_bar.isVisible():
            self.search_bar.hide_bar()
        else:
            self.search_bar.show_and_focus()

    def _on_search_match(self, match: dict):
        self.go_to_page(match["page"])
        # Centering on match rect could be added
        self._set_status(f"Found match on page {match['page'] + 1}")

    # ==================== EXPORT REPORTS ====================

    def _export_markdown(self):
        if not self.doc_model.is_open:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export Review to Markdown", f"{self.doc_model.filename}_review.md", "Markdown (*.md)")
        if path:
            md = generate_markdown_report(self.doc_model)
            with open(path, "w", encoding="utf-8") as f:
                f.write(md)
            QMessageBox.information(self, "Exported", f"Saved review notes to:\n{path}")

    def _export_text(self):
        if not self.doc_model.is_open:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export Review to Text", f"{self.doc_model.filename}_review.txt", "Text (*.txt)")
        if path:
            txt = generate_plain_text_report(self.doc_model)
            with open(path, "w", encoding="utf-8") as f:
                f.write(txt)
            QMessageBox.information(self, "Exported", f"Saved review notes to:\n{path}")

    # ==================== HELP & STATUS ====================

    def _show_shortcuts(self):
        msg = """
<h3>ReviewerPDF Keyboard Shortcuts</h3>
<ul>
  <li><b>V</b>: Select / Pointer tool</li>
  <li><b>Shift + H</b>: Highlight tool (drag over text to highlight)</li>
  <li><b>U</b>: Underline tool</li>
  <li><b>S</b>: Strikeout tool</li>
  <li><b>N</b>: Sticky Note / Comment tool (click page to place)</li>
  <li><b>T</b>: Margin Text Box tool</li>
  <li><b>P</b>: Freehand Pen drawing tool</li>
  <li><b>R</b>: Rectangle / Box tool</li>
  <li><b>Delete / Backspace</b>: Delete selected annotation</li>
  <li><b>Ctrl + F</b>: Find text in document</li>
  <li><b>Ctrl + S</b>: Save PDF with ISO standard annotations</li>
  <li><b>Ctrl + Shift + S</b>: Save As...</li>
  <li><b>Ctrl + Z</b>: Undo annotation</li>
  <li><b>Ctrl + 0</b>: Fit Page</li>
  <li><b>F9</b>: Toggle left sidebar (Thumbnails & Review Notes)</li>
  <li><b>Page Up / Page Down</b>: Next / Previous page</li>
</ul>
        """
        QMessageBox.information(self, "Keyboard Shortcuts", msg)

    def _show_about(self):
        msg = """
<h3>ReviewerPDF 1.0.0</h3>
<p>An open-source, Acrobat-like PDF review and annotation editor tailored for reviewers on Ubuntu.</p>
<p><b>Features:</b>
<ul>
  <li>1-Click multi-color text highlights (Yellow, Green, Blue, Pink, Orange)</li>
  <li>Sticky notes, Underline, Strikeout, Freehand Pen, and Margin Text boxes</li>
  <li>Review Comments Panel with direct jump and inline editing</li>
  <li>1-Click Export to Markdown & Plain Text for OpenReview / HotCRP / EasyChair</li>
  <li>ISO 32000 standard annotations compatible with Adobe Acrobat & Evince</li>
</ul>
</p>
<p>Built with Python 3, PyQt5, and PyMuPDF.</p>
        """
        QMessageBox.about(self, "About ReviewerPDF", msg)

    def _set_status(self, msg: str):
        self.lbl_status_msg.setText(msg)

    def _update_ui_state(self):
        has_doc = self.doc_model.is_open
        self.act_save.setEnabled(has_doc)
        self.act_save_as.setEnabled(has_doc)
        self.act_undo.setEnabled(has_doc)
        self.act_first.setEnabled(has_doc)
        self.act_prev.setEnabled(has_doc)
        self.act_next.setEnabled(has_doc)
        self.act_last.setEnabled(has_doc)
        self.act_zoom_in.setEnabled(has_doc)
        self.act_zoom_out.setEnabled(has_doc)
        self.act_fit_width.setEnabled(has_doc)
        self.act_fit_page.setEnabled(has_doc)
        self.act_search.setEnabled(has_doc)
        self.spin_page.setEnabled(has_doc)
        self.combo_zoom.setEnabled(has_doc)
        self.ribbon.setEnabled(has_doc)

    def closeEvent(self, event):
        if self.doc_model.is_modified:
            resp = QMessageBox.question(
                self, "Unsaved Changes", "You have unsaved annotations. Do you want to save before closing?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
            )
            if resp == QMessageBox.Save:
                self.save_file()
                event.accept()
            elif resp == QMessageBox.Discard:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
