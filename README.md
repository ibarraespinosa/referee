# Referee 📄⚖️

<div align="center">

**Lightweight, Open-Source, Acrobat-Like PDF Review & Annotation Editor for Ubuntu / Linux**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Platform: Linux](https://img.shields.io/badge/platform-Linux%20%7C%20Ubuntu-orange.svg)](https://ubuntu.com/)
[![CI](https://github.com/ibarraespinosa/referee/actions/workflows/ci.yml/badge.svg)](https://github.com/ibarraespinosa/referee/actions/workflows/ci.yml)
[![Standard: ISO 32000](https://img.shields.io/badge/PDF-ISO%2032000%20Standard-brightgreen.svg)](https://www.iso.org/standard/75839.html)

</div>

---

## 🎯 Motivation

As researchers, paper reviewers, and editors, reviewing manuscripts shouldn't require clunky proprietary software or slow electron apps.

**Referee** is built from the ground up for academic and document reviewers on Linux:
- **Instant startup** and crisp high-DPI rendering powered by **PyMuPDF (fitz)**.
- **Acrobat-inspired review ribbon**: 1-click multi-color text highlights, sticky notes, margin callouts, underlines, and freehand drawing.
- **Live Review Notes Sidebar**: View, search, and jump to every comment in the document.
- **1-Click Review Export**: Export all quotes, page numbers, and review notes into clean **Markdown (`.md`)** or **Plain Text (`.txt`)** ready to copy-paste directly into **OpenReview**, **HotCRP**, **EasyChair**, or journal editorial systems.
- **100% ISO 32000 Standards Compliant**: Saved annotations are native PDF annotations (`/Highlight`, `/Text`, `/Underline`, `/StrikeOut`, `/FreeText`, `/Ink`, `/Square`), rendering seamlessly in Adobe Acrobat, Apple Preview, Okular, Evince, and web browsers.

---

## ✨ Features

### 🖍️ 1-Click Multi-Color Highlighting
Select text and instantly highlight with standard academic review colors:
- 🟡 **Yellow**: Key findings / Main takeaways
- 🟢 **Green**: Strengths / Well-formulated arguments
- 🔵 **Blue**: Reference needed / Question to author
- 🔴 **Pink**: Critique / Technical flaw / Weakness
- 🟠 **Orange**: Clarification needed / Formatting note

### 📌 Sticky Note Comments & Margin Boxes
- Click anywhere on a page, formula, or figure to place a comment pin.
- Tag comments with your custom reviewer identity (e.g. `Reviewer 1`, `Reviewer 2`).
- Add margin text boxes with custom dimensions.

### ✍️ Visual Markup Tools
- **Underline (`U`)** and **Strikeout (`S`)** for suggested textual corrections.
- **Freehand Pen (`P`)** with configurable stroke width for circling equations and formulas.
- **Bounding Boxes / Rectangles (`R`)** for highlighting figures, plots, and tables.
- **Eraser / Delete**: Click any mark to delete or press `Del`.

### 📋 Live Review Notes Drawer & 1-Click Export
- Live sidebar tree grouping all annotations across the document by page.
- Double-click any note to edit your remarks.
- Search and filter across review notes.
- **Export Review Report**:
  - Export to structured **Markdown (`.md`)**
  - Export to **Plain Text (`.txt`)**
  - **Copy Review Summary to Clipboard** for instantaneous pasting into review submission forms.

### 🔍 Fast In-Document Search (`Ctrl + F`)
- Live hit counter (`Match 2 of 14`).
- Next/Previous jump navigation with automatic page scrolling.

---

## 🚀 Installation & Desktop Integration

### Option 1: Quick Install (Recommended for Ubuntu)

Clone the repository and run the automated installer:
```bash
git clone https://github.com/ibarraespinosa/referee.git
cd referee
./install.sh
```

`install.sh` will:
1. Symlink the `referee` command into `~/.local/bin/referee`
2. Create the system desktop entry at `~/.local/share/applications/referee.desktop`
3. Make **Referee** searchable in your Ubuntu application menu ("Show Applications" $\rightarrow$ **Referee**)

### Option 2: Python Package (Pip)

Install directly as an editable package:
```bash
pip install --user . --break-system-packages
```

---

## 💻 Usage

### Command Line
```bash
# Open any PDF document:
referee manuscript.pdf

# Or launch directly with Python:
python3 app.py manuscript.pdf
```

### Ubuntu Desktop
- Search for **Referee** in your application launcher.
- Or right-click any PDF file in Nautilus / Files $\rightarrow$ **Open With Other Application** $\rightarrow$ **Referee**.
- Drag and drop any `.pdf` file directly into the application window.

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
| :--- | :--- |
| `V` | **Select / Pointer tool** (select marks or text) |
| `Shift + H` | **Highlight tool** (drag over text to highlight) |
| `U` | **Underline tool** |
| `S` | **Strikeout tool** |
| `N` | **Sticky Note tool** (click page to place comment pin) |
| `T` | **Margin Text Box tool** |
| `P` | **Freehand Pen drawing tool** |
| `R` | **Rectangle / Box tool** |
| `Delete` / `Backspace` | **Delete selected annotation** |
| `Ctrl + F` | **Find text in document** |
| `Ctrl + S` | **Save PDF** with standard ISO annotations |
| `Ctrl + Shift + S` | **Save As...** |
| `Ctrl + Z` | **Undo** last annotation |
| `Ctrl + +` / `Ctrl + -` | **Zoom In / Zoom Out** |
| `Ctrl + 0` | **Fit Page** |
| `Ctrl + W` | **Fit Width** |
| `F9` | **Toggle Sidebar** (Thumbnails & Review Notes) |
| `Page Up` / `Page Down` | **Previous / Next page** |
| `Home` / `End` | **First / Last page** |

---

## 🏗️ Architecture

```
referee/
├── pyproject.toml              # Modern PEP 621 build configuration
├── setup.py                    # Standard setuptools packaging
├── requirements.txt            # Core dependencies (PyQt5, pymupdf)
├── LICENSE                     # MIT License
├── README.md                   # Documentation
├── install.sh                  # One-click Ubuntu desktop integration installer
├── app.py                      # Root launcher script
├── bin/
│   ├── referee                 # CLI launcher executable
│   └── pdf-reviewer            # Backwards-compatible CLI alias
├── referee/
│   ├── __init__.py
│   ├── app.py                  # Package entrypoint (main)
│   ├── main_window.py          # Acrobat-style main window, ribbon, and menus
│   ├── pdf_document.py         # PyMuPDF document model & ISO 32000 annotation engine
│   ├── pdf_canvas.py           # Interactive viewing canvas, text selection, drawing
│   ├── thumbnail_view.py       # Sidebar page thumbnail previews
│   ├── comments_panel.py       # Review comments tree with inline editing & export
│   ├── search_dialog.py        # In-document search bar
│   ├── review_exporter.py      # Markdown & Text review summary generator
│   ├── styles.py               # Modern Ubuntu Yaru dark theme stylesheet
│   └── icons.py                # Crisp vector QPainter icons
└── tests/
    ├── test_annotations.py     # Document engine & ISO annotation tests
    └── test_gui.py             # Offscreen GUI smoke tests
```

---

## 🧪 Testing

Run the automated test suite:
```bash
QT_QPA_PLATFORM=offscreen python3 -m unittest discover tests
```

---

## 👤 Author & Acknowledgments

- **Sergio Ibarra-Espinosa** ([@ibarraespinosa](https://github.com/ibarraespinosa) · [sibarra@umd.edu](mailto:sibarra@umd.edu))
- Built with [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) and [PyMuPDF](https://pymupdf.readthedocs.io/).

---

## 📜 License

This project is licensed under the [MIT License](LICENSE).
