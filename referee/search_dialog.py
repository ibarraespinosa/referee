"""
Search bar widget for ReviewerPDF.
Provides fast in-document text search with hit count and next/prev navigation.
"""
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QLineEdit, QPushButton, QLabel, QCheckBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from .icons import get_icon

class SearchBar(QWidget):
    find_next = pyqtSignal(dict) # match dict: {page, rect, query}
    closed = pyqtSignal()

    def __init__(self, doc_model, parent=None):
        super().__init__(parent)
        self.doc_model = doc_model
        self.matches = []
        self.current_match_idx = -1
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(6)
        
        self.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                border: 1px solid #444444;
                border-radius: 6px;
            }
        """)
        
        lbl_icon = QLabel(self)
        lbl_icon.setPixmap(get_icon("search").pixmap(16, 16))
        layout.addWidget(lbl_icon)
        
        self.edit_search = QLineEdit(self)
        self.edit_search.setPlaceholderText("Find text in document...")
        self.edit_search.setMinimumWidth(220)
        self.edit_search.textChanged.connect(self._on_search_text_changed)
        self.edit_search.returnPressed.connect(self.next_match)
        layout.addWidget(self.edit_search)
        
        self.lbl_count = QLabel("0/0", self)
        self.lbl_count.setStyleSheet("color: #9e9e9e; min-width: 45px;")
        layout.addWidget(self.lbl_count)
        
        self.chk_case = QCheckBox("Aa", self)
        self.chk_case.setToolTip("Match Case")
        self.chk_case.toggled.connect(self._on_search_text_changed)
        layout.addWidget(self.chk_case)
        
        self.btn_prev = QPushButton(self)
        self.btn_prev.setIcon(get_icon("prev"))
        self.btn_prev.setToolTip("Previous match (Shift+Enter)")
        self.btn_prev.clicked.connect(self.prev_match)
        layout.addWidget(self.btn_prev)
        
        self.btn_next = QPushButton(self)
        self.btn_next.setIcon(get_icon("next"))
        self.btn_next.setToolTip("Next match (Enter)")
        self.btn_next.clicked.connect(self.next_match)
        layout.addWidget(self.btn_next)
        
        self.btn_close = QPushButton("×", self)
        self.btn_close.setToolTip("Close search (Esc)")
        self.btn_close.setStyleSheet("font-weight: bold; font-size: 14px; padding: 2px 6px;")
        self.btn_close.clicked.connect(self.hide_bar)
        layout.addWidget(self.btn_close)

    def show_and_focus(self):
        self.show()
        self.edit_search.selectAll()
        self.edit_search.setFocus()

    def hide_bar(self):
        self.hide()
        self.matches.clear()
        self.current_match_idx = -1
        self.lbl_count.setText("0/0")
        self.closed.emit()

    def _on_search_text_changed(self):
        query = self.edit_search.text().strip()
        if not query or not self.doc_model.is_open:
            self.matches = []
            self.current_match_idx = -1
            self.lbl_count.setText("0/0")
            return
            
        self.matches = self.doc_model.search_text(query, match_case=self.chk_case.isChecked())
        if self.matches:
            self.current_match_idx = 0
            self.lbl_count.setText(f"1/{len(self.matches)}")
            self.find_next.emit(self.matches[0])
        else:
            self.current_match_idx = -1
            self.lbl_count.setText("0/0")

    def next_match(self):
        if not self.matches:
            return
        self.current_match_idx = (self.current_match_idx + 1) % len(self.matches)
        self.lbl_count.setText(f"{self.current_match_idx + 1}/{len(self.matches)}")
        self.find_next.emit(self.matches[self.current_match_idx])

    def prev_match(self):
        if not self.matches:
            return
        self.current_match_idx = (self.current_match_idx - 1 + len(self.matches)) % len(self.matches)
        self.lbl_count.setText(f"{self.current_match_idx + 1}/{len(self.matches)}")
        self.find_next.emit(self.matches[self.current_match_idx])
