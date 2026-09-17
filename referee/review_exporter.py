"""
Review Exporter for ReviewerPDF.
Exports all highlights, comments, and annotations to clean Markdown and Plain Text
review summaries ready for peer review systems (OpenReview, HotCRP, EasyChair).
"""
import datetime
from typing import List, Dict, Any
from .pdf_document import PDFDocument

def generate_markdown_report(doc: PDFDocument) -> str:
    """Generate structured Markdown review report."""
    annots = doc.get_all_annotations()
    
    # Sort annotations by page and vertical coordinate
    annots.sort(key=lambda a: (a.get("page", 0), a.get("rect", (0, 0, 0, 0))[1]))
    
    filename = doc.filename
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    
    lines = [
        f"# Review Notes: {filename}",
        f"**Reviewer:** {doc.reviewer_name}  ",
        f"**Date:** {now}  ",
        f"**Total Annotations:** {len(annots)}  ",
        "",
        "---",
        ""
    ]
    
    if not annots:
        lines.append("*No annotations found in this document.*")
        return "\n".join(lines)
    
    # Group by page
    pages_dict: Dict[int, List[Dict[str, Any]]] = {}
    for a in annots:
        p = a.get("page", 0)
        if p not in pages_dict:
            pages_dict[p] = []
        pages_dict[p].append(a)
        
    for page_idx in sorted(pages_dict.keys()):
        page_num = page_idx + 1
        lines.append(f"## Page {page_num}")
        lines.append("")
        
        for a in pages_dict[page_idx]:
            type_name = a.get("type_name", "Annotation")
            content = a.get("content", "").strip()
            subject = a.get("subject", "")
            
            # Icon / marker based on type
            badge = f"`[{type_name}]`"
            
            if "Highlight" in type_name or "Underline" in type_name or "Strikeout" in type_name:
                # Quoted text if stored in subject or content
                quote = ""
                if subject and ":" in subject:
                    quote = subject.split(":", 1)[1].strip()
                elif content and not subject:
                    quote = content
                    
                if quote and content and quote != content:
                    lines.append(f"- {badge} *\"{quote}\"*")
                    lines.append(f"  > **Reviewer Comment:** {content}")
                elif quote:
                    lines.append(f"- {badge} *\"{quote}\"*")
                elif content:
                    lines.append(f"- {badge} {content}")
                else:
                    lines.append(f"- {badge} *(Highlighted section)*")
            elif "Note" in type_name or "Comment" in type_name:
                lines.append(f"- {badge} **Comment:** {content if content else '*(Empty note)*'}")
            elif "Text Box" in type_name:
                lines.append(f"- {badge} **Margin Note:** {content}")
            else:
                desc = content if content else f"Coordinates: {a.get('rect')}"
                lines.append(f"- {badge} {desc}")
                
            lines.append("")
            
    return "\n".join(lines)

def generate_plain_text_report(doc: PDFDocument) -> str:
    """Generate plain text summary for easy copy-paste into review textboxes."""
    annots = doc.get_all_annotations()
    annots.sort(key=lambda a: (a.get("page", 0), a.get("rect", (0, 0, 0, 0))[1]))
    
    filename = doc.filename
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    
    lines = [
        f"REVIEW COMMENTS FOR: {filename}",
        f"Reviewer: {doc.reviewer_name}",
        f"Date: {now}",
        "=" * 60,
        ""
    ]
    
    if not annots:
        lines.append("No annotations found.")
        return "\n".join(lines)

    pages_dict: Dict[int, List[Dict[str, Any]]] = {}
    for a in annots:
        p = a.get("page", 0)
        if p not in pages_dict:
            pages_dict[p] = []
        pages_dict[p].append(a)

    for page_idx in sorted(pages_dict.keys()):
        page_num = page_idx + 1
        lines.append(f"[Page {page_num}]")
        
        for a in pages_dict[page_idx]:
            type_name = a.get("type_name", "Note")
            content = a.get("content", "").strip()
            subject = a.get("subject", "")
            
            quote = ""
            if subject and ":" in subject:
                quote = subject.split(":", 1)[1].strip()
                
            if quote and content and quote != content:
                lines.append(f"  - [{type_name}] \"{quote}\" -> {content}")
            elif content:
                lines.append(f"  - [{type_name}] {content}")
            elif quote:
                lines.append(f"  - [{type_name}] \"{quote}\"")
            else:
                lines.append(f"  - [{type_name}]")
        lines.append("")
        
    return "\n".join(lines)
