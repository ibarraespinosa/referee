"""
PDF Document Model for ReviewerPDF.
Wraps PyMuPDF (fitz) to provide document rendering, text extraction,
standard ISO 32000 PDF annotation manipulation, and undo/redo support.
"""
import os
import pymupdf
from PyQt5.QtGui import QImage, QPixmap
from typing import List, Dict, Tuple, Optional, Any

# Map fitz annotation types to human-readable names
ANNOT_TYPE_NAMES = {
    pymupdf.PDF_ANNOT_TEXT: "Sticky Note",
    pymupdf.PDF_ANNOT_HIGHLIGHT: "Highlight",
    pymupdf.PDF_ANNOT_UNDERLINE: "Underline",
    getattr(pymupdf, "PDF_ANNOT_STRIKE_OUT", 11): "Strikeout",
    pymupdf.PDF_ANNOT_SQUARE: "Rectangle",
    pymupdf.PDF_ANNOT_CIRCLE: "Circle",
    pymupdf.PDF_ANNOT_LINE: "Line",
    pymupdf.PDF_ANNOT_FREE_TEXT: "Text Box",
    pymupdf.PDF_ANNOT_INK: "Pen / Ink",
}

class PDFDocument:
    def __init__(self):
        self.doc: Optional[pymupdf.Document] = None
        self.filepath: Optional[str] = None
        self.is_modified: bool = False
        self._pixmap_cache: Dict[Tuple[int, float], QPixmap] = {}
        self.reviewer_name: str = "Reviewer"
        
        # Undo / Redo history
        self._undo_stack: List[Dict[str, Any]] = []
        self._redo_stack: List[Dict[str, Any]] = []

    def open(self, filepath: str) -> bool:
        """Open a PDF file."""
        try:
            self.close()
            self.doc = pymupdf.open(filepath)
            self.filepath = filepath
            self.is_modified = False
            self._pixmap_cache.clear()
            self._undo_stack.clear()
            self._redo_stack.clear()
            return True
        except Exception as e:
            print(f"Error opening PDF: {e}")
            return False

    def close(self):
        """Close current document."""
        if self.doc:
            self.doc.close()
            self.doc = None
        self.filepath = None
        self.is_modified = False
        self._pixmap_cache.clear()
        self._undo_stack.clear()
        self._redo_stack.clear()

    @property
    def is_open(self) -> bool:
        return self.doc is not None

    @property
    def page_count(self) -> int:
        return len(self.doc) if self.doc else 0

    @property
    def filename(self) -> str:
        return os.path.basename(self.filepath) if self.filepath else "Untitled"

    def get_page(self, page_idx: int) -> Optional[pymupdf.Page]:
        if not self.doc or page_idx < 0 or page_idx >= self.page_count:
            return None
        return self.doc[page_idx]

    def get_page_size(self, page_idx: int) -> Tuple[float, float]:
        page = self.get_page(page_idx)
        if not page:
            return (0.0, 0.0)
        rect = page.rect
        return (rect.width, rect.height)

    def render_page_pixmap(self, page_idx: int, zoom: float = 1.0) -> Optional[QPixmap]:
        """Render page at specific zoom to QPixmap with caching."""
        if not self.doc:
            return None
        
        cache_key = (page_idx, round(zoom, 2))
        if cache_key in self._pixmap_cache:
            return self._pixmap_cache[cache_key]

        page = self.get_page(page_idx)
        if not page:
            return None

        # Render with subpixel anti-aliasing
        matrix = pymupdf.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        
        qimg = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
        qpix = QPixmap.fromImage(qimg)
        
        # Limit cache size to 15 pages
        if len(self._pixmap_cache) > 15:
            self._pixmap_cache.pop(next(iter(self._pixmap_cache)))
            
        self._pixmap_cache[cache_key] = qpix
        return qpix

    def invalidate_page_cache(self, page_idx: Optional[int] = None):
        """Invalidate rendered cache when annotations are added/modified."""
        if page_idx is None:
            self._pixmap_cache.clear()
        else:
            keys_to_remove = [k for k in self._pixmap_cache if k[0] == page_idx]
            for k in keys_to_remove:
                self._pixmap_cache.pop(k, None)

    def get_words(self, page_idx: int) -> List[Tuple]:
        """Get all words on page: (x0, y0, x1, y1, word, block_no, line_no, word_no)."""
        page = self.get_page(page_idx)
        if not page:
            return []
        return page.get_text("words")

    def get_page_text(self, page_idx: int) -> str:
        page = self.get_page(page_idx)
        if not page:
            return ""
        return page.get_text("text")

    def search_text(self, query: str, match_case: bool = False) -> List[Dict[str, Any]]:
        """Search across entire document and return matches with bounding boxes."""
        if not self.doc or not query.strip():
            return []
        
        results = []
        flags = pymupdf.TEXT_DEHYPHENATE
        if not match_case:
            flags |= pymupdf.TEXT_PRESERVE_WHITESPACE

        for page_idx in range(self.page_count):
            page = self.doc[page_idx]
            rects = page.search_for(query, flags=flags)
            for r in rects:
                results.append({
                    "page": page_idx,
                    "rect": (r.x0, r.y0, r.x1, r.y1),
                    "query": query
                })
        return results

    # ==================== ANNOTATIONS ====================

    def get_annotations(self, page_idx: int) -> List[Dict[str, Any]]:
        """Retrieve all annotations on the given page."""
        page = self.get_page(page_idx)
        if not page:
            return []

        annot_list = []
        for annot in page.annots():
            info = annot.info or {}
            annot_type = annot.type[0] if isinstance(annot.type, (tuple, list)) else annot.type
            type_name = ANNOT_TYPE_NAMES.get(annot_type, annot.type[1] if isinstance(annot.type, (tuple, list)) else "Annotation")
            
            rect = annot.rect
            annot_id = info.get("id") or f"{page_idx}_{rect.x0:.1f}_{rect.y0:.1f}"
            
            # Extract underlying text for markup annotations if not specified
            content = info.get("content", "")
            title = info.get("title", "")
            
            # Color
            colors = annot.colors or {}
            stroke_color = colors.get("stroke")

            annot_list.append({
                "id": annot_id,
                "type": annot_type,
                "type_name": type_name,
                "rect": (rect.x0, rect.y0, rect.x1, rect.y1),
                "author": title,
                "content": content,
                "subject": info.get("subject", ""),
                "color": stroke_color,
                "page": page_idx,
                "annot_ref": annot
            })
        return annot_list

    def get_all_annotations(self) -> List[Dict[str, Any]]:
        """Retrieve all annotations across all pages in document."""
        all_annots = []
        for i in range(self.page_count):
            all_annots.extend(self.get_annotations(i))
        return all_annots

    def add_highlight(self, page_idx: int, rects: List[pymupdf.Rect], 
                      color: Tuple[float, float, float] = (1.0, 0.92, 0.23),
                      content: str = "", quoted_text: str = "") -> Optional[str]:
        """Add text highlight annotation."""
        page = self.get_page(page_idx)
        if not page or not rects:
            return None
        
        annot = page.add_highlight_annot(rects)
        annot.set_colors(stroke=color)
        annot.set_info(
            title=self.reviewer_name,
            content=content,
            subject=f"Highlight: {quoted_text[:80]}" if quoted_text else "Highlight"
        )
        annot.update()
        
        self.invalidate_page_cache(page_idx)
        self.is_modified = True
        annot_id = annot.info.get("id")
        
        self._record_action({
            "action": "add",
            "page": page_idx,
            "id": annot_id
        })
        return annot_id

    def add_underline(self, page_idx: int, rects: List[pymupdf.Rect],
                      color: Tuple[float, float, float] = (0.2, 0.6, 1.0),
                      content: str = "", quoted_text: str = "") -> Optional[str]:
        """Add text underline annotation."""
        page = self.get_page(page_idx)
        if not page or not rects:
            return None
            
        annot = page.add_underline_annot(rects)
        annot.set_colors(stroke=color)
        annot.set_info(
            title=self.reviewer_name,
            content=content,
            subject=f"Underline: {quoted_text[:80]}" if quoted_text else "Underline"
        )
        annot.update()
        
        self.invalidate_page_cache(page_idx)
        self.is_modified = True
        annot_id = annot.info.get("id")
        
        self._record_action({
            "action": "add",
            "page": page_idx,
            "id": annot_id
        })
        return annot_id

    def add_strikeout(self, page_idx: int, rects: List[pymupdf.Rect],
                      color: Tuple[float, float, float] = (0.9, 0.2, 0.2),
                      content: str = "", quoted_text: str = "") -> Optional[str]:
        """Add text strikeout annotation."""
        page = self.get_page(page_idx)
        if not page or not rects:
            return None
            
        annot = page.add_strikeout_annot(rects)
        annot.set_colors(stroke=color)
        annot.set_info(
            title=self.reviewer_name,
            content=content,
            subject=f"Strikeout: {quoted_text[:80]}" if quoted_text else "Strikeout"
        )
        annot.update()
        
        self.invalidate_page_cache(page_idx)
        self.is_modified = True
        annot_id = annot.info.get("id")
        
        self._record_action({
            "action": "add",
            "page": page_idx,
            "id": annot_id
        })
        return annot_id

    def add_sticky_note(self, page_idx: int, point: Tuple[float, float],
                        content: str, color: Tuple[float, float, float] = (1.0, 0.85, 0.0),
                        icon: str = "Comment") -> Optional[str]:
        """Add sticky note / comment pin annotation."""
        page = self.get_page(page_idx)
        if not page:
            return None
            
        pt = pymupdf.Point(point[0], point[1])
        annot = page.add_text_annot(pt, content, icon=icon)
        annot.set_colors(stroke=color)
        annot.set_info(title=self.reviewer_name, content=content, subject="Comment")
        annot.update()
        
        self.invalidate_page_cache(page_idx)
        self.is_modified = True
        annot_id = annot.info.get("id")
        
        self._record_action({
            "action": "add",
            "page": page_idx,
            "id": annot_id
        })
        return annot_id

    def add_freetext(self, page_idx: int, rect: Tuple[float, float, float, float],
                     text: str, fontsize: float = 11,
                     text_color: Tuple[float, float, float] = (0.1, 0.1, 0.1),
                     fill_color: Optional[Tuple[float, float, float]] = (1.0, 1.0, 0.85),
                     border_color: Optional[Tuple[float, float, float]] = (0.7, 0.7, 0.7)) -> Optional[str]:
        """Add direct text box annotation."""
        page = self.get_page(page_idx)
        if not page or not text.strip():
            return None
            
        r = pymupdf.Rect(*rect)
        annot = page.add_freetext_annot(
            r, text, fontsize=fontsize, 
            text_color=text_color, 
            fill_color=fill_color,
            border_color=border_color
        )
        annot.set_info(title=self.reviewer_name, content=text, subject="Text Box")
        annot.update()
        
        self.invalidate_page_cache(page_idx)
        self.is_modified = True
        annot_id = annot.info.get("id")
        
        self._record_action({
            "action": "add",
            "page": page_idx,
            "id": annot_id
        })
        return annot_id

    def add_ink(self, page_idx: int, stroke_points_list: List[List[Tuple[float, float]]],
                color: Tuple[float, float, float] = (0.85, 0.15, 0.15),
                width: float = 2.0) -> Optional[str]:
        """Add freehand pen / ink drawing."""
        page = self.get_page(page_idx)
        if not page or not stroke_points_list:
            return None
            
        points = [[pymupdf.Point(p[0], p[1]) for p in stroke] for stroke in stroke_points_list]
        annot = page.add_ink_annot(points)
        annot.set_colors(stroke=color)
        annot.set_border(width=width)
        annot.set_info(title=self.reviewer_name, subject="Drawing")
        annot.update()
        
        self.invalidate_page_cache(page_idx)
        self.is_modified = True
        annot_id = annot.info.get("id")
        
        self._record_action({
            "action": "add",
            "page": page_idx,
            "id": annot_id
        })
        return annot_id

    def add_rect(self, page_idx: int, rect: Tuple[float, float, float, float],
                 color: Tuple[float, float, float] = (0.85, 0.15, 0.15),
                 width: float = 2.0, fill_color: Optional[Tuple[float, float, float]] = None) -> Optional[str]:
        """Add rectangle annotation around figure/table."""
        page = self.get_page(page_idx)
        if not page:
            return None
            
        r = pymupdf.Rect(*rect)
        annot = page.add_rect_annot(r)
        annot.set_colors(stroke=color, fill=fill_color)
        annot.set_border(width=width)
        annot.set_info(title=self.reviewer_name, subject="Rectangle")
        annot.update()
        
        self.invalidate_page_cache(page_idx)
        self.is_modified = True
        annot_id = annot.info.get("id")
        
        self._record_action({
            "action": "add",
            "page": page_idx,
            "id": annot_id
        })
        return annot_id

    def delete_annotation(self, page_idx: int, annot_id: str) -> bool:
        """Delete an annotation by its ID or coordinate match."""
        page = self.get_page(page_idx)
        if not page:
            return False

        for annot in page.annots():
            info = annot.info or {}
            curr_id = info.get("id") or f"{page_idx}_{annot.rect.x0:.1f}_{annot.rect.y0:.1f}"
            if curr_id == annot_id:
                page.delete_annot(annot)
                self.invalidate_page_cache(page_idx)
                self.is_modified = True
                return True
        return False

    def update_annotation_content(self, page_idx: int, annot_id: str, new_content: str) -> bool:
        """Update comment text of an annotation."""
        page = self.get_page(page_idx)
        if not page:
            return False

        for annot in page.annots():
            info = annot.info or {}
            curr_id = info.get("id") or f"{page_idx}_{annot.rect.x0:.1f}_{annot.rect.y0:.1f}"
            if curr_id == annot_id:
                annot.set_info(content=new_content)
                annot.update()
                self.invalidate_page_cache(page_idx)
                self.is_modified = True
                return True
        return False

    # ==================== SAVE / EXPORT ====================

    def save(self, target_filepath: Optional[str] = None) -> bool:
        """Save PDF document with standard ISO annotations."""
        if not self.doc:
            return False
        
        save_path = target_filepath or self.filepath
        if not save_path:
            return False

        try:
            # If saving to the same file that's open in PyMuPDF, write to a temp file then atomic replace
            if os.path.abspath(save_path) == (os.path.abspath(self.filepath) if self.filepath else ""):
                temp_path = save_path + ".tmp_save.pdf"
                self.doc.save(temp_path, garbage=4, deflate=True)
                self.doc.close()
                os.replace(temp_path, save_path)
                self.doc = pymupdf.open(save_path)
            else:
                self.doc.save(save_path, garbage=4, deflate=True)
                
            self.filepath = save_path
            self.is_modified = False
            return True
        except Exception as e:
            print(f"Error saving PDF: {e}")
            return False

    # ==================== UNDO / REDO ====================

    def _record_action(self, action_dict: Dict[str, Any]):
        self._undo_stack.append(action_dict)
        self._redo_stack.clear()

    def can_undo(self) -> bool:
        return len(self._undo_stack) > 0

    def can_redo(self) -> bool:
        return len(self._redo_stack) > 0

    def undo(self) -> Optional[int]:
        """Undo last annotation action. Returns affected page_idx."""
        if not self.can_undo():
            return None
        action = self._undo_stack.pop()
        if action["action"] == "add":
            page_idx = action["page"]
            self.delete_annotation(page_idx, action["id"])
            self._redo_stack.append(action)
            return page_idx
        return None
