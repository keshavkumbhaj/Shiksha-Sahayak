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


class MasterDemonstrationE2ETestCase(unittest.TestCase):
    """
    End-to-End integration test following Section 6 & Section 22:
    - Teacher: Create DBMS course -> Define Unit 3 -> Add Normalization topic -> Upload DBMS PDF -> Process material
    - Student: Select DBMS -> Select Normalization -> Intermediate -> English -> 5 marks -> Exam Answer -> Generate
    - Teacher: Review and approve answer
    - Assessment: Generate MCQs -> Student answers -> Score calculated -> Weak topic identified -> Query weak topics
    """

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

    def tearDown(self):
        Config.DATABASE_PATH = self.original_db_path
        Config.UPLOAD_FOLDER = self.original_upload_folder
        os.close(self.db_fd)
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_complete_demonstration_scenario(self):
        # 1. Teacher creates DBMS course
        res_course = self.client.post("/api/courses", json={
            "course_name": "DBMS",
            "description": "Database Management Systems (CS-301)"
        })
        self.assertEqual(res_course.status_code, 201)
        course_id = res_course.get_json()["course_id"]

        # 2. Teacher defines Unit 3
        res_unit = self.client.post(f"/api/courses/{course_id}/units", json={
            "unit_number": 3,
            "unit_name": "Unit 3: Normalization & Functional Dependencies"
        })
        self.assertEqual(res_unit.status_code, 201)
        unit_id = res_unit.get_json()["unit_id"]

        # 3. Teacher adds Normalization topic
        res_topic = self.client.post(f"/api/units/{unit_id}/topics", json={
            "topic_name": "Normalization"
        })
        self.assertEqual(res_topic.status_code, 201)
        topic_id = res_topic.get_json()["topic_id"]

        # Verify course topics query
        res_topics = self.client.get(f"/api/courses/{course_id}/topics")
        self.assertEqual(res_topics.status_code, 200)
        self.assertEqual(len(res_topics.get_json()), 1)

        # 4. Teacher uploads DBMS PDF material
        pdf_content = b"%PDF-1.4 DBMS Unit 3 Normalization approved notes"
        res_upload = self.client.post(
            "/api/materials/upload",
            data={"course_id": str(course_id), "file": (io.BytesIO(pdf_content), "dbms_unit3.pdf")},
            content_type="multipart/form-data"
        )
        self.assertEqual(res_upload.status_code, 201)
        material_id = res_upload.get_json()["material_id"]

        # 5. Teacher processes material
        res_proc = self.client.post(f"/api/materials/{material_id}/process")
        self.assertEqual(res_proc.status_code, 200)

        # 6. Student generates answer (Intermediate + English + 5 marks + Exam Answer)
        student_request = {
            "course_id": course_id,
            "topic_id": topic_id,
            "level": "intermediate",
            "language": "english",
            "marks": 5,
            "mode": "exam"
        }
        res_answer = self.client.post("/api/answers/generate", json=student_request)
        self.assertEqual(res_answer.status_code, 200)
        answer_data = res_answer.get_json()
        self.assertIn("answer", answer_data)
        self.assertIn("source_reference", answer_data)
        self.assertTrue(answer_data["source_verified"])
        self.assertTrue(answer_data["keywords_verified"])
        self.assertEqual(answer_data["approval_status"], "pending")
        answer_id = answer_data["answer_id"]

        # 7. Teacher reviews and approves answer
        res_approve = self.client.post(f"/api/answers/{answer_id}/approve")
        self.assertEqual(res_approve.status_code, 200)
        self.assertEqual(res_approve.get_json()["approval_status"], "approved")

        # Verify answer status
        res_get_ans = self.client.get(f"/api/answers/{answer_id}")
        self.assertEqual(res_get_ans.status_code, 200)
        self.assertEqual(res_get_ans.get_json()["approval_status"], "approved")

        # 8. Student attempts MCQs
        res_mcq = self.client.post("/api/assessment/generate", json={
            "topic_id": topic_id,
            "num_questions": 3
        })
        self.assertEqual(res_mcq.status_code, 201)
        mcq_data = res_mcq.get_json()
        assessment_id = mcq_data["assessment_id"]
        questions = mcq_data["questions"]
        self.assertEqual(len(questions), 3)

        # 9. Student submits MCQ answers (score low to trigger weak topic flow)
        res_submit = self.client.post("/api/assessment/submit", json={
            "assessment_id": assessment_id,
            "answers": {
                str(questions[0]["question_id"]): "Incorrect Choice A",
                str(questions[1]["question_id"]): "Incorrect Choice B",
                str(questions[2]["question_id"]): "Incorrect Choice C"
            }
        })
        self.assertEqual(res_submit.status_code, 200)
        submit_data = res_submit.get_json()
        self.assertEqual(submit_data["score"], 0)
        self.assertTrue(submit_data["is_weak"])

        # 10. Weak topic is identified and can be retrieved for targeted revision
        res_weak = self.client.get("/api/assessment/weak-topics")
        self.assertEqual(res_weak.status_code, 200)
        weak_list = res_weak.get_json()
        self.assertEqual(len(weak_list), 1)
        self.assertEqual(weak_list[0]["topic_id"], topic_id)
        self.assertEqual(weak_list[0]["topic_name"], "Normalization")


if __name__ == "__main__":
    unittest.main()
