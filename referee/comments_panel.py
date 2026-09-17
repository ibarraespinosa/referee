"""
Review Comments & Annotations Sidebar for ReviewerPDF.
Provides a comprehensive overview of all reviewer marks, quotes, and notes,
enables fast jumping to annotations, and supports 1-click export to Markdown/TXT.
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem, 
    QPushButton, QLineEdit, QLabel, QMenu, QMessageBox, QFileDialog, QApplication
)
from PyQt5.QtGui import QColor, QBrush, QFont, QIcon
from PyQt5.QtCore import Qt, pyqtSignal
from .pdf_canvas import CommentDialog
from .review_exporter import generate_markdown_report, generate_plain_text_report
from .icons import get_icon

class CommentsPanel(QWidget):
    annotation_selected = pyqtSignal(int, str)  # page_idx, annot_id
    annotation_updated = pyqtSignal()

    def __init__(self, doc_model, parent=None):
        super().__init__(parent)
        self.doc_model = doc_model
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(6)
        
        # Header with Title and Count
        header_layout = QHBoxLayout()
        self.lbl_title = QLabel("Review Comments (0)")
        self.lbl_title.setStyleSheet("font-weight: bold; color: #e0e0e0; font-size: 13px;")
        header_layout.addWidget(self.lbl_title)
        
        header_layout.addStretch()
        
        # Export button
        self.btn_export = QPushButton("Export...")
        self.btn_export.setIcon(get_icon("export"))
        self.btn_export.setToolTip("Export review report to Markdown or Text")
        self.btn_export.clicked.connect(self._on_export_clicked)
        header_layout.addWidget(self.btn_export)
        layout.addLayout(header_layout)
        
        # Filter input
        self.filter_edit = QLineEdit(self)
        self.filter_edit.setPlaceholderText("Filter notes or text...")
        self.filter_edit.textChanged.connect(self._apply_filter)
        layout.addWidget(self.filter_edit)
        
        # Tree widget listing annotations grouped by page
        self.tree = QTreeWidget(self)
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(16)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._on_context_menu)
        self.tree.itemClicked.connect(self._on_item_clicked)
        self.tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.tree)

    def reload_comments(self):
        """Re-populate tree with all annotations from document."""
        self.tree.clear()
        if not self.doc_model.is_open:
            self.lbl_title.setText("Review Comments (0)")
            return
        
        all_annots = self.doc_model.get_all_annotations()
        self.lbl_title.setText(f"Review Comments ({len(all_annots)})")
        
        if not all_annots:
            placeholder = QTreeWidgetItem(self.tree, ["No annotations yet."])
            placeholder.setFlags(Qt.NoItemFlags)
            return

        # Group by page
        pages: dict = {}
        for a in all_annots:
            p = a.get("page", 0)
            if p not in pages:
                pages[p] = []
            pages[p].append(a)
            
        for page_idx in sorted(pages.keys()):
            page_annots = pages[page_idx]
            page_item = QTreeWidgetItem(self.tree, [f"Page {page_idx + 1} ({len(page_annots)})"])
            page_item.setFont(0, QFont("Ubuntu", 10, QFont.Bold))
            page_item.setForeground(0, QBrush(QColor("#E95420")))
            page_item.setExpanded(True)
            
            for a in page_annots:
                type_name = a.get("type_name", "Mark")
                content = a.get("content", "").strip()
                subject = a.get("subject", "")
                
                # Preview text
                preview = ""
                if subject and ":" in subject:
                    preview = subject.split(":", 1)[1].strip()
                elif content:
                    preview = content
                else:
                    preview = type_name
                    
                if len(preview) > 45:
                    preview = preview[:42] + "..."
                    
                item_text = f"[{type_name}] {preview}"
                child_item = QTreeWidgetItem(page_item, [item_text])
                child_item.setData(0, Qt.UserRole, a)
                
                # Color indicator
                if a.get("color"):
                    c = a["color"]
                    if len(c) == 3:
                        qc = QColor(int(c[0]*255), int(c[1]*255), int(c[2]*255))
                        child_item.setForeground(0, QBrush(qc))
                        
                # Tooltip with full detail
                detail = f"Type: {type_name}\nAuthor: {a.get('author') or 'Reviewer'}"
                if content:
                    detail += f"\nComment: {content}"
                if subject:
                    detail += f"\nQuote: {subject}"
                child_item.setToolTip(0, detail)

        self._apply_filter(self.filter_edit.text())

    def _apply_filter(self, text: str):
        query = text.strip().lower()
        for i in range(self.tree.topLevelItemCount()):
            page_item = self.tree.topLevelItem(i)
            page_visible = False
            for j in range(page_item.childCount()):
                child = page_item.child(j)
                annot = child.data(0, Qt.UserRole) or {}
                content = (annot.get("content") or "").lower()
                subject = (annot.get("subject") or "").lower()
                type_name = (annot.get("type_name") or "").lower()
                
                matches = (not query) or (query in content) or (query in subject) or (query in type_name)
                child.setHidden(not matches)
                if matches:
                    page_visible = True
            page_item.setHidden(not page_visible and bool(query))

    def _on_item_clicked(self, item: QTreeWidgetItem, column: int):
        annot = item.data(0, Qt.UserRole)
        if annot:
            self.annotation_selected.emit(annot["page"], annot["id"])

    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        annot = item.data(0, Qt.UserRole)
        if annot:
            self._edit_annotation(annot)

    def _on_context_menu(self, pos):
        item = self.tree.itemAt(pos)
        if not item:
            return
        annot = item.data(0, Qt.UserRole)
        if not annot:
            return
            
        menu = QMenu(self)
        act_jump = menu.addAction("Jump to Annotation")
        act_edit = menu.addAction("Edit Review Comment...")
        act_copy = menu.addAction("Copy Comment Text")
        menu.addSeparator()
        act_del = menu.addAction("Delete Annotation")
        
        selected = menu.exec_(self.tree.viewport().mapToGlobal(pos))
        if selected == act_jump:
            self.annotation_selected.emit(annot["page"], annot["id"])
        elif selected == act_edit:
            self._edit_annotation(annot)
        elif selected == act_copy:
            text = annot.get("content") or annot.get("subject") or ""
            QApplication.clipboard().setText(text)
        elif selected == act_del:
            self.doc_model.delete_annotation(annot["page"], annot["id"])
            self.annotation_updated.emit()
            self.reload_comments()

    def _edit_annotation(self, annot: dict):
        dialog = CommentDialog(self, title="Edit Review Comment", initial_text=annot.get("content", ""))
        if dialog.exec_() == CommentDialog.Accepted:
            new_text = dialog.get_text()
            self.doc_model.update_annotation_content(annot["page"], annot["id"], new_text)
            self.annotation_updated.emit()
            self.reload_comments()

    def _on_export_clicked(self):
        if not self.doc_model.is_open:
            QMessageBox.information(self, "Export", "Please open a PDF document first.")
            return

        menu = QMenu(self)
        act_md = menu.addAction("Export as Markdown (.md)...")
        act_txt = menu.addAction("Export as Plain Text (.txt)...")
        act_clip = menu.addAction("Copy Review Summary to Clipboard")
        
        chosen = menu.exec_(self.btn_export.mapToGlobal(self.btn_export.rect().bottomLeft()))
        if chosen == act_md:
            path, _ = QFileDialog.getSaveFileName(self, "Export Review to Markdown", f"{self.doc_model.filename}_review.md", "Markdown Files (*.md)")
            if path:
                md_content = generate_markdown_report(self.doc_model)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(md_content)
                QMessageBox.information(self, "Export Successful", f"Review notes saved to:\n{path}")
        elif chosen == act_txt:
            path, _ = QFileDialog.getSaveFileName(self, "Export Review to Text", f"{self.doc_model.filename}_review.txt", "Text Files (*.txt)")
            if path:
                txt_content = generate_plain_text_report(self.doc_model)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(txt_content)
                QMessageBox.information(self, "Export Successful", f"Review summary saved to:\n{path}")
        elif chosen == act_clip:
            txt_content = generate_plain_text_report(self.doc_model)
            QApplication.clipboard().setText(txt_content)
            QMessageBox.information(self, "Copied", "Review summary copied to clipboard! Ready to paste into review forms.")
