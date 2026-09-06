import sys
import unittest
import tempfile
import os
import io
from pathlib import Path

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.app import create_app
from backend.config import Config


class Stage2MaterialsAPITestCase(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        self.temp_upload_dir = tempfile.mkdtemp()
        self.original_db_path = Config.DATABASE_PATH
        self.original_upload_folder = Config.UPLOAD_FOLDER

        Config.DATABASE_PATH = self.db_path
        Config.UPLOAD_FOLDER = self.temp_upload_dir

        class TestConfig(Config):
            TESTING = True
            DATABASE_PATH = self.db_path
            UPLOAD_FOLDER = self.temp_upload_dir

        self.app = create_app(TestConfig)
        self.client = self.app.test_client()

        # Create a test course
        c_res = self.client.post("/api/courses", json={"course_name": "DBMS", "description": "Database Systems"})
        self.course_id = c_res.get_json()["course_id"]

    def tearDown(self):
        Config.DATABASE_PATH = self.original_db_path
        Config.UPLOAD_FOLDER = self.original_upload_folder
        os.close(self.db_fd)
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_upload_pdf_success(self):
        pdf_content = b"%PDF-1.4 test dbms pdf content"
        data = {
            "course_id": str(self.course_id),
            "file": (io.BytesIO(pdf_content), "dbms_unit3.pdf")
        }
        response = self.client.post(
            "/api/materials/upload",
            data=data,
            content_type="multipart/form-data"
        )
        self.assertEqual(response.status_code, 201)
        res_data = response.get_json()
        self.assertIn("material_id", res_data)
        self.assertEqual(res_data["file_name"], "dbms_unit3.pdf")
        self.assertEqual(res_data["processing_status"], "pending")
        self.assertTrue(os.path.exists(res_data["file_path"]))

    def test_upload_missing_course_or_invalid_course(self):
        pdf_content = b"%PDF-1.4 sample content"
        # Missing course_id
        res_no_course = self.client.post(
            "/api/materials/upload",
            data={"file": (io.BytesIO(pdf_content), "doc.pdf")},
            content_type="multipart/form-data"
        )
        self.assertEqual(res_no_course.status_code, 400)

        # Invalid non-existent course_id
        res_bad_course = self.client.post(
            "/api/materials/upload",
            data={"course_id": "9999", "file": (io.BytesIO(pdf_content), "doc.pdf")},
            content_type="multipart/form-data"
        )
        self.assertEqual(res_bad_course.status_code, 404)

    def test_upload_invalid_file_type(self):
        data = {
            "course_id": str(self.course_id),
            "file": (io.BytesIO(b"Hello world"), "notes.txt")
        }
        response = self.client.post(
            "/api/materials/upload",
            data=data,
            content_type="multipart/form-data"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Only PDF files are accepted", response.get_json()["error"])

    def test_process_material_endpoint(self):
        # Upload material first
        pdf_content = b"%PDF-1.4 unit 3 normalization"
        up_res = self.client.post(
            "/api/materials/upload",
            data={"course_id": str(self.course_id), "file": (io.BytesIO(pdf_content), "unit3.pdf")},
            content_type="multipart/form-data"
        )
        material_id = up_res.get_json()["material_id"]

        # Call process endpoint
        proc_res = self.client.post(f"/api/materials/{material_id}/process")
        self.assertEqual(proc_res.status_code, 200)
        proc_data = proc_res.get_json()
        self.assertEqual(proc_data["material_id"], material_id)
        # When AI document_processor is implemented, status is 'processed'; if absent, remains 'pending'
        if "not implemented yet" in proc_data.get("message", ""):
            self.assertEqual(proc_data["processing_status"], "pending")
            self.assertIn("not implemented yet", proc_data["message"])
        else:
            self.assertEqual(proc_data["processing_status"], "processed")
            self.assertIn("processed successfully", proc_data["message"])


        # Test non-existent material process
        proc_404 = self.client.post("/api/materials/9999/process")
        self.assertEqual(proc_404.status_code, 404)

    def test_get_materials(self):
        # Initial empty
        res_empty = self.client.get("/api/materials")
        self.assertEqual(res_empty.status_code, 200)
        self.assertEqual(res_empty.get_json(), [])

        # Upload two files
        pdf_content = b"%PDF-1.4 test"
        self.client.post(
            "/api/materials/upload",
            data={"course_id": str(self.course_id), "file": (io.BytesIO(pdf_content), "file1.pdf")},
            content_type="multipart/form-data"
        )
        self.client.post(
            "/api/materials/upload",
            data={"course_id": str(self.course_id), "file": (io.BytesIO(pdf_content), "file2.pdf")},
            content_type="multipart/form-data"
        )

        # Get all
        res_all = self.client.get("/api/materials")
        self.assertEqual(res_all.status_code, 200)
        self.assertEqual(len(res_all.get_json()), 2)

        # Filter by course_id
        res_course = self.client.get(f"/api/materials?course_id={self.course_id}")
        self.assertEqual(res_course.status_code, 200)
        self.assertEqual(len(res_course.get_json()), 2)

        # Filter by non-existent course_id
        res_bad_course = self.client.get("/api/materials?course_id=9999")
        self.assertEqual(res_bad_course.status_code, 404)


if __name__ == "__main__":
    unittest.main()
