import os
import tempfile
import unittest
import json
from pathlib import Path
import pymupdf

from ai.document_processor import process_document, clean_text, validate_pdf, extract_pages


class DocumentProcessorTestCase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = os.path.join(self.temp_dir, "processed")
        os.makedirs(self.output_dir, exist_ok=True)

    def tearDown(self):
        # Clean up temporary directory and files
        for root, dirs, files in os.walk(self.temp_dir, topdown=False):
            for file in files:
                try:
                    os.remove(os.path.join(root, file))
                except OSError:
                    pass
            for dir in dirs:
                try:
                    os.rmdir(os.path.join(root, dir))
                except OSError:
                    pass
        try:
            os.rmdir(self.temp_dir)
        except OSError:
            pass

    def _create_sample_pdf(self, pages_text: list[str]) -> str:
        """Helper to create a temporary valid PDF using PyMuPDF."""
        doc = pymupdf.open()
        for text in pages_text:
            page = doc.new_page()
            if text.strip():
                page.insert_text((50, 72), text)

        temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf", dir=self.temp_dir)
        temp_pdf.close()
        doc.save(temp_pdf.name)
        doc.close()
        return temp_pdf.name

    def test_clean_text(self):
        noisy_text = "Database   Management\r\n\r\n\r\n\r\nSystems\t\t\xa0(DBMS)\n\n\n\nUnit 3"
        cleaned = clean_text(noisy_text)
        self.assertNotIn("\r", cleaned)
        self.assertNotIn("\xa0", cleaned)
        self.assertNotIn("\t\t", cleaned)
        self.assertNotIn("   ", cleaned)
        self.assertIn("Database Management\n\nSystems (DBMS)\n\nUnit 3", cleaned)

    def test_process_valid_pdf(self):
        page1 = (
            "Unit 3: Normalization & Functional Dependencies\n\n"
            "Normalization is the process of organizing attributes in a database to reduce data redundancy "
            "and improve data integrity. Normal forms include 1NF, 2NF, 3NF, and BCNF."
        )
        page2 = (
            "First Normal Form (1NF):\n"
            "Each attribute value must be atomic, meaning that columns cannot contain multiple values or arrays.\n\n"
            "Second Normal Form (2NF):\n"
            "Must be in 1NF and no non-prime attribute may be partially dependent on any candidate key."
        )

        pdf_path = self._create_sample_pdf([page1, page2])

        result = process_document(
            file_path=pdf_path,
            course_id=1,
            material_id=10,
            output_dir=self.output_dir
        )

        self.assertEqual(result["total_pages"], 2)
        self.assertGreaterEqual(result["total_chunks"], 2)
        self.assertEqual(result["course_id"], 1)
        self.assertEqual(result["material_id"], 10)
        self.assertTrue(os.path.exists(result["output_file"]))

        # Verify persisted JSON structure
        with open(result["output_file"], "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data["course_id"], 1)
        self.assertEqual(data["material_id"], 10)
        self.assertEqual(data["total_pages"], 2)
        self.assertEqual(len(data["chunks"]), result["total_chunks"])

        # Verify chunk metadata contract
        first_chunk = data["chunks"][0]
        self.assertIn("chunk_id", first_chunk)
        self.assertEqual(first_chunk["course_id"], 1)
        self.assertEqual(first_chunk["material_id"], 10)
        self.assertEqual(first_chunk["page_number"], 1)
        self.assertIn("text", first_chunk)
        self.assertIn("char_count", first_chunk)
        self.assertIn("token_count_approx", first_chunk)
        self.assertIn("Normalization", first_chunk["text"])

    def test_ignore_empty_pages(self):
        # Page 1 is empty, Page 2 has content
        pdf_path = self._create_sample_pdf(["", "Valid content on page two."])

        result = process_document(
            file_path=pdf_path,
            course_id=2,
            output_dir=self.output_dir
        )

        self.assertEqual(result["total_pages"], 1)
        self.assertGreaterEqual(result["total_chunks"], 1)

        with open(result["output_file"], "r", encoding="utf-8") as f:
            data = json.load(f)

        # The extracted page should be page 2
        self.assertEqual(data["chunks"][0]["page_number"], 2)

    def test_invalid_file_handling(self):
        # Non-existent file
        with self.assertRaises(FileNotFoundError):
            validate_pdf("non_existent_file.pdf")

        # Non-PDF extension
        txt_path = os.path.join(self.temp_dir, "notes.txt")
        with open(txt_path, "w") as f:
            f.write("Some text")
        with self.assertRaises(ValueError):
            validate_pdf(txt_path)

        # File with .pdf extension but invalid header
        bad_pdf = os.path.join(self.temp_dir, "corrupt.pdf")
        with open(bad_pdf, "wb") as f:
            f.write(b"NOT_A_PDF_HEADER_12345")
        with self.assertRaises(ValueError):
            validate_pdf(bad_pdf)


if __name__ == "__main__":
    unittest.main()
