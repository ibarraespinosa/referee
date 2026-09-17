"""
Styles and color schemes for ReviewerPDF.
Designed to look modern, clean, and native on Ubuntu Linux (Yaru/GNOME inspired).
"""

# Preset reviewer colors (Name: (hex, rgb_0_1_tuple))
REVIEWER_COLORS = {
    "Yellow": ("#FFEB3B", (1.0, 0.92, 0.23)),       # Classic highlight / Key point
    "Green": ("#A8E6CF", (0.66, 0.90, 0.81)),        # Positive note / Strength
    "Blue": ("#B3E5FC", (0.70, 0.90, 0.99)),         # Question / Reference
    "Pink": ("#FF8B94", (1.0, 0.55, 0.58)),          # Issue / Critique / Weakness
    "Orange": ("#FFD3B6", (1.0, 0.83, 0.71)),        # Clarification needed
    "Purple": ("#E1BEE7", (0.88, 0.75, 0.91)),       # Methodology / Theory
}

DARK_THEME_QSS = """
QMainWindow {
    background-color: #2b2b2b;
    color: #e0e0e0;
}

QWidget {
    background-color: #2b2b2b;
    color: #e0e0e0;
    font-family: 'Ubuntu', 'Cantarell', 'Segoe UI', sans-serif;
    font-size: 13px;
}

QMenuBar {
    background-color: #242424;
    color: #e0e0e0;
    border-bottom: 1px solid #3c3c3c;
    padding: 2px;
}

QMenuBar::item {
    background: transparent;
    padding: 6px 10px;
    border-radius: 4px;
}

QMenuBar::item:selected {
    background-color: #3d3d3d;
}

QMenu {
    background-color: #2f2f2f;
    color: #e0e0e0;
    border: 1px solid #444444;
    border-radius: 6px;
    padding: 4px;
}

QMenu::item {
    padding: 6px 24px 6px 12px;
    border-radius: 4px;
}

QMenu::item:selected {
    background-color: #E95420;
    color: #ffffff;
}

QMenu::separator {
    height: 1px;
    background: #444444;
    margin: 4px 6px;
}

QToolBar {
    background-color: #242424;
    border: none;
    border-bottom: 1px solid #3a3a3a;
    spacing: 4px;
    padding: 4px 6px;
}

QToolBar::separator {
    width: 1px;
    background-color: #444444;
    margin: 4px 6px;
}

QToolButton {
    background-color: transparent;
    color: #e0e0e0;
    border: 1px solid transparent;
    border-radius: 5px;
    padding: 4px 8px;
    font-weight: 500;
}

QToolButton:hover {
    background-color: #383838;
    border: 1px solid #4d4d4d;
}

QToolButton:pressed, QToolButton:checked {
    background-color: #E95420;
    color: #ffffff;
    border: 1px solid #c34113;
}

QPushButton {
    background-color: #3a3a3a;
    color: #e0e0e0;
    border: 1px solid #4d4d4d;
    border-radius: 5px;
    padding: 5px 12px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #474747;
    border-color: #5c5c5c;
}

QPushButton:pressed {
    background-color: #E95420;
    color: #ffffff;
}

QPushButton#primaryButton {
    background-color: #E95420;
    color: #ffffff;
    border: 1px solid #c34113;
}

QPushButton#primaryButton:hover {
    background-color: #fb6a34;
}

QLineEdit, QSpinBox, QComboBox {
    background-color: #1f1f1f;
    color: #ffffff;
    border: 1px solid #444444;
    border-radius: 5px;
    padding: 4px 8px;
    selection-background-color: #E95420;
}

QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
    border: 1px solid #E95420;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 20px;
    border-left: none;
}

QSplitter::handle {
    background-color: #383838;
}

QSplitter::handle:hover {
    background-color: #E95420;
}

QScrollArea {
    border: none;
    background-color: #1e1e1e;
}

QScrollBar:vertical {
    background: #242424;
    width: 12px;
    margin: 0px;
    border-radius: 6px;
}

QScrollBar::handle:vertical {
    background: #474747;
    min-height: 25px;
    border-radius: 5px;
    margin: 2px;
}

QScrollBar::handle:vertical:hover {
    background: #E95420;
}

QScrollBar:horizontal {
    background: #242424;
    height: 12px;
    margin: 0px;
    border-radius: 6px;
}

QScrollBar::handle:horizontal {
    background: #474747;
    min-width: 25px;
    border-radius: 5px;
    margin: 2px;
}

QScrollBar::handle:horizontal:hover {
    background: #E95420;
}

QScrollBar::add-line, QScrollBar::sub-line {
    border: none;
    background: none;
}

QTabWidget::pane {
    border: 1px solid #3c3c3c;
    background-color: #282828;
    border-radius: 4px;
}

QTabBar::tab {
    background-color: #202020;
    color: #a0a0a0;
    padding: 7px 14px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background-color: #282828;
    color: #ffffff;
    font-weight: bold;
    border-bottom: 2px solid #E95420;
}

QTabBar::tab:hover:!selected {
    background-color: #2a2a2a;
    color: #e0e0e0;
}

QTreeWidget, QListWidget, QTextEdit {
    background-color: #202020;
    color: #e0e0e0;
    border: 1px solid #383838;
    border-radius: 5px;
    padding: 4px;
}

QTreeWidget::item, QListWidget::item {
    padding: 6px 4px;
    border-radius: 4px;
}

QTreeWidget::item:selected, QListWidget::item:selected {
    background-color: #383838;
    color: #ffffff;
    border-left: 3px solid #E95420;
}

QTreeWidget::item:hover:!selected, QListWidget::item:hover:!selected {
    background-color: #2b2b2b;
}

QStatusBar {
    background-color: #1e1e1e;
    color: #9e9e9e;
    border-top: 1px solid #333333;
    font-size: 12px;
}

QToolTip {
    background-color: #1a1a1a;
    color: #ffffff;
    border: 1px solid #444444;
    border-radius: 4px;
    padding: 5px;
}
"""
