"""
Thumbnail Sidebar View for ReviewerPDF.
Displays preview miniatures of all document pages for rapid visual navigation.
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QListWidgetItem, QLabel
)
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt, QSize, pyqtSignal

class ThumbnailView(QWidget):
    page_selected = pyqtSignal(int)

    def __init__(self, doc_model, parent=None):
        super().__init__(parent)
        self.doc_model = doc_model
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        
        header = QLabel("Pages")
        header.setStyleSheet("font-weight: bold; color: #b0b0b0; padding: 4px;")
        layout.addWidget(header)
        
        self.list_widget = QListWidget(self)
        self.list_widget.setIconSize(QSize(110, 150))
        self.list_widget.setSpacing(6)
        self.list_widget.setStyleSheet("""
            QListWidget {
                background-color: #202020;
                border: 1px solid #383838;
                border-radius: 4px;
            }
            QListWidget::item {
                border-radius: 4px;
                padding: 4px;
                color: #cccccc;
            }
            QListWidget::item:selected {
                background-color: #383838;
                border: 2px solid #E95420;
                color: #ffffff;
            }
        """)
        self.list_widget.currentRowChanged.connect(self._on_row_changed)
        layout.addWidget(self.list_widget)

    def reload_thumbnails(self):
        """Regenerate page thumbnails from document model."""
        self.list_widget.blockSignals(True)
        self.list_widget.clear()
        
        if not self.doc_model.is_open:
            self.list_widget.blockSignals(False)
            return

        for page_idx in range(self.doc_model.page_count):
            pix = self.doc_model.render_page_pixmap(page_idx, zoom=0.22)
            item = QListWidgetItem(f"Page {page_idx + 1}")
            item.setTextAlignment(Qt.AlignCenter)
            if pix:
                item.setIcon(QIcon(pix))
            self.list_widget.addItem(item)
            
        self.list_widget.blockSignals(False)

    def set_current_page(self, page_idx: int):
        """Update selected thumbnail without firing navigation signal."""
        if 0 <= page_idx < self.list_widget.count():
            self.list_widget.blockSignals(True)
            self.list_widget.setCurrentRow(page_idx)
            self.list_widget.scrollToItem(self.list_widget.item(page_idx))
            self.list_widget.blockSignals(False)

    def _on_row_changed(self, row: int):
        if row >= 0:
            self.page_selected.emit(row)
