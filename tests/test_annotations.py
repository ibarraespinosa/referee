"""
Unit tests for ReviewerPDF core document engine and annotation pipeline.
"""
import os
import tempfile
import unittest
import pymupdf
from referee.pdf_document import PDFDocument
from referee.review_exporter import generate_markdown_report, generate_plain_text_report

class TestPDFReviewerCore(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.sample_pdf = os.path.join(self.temp_dir, "sample_paper.pdf")
        
        # Create a sample PDF with academic paper text
        doc = pymupdf.open()
        p1 = doc.new_page(width=595, height=842)
        p1.insert_text((50, 80), "Neural Architecture Search for Protein Sequence Modeling", fontsize=16)
        p1.insert_text((50, 120), "Abstract:\nWe present an empirical study of transformer scaling laws on biological sequences.\nExperimental results show a 15% reduction in cross-entropy loss across all benchmark tasks.", fontsize=11)
        p1.insert_text((50, 200), "1. Introduction\nLarge language models have achieved strong generalization capabilities.\nHowever, previous evaluations failed to address domain shifts.", fontsize=11)
        
        p2 = doc.new_page(width=595, height=842)
        p2.insert_text((50, 80), "2. Methodology\nEquation (1) defines the parameterized objective function:\nL = sum(w_i * loss_i)", fontsize=11)
        
        doc.save(self.sample_pdf)
        doc.close()
        
        self.doc_model = PDFDocument()
        self.assertTrue(self.doc_model.open(self.sample_pdf))

    def tearDown(self):
        self.doc_model.close()
        if os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir)

    def test_document_properties(self):
        self.assertEqual(self.doc_model.page_count, 2)
        w, h = self.doc_model.get_page_size(0)
        self.assertAlmostEqual(w, 595.0, delta=1.0)
        self.assertAlmostEqual(h, 842.0, delta=1.0)

    def test_text_search(self):
        matches = self.doc_model.search_text("scaling laws")
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["page"], 0)
        self.assertIn("scaling laws", matches[0]["query"])

    def test_highlight_annotation(self):
        # Search rect for words to highlight
        rects = [pymupdf.Rect(50, 120, 250, 135)]
        annot_id = self.doc_model.add_highlight(
            page_idx=0,
            rects=rects,
            color=(1.0, 0.92, 0.23),
            content="Check if authors verified this empirically.",
            quoted_text="We present an empirical study"
        )
        self.assertIsNotNone(annot_id)
        
        annots = self.doc_model.get_annotations(0)
        self.assertEqual(len(annots), 1)
        self.assertEqual(annots[0]["type_name"], "Highlight")
        self.assertEqual(annots[0]["content"], "Check if authors verified this empirically.")

    def test_sticky_note_annotation(self):
        annot_id = self.doc_model.add_sticky_note(
            page_idx=1,
            point=(100, 100),
            content="Clarify derivation of Equation 1 weights w_i",
            color=(1.0, 0.85, 0.0)
        )
        self.assertIsNotNone(annot_id)
        
        annots = self.doc_model.get_annotations(1)
        self.assertEqual(len(annots), 1)
        self.assertEqual(annots[0]["type_name"], "Sticky Note")
        self.assertIn("Equation 1", annots[0]["content"])

    def test_save_and_reopen_annotations(self):
        # Add a highlight and a sticky note
        self.doc_model.add_highlight(0, [pymupdf.Rect(50, 80, 400, 100)], content="Key title observation")
        self.doc_model.add_sticky_note(0, (200, 200), content="Note on Introduction")
        
        saved_pdf = os.path.join(self.temp_dir, "saved_review.pdf")
        self.assertTrue(self.doc_model.save(saved_pdf))
        
        # Open saved file with a fresh PDFDocument instance
        doc2 = PDFDocument()
        self.assertTrue(doc2.open(saved_pdf))
        annots_p0 = doc2.get_annotations(0)
        self.assertEqual(len(annots_p0), 2)
        
        types = [a["type_name"] for a in annots_p0]
        self.assertIn("Highlight", types)
        self.assertIn("Sticky Note", types)
        doc2.close()

    def test_review_reports(self):
        self.doc_model.add_highlight(0, [pymupdf.Rect(50, 80, 200, 100)], content="Important finding", quoted_text="Protein Sequence Modeling")
        self.doc_model.add_sticky_note(1, (100, 100), content="Check convergence proof")
        
        md = generate_markdown_report(self.doc_model)
        self.assertIn("# Review Notes:", md)
        self.assertIn("Protein Sequence Modeling", md)
        self.assertIn("Check convergence proof", md)
        self.assertIn("Page 1", md)
        self.assertIn("Page 2", md)
        
        txt = generate_plain_text_report(self.doc_model)
        self.assertIn("REVIEW COMMENTS FOR:", txt)
        self.assertIn("[Page 1]", txt)
        self.assertIn("[Page 2]", txt)

    def test_delete_annotation(self):
        annot_id = self.doc_model.add_sticky_note(0, (100, 100), "Temporary note")
        self.assertEqual(len(self.doc_model.get_annotations(0)), 1)
        
        deleted = self.doc_model.delete_annotation(0, annot_id)
        self.assertTrue(deleted)
        self.assertEqual(len(self.doc_model.get_annotations(0)), 0)

if __name__ == "__main__":
    unittest.main()
