"""
GUI smoke test for ReviewerPDF using offscreen Qt platform.
"""
import os
import sys
import tempfile
import unittest
import pymupdf
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QPointF
from referee.main_window import MainWindow

# Ensure offscreen Qt application
app = QApplication.instance()
if not app:
    app = QApplication(["ReviewerPDF_Test", "-platform", "offscreen"])

class TestReviewerGUI(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.pdf_path = os.path.join(self.temp_dir, "test_paper.pdf")
        
        doc = pymupdf.open()
        p1 = doc.new_page()
        p1.insert_text((50, 50), "Attention Is All You Need in Molecular Biology", fontsize=14)
        p1.insert_text((50, 100), "We test neural networks on genomic data.", fontsize=11)
        p2 = doc.new_page()
        p2.insert_text((50, 50), "Results and Discussion", fontsize=14)
        doc.save(self.pdf_path)
        doc.close()
        
        self.window = MainWindow(initial_pdf=self.pdf_path)

    def tearDown(self):
        self.window.doc_model.is_modified = False
        self.window.close()
        if os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir)

    def test_window_initialization(self):
        self.assertTrue(self.window.doc_model.is_open)
        self.assertEqual(self.window.doc_model.page_count, 2)
        self.assertEqual(self.window.canvas.current_page, 0)
        self.assertEqual(self.window.spin_page.value(), 1)

    def test_navigation_and_zoom(self):
        self.window.go_to_page(1)
        self.assertEqual(self.window.canvas.current_page, 1)
        self.assertEqual(self.window.spin_page.value(), 2)
        
        # Test zoom
        initial_zoom = self.window.canvas.zoom
        self.window.canvas.set_zoom(1.5)
        self.assertAlmostEqual(self.window.canvas.zoom, 1.5)
        self.assertEqual(self.window.combo_zoom.currentText(), "150%")

    def test_search_integration(self):
        self.window.search_bar.edit_search.setText("genomic")
        self.assertEqual(len(self.window.search_bar.matches), 1)
        self.assertEqual(self.window.search_bar.matches[0]["page"], 0)

    def test_comments_panel_integration(self):
        # Programmatically add annotation
        self.window.doc_model.add_sticky_note(0, (100, 100), "Critical review point")
        self.window.comments_panel.reload_comments()
        
        # Check that comments panel displays 1 annotation
        self.assertIn("Review Comments (1)", self.window.comments_panel.lbl_title.text())
        self.assertEqual(self.window.comments_panel.tree.topLevelItemCount(), 1)

if __name__ == "__main__":
    unittest.main()
