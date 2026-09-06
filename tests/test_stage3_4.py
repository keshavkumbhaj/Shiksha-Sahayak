import sys
import unittest
import tempfile
import os
from pathlib import Path

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.app import create_app
from backend.config import Config


class Stage3And4APITestCase(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        self.original_db_path = Config.DATABASE_PATH
        Config.DATABASE_PATH = self.db_path

        class TestConfig(Config):
            TESTING = True
            DATABASE_PATH = self.db_path

        self.app = create_app(TestConfig)
        self.client = self.app.test_client()

        # Seed core scenario: DBMS -> Unit 3 -> Normalization
        c_res = self.client.post("/api/courses", json={"course_name": "DBMS", "description": "Database Management Systems"})
        self.course_id = c_res.get_json()["course_id"]

        u_res = self.client.post(f"/api/courses/{self.course_id}/units", json={
            "unit_number": 3,
            "unit_name": "Unit 3: Normalization & Functional Dependencies"
        })
        self.unit_id = u_res.get_json()["unit_id"]

        t_res = self.client.post(f"/api/units/{self.unit_id}/topics", json={
            "topic_name": "Normalization"
        })
        self.topic_id = t_res.get_json()["topic_id"]

    def tearDown(self):
        Config.DATABASE_PATH = self.original_db_path
        os.close(self.db_fd)
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_generate_answer_success(self):
        payload = {
            "course_id": self.course_id,
            "topic_id": self.topic_id,
            "level": "intermediate",
            "language": "english",
            "marks": 5,
            "mode": "exam"
        }
        response = self.client.post("/api/answers/generate", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()

        # Verify Data Contract (Section 12)
        self.assertIn("answer", data)
        self.assertIn("source_reference", data)
        self.assertIn("source_verified", data)
        self.assertIn("keywords_verified", data)
        self.assertTrue(isinstance(data["source_verified"], bool))
        self.assertTrue(isinstance(data["keywords_verified"], bool))
        self.assertEqual(data["level"], "intermediate")
        self.assertEqual(data["marks"], 5)
        self.assertEqual(data["mode"], "exam")
        self.assertEqual(data["approval_status"], "pending")

    def test_generate_answer_validations(self):
        # Invalid level
        bad_level = self.client.post("/api/answers/generate", json={
            "course_id": self.course_id, "topic_id": self.topic_id,
            "level": "expert", "language": "english", "marks": 5, "mode": "exam"
        })
        self.assertEqual(bad_level.status_code, 400)

        # Invalid language
        bad_lang = self.client.post("/api/answers/generate", json={
            "course_id": self.course_id, "topic_id": self.topic_id,
            "level": "basic", "language": "french", "marks": 5, "mode": "exam"
        })
        self.assertEqual(bad_lang.status_code, 400)

        # Invalid marks (only 2, 5, 10 allowed)
        bad_marks = self.client.post("/api/answers/generate", json={
            "course_id": self.course_id, "topic_id": self.topic_id,
            "level": "basic", "language": "english", "marks": 15, "mode": "exam"
        })
        self.assertEqual(bad_marks.status_code, 400)

        # Non-existent topic
        bad_topic = self.client.post("/api/answers/generate", json={
            "course_id": self.course_id, "topic_id": 9999,
            "level": "basic", "language": "english", "marks": 5, "mode": "exam"
        })
        self.assertEqual(bad_topic.status_code, 404)

    def test_get_answer(self):
        gen_res = self.client.post("/api/answers/generate", json={
            "course_id": self.course_id, "topic_id": self.topic_id,
            "level": "intermediate", "language": "english", "marks": 5, "mode": "exam"
        })
        answer_id = gen_res.get_json()["answer_id"]

        get_res = self.client.get(f"/api/answers/{answer_id}")
        self.assertEqual(get_res.status_code, 200)
        data = get_res.get_json()
        self.assertEqual(data["answer_id"], answer_id)
        self.assertEqual(data["topic_id"], self.topic_id)
        self.assertIn("answer", data)

        # Non-existent
        not_found = self.client.get("/api/answers/9999")
        self.assertEqual(not_found.status_code, 404)

    def test_teacher_approve_and_reject(self):
        gen_res = self.client.post("/api/answers/generate", json={
            "course_id": self.course_id, "topic_id": self.topic_id,
            "level": "intermediate", "language": "english", "marks": 5, "mode": "exam"
        })
        answer_id = gen_res.get_json()["answer_id"]

        # Approve
        app_res = self.client.post(f"/api/answers/{answer_id}/approve")
        self.assertEqual(app_res.status_code, 200)
        self.assertEqual(app_res.get_json()["approval_status"], "approved")

        # Verify through GET
        ans_data = self.client.get(f"/api/answers/{answer_id}").get_json()
        self.assertEqual(ans_data["approval_status"], "approved")

        # Reject
        rej_res = self.client.post(f"/api/answers/{answer_id}/reject")
        self.assertEqual(rej_res.status_code, 200)
        self.assertEqual(rej_res.get_json()["approval_status"], "rejected")

        # Verify through GET
        ans_data_rej = self.client.get(f"/api/answers/{answer_id}").get_json()
        self.assertEqual(ans_data_rej["approval_status"], "rejected")

        # Non-existent answer approve/reject
        self.assertEqual(self.client.post("/api/answers/9999/approve").status_code, 404)
        self.assertEqual(self.client.post("/api/answers/9999/reject").status_code, 404)

    def test_get_answers_list(self):
        # Initial answers list empty
        empty_res = self.client.get("/api/answers")
        self.assertEqual(empty_res.status_code, 200)
        self.assertEqual(empty_res.get_json(), [])

        # Generate two answers
        res1 = self.client.post("/api/answers/generate", json={
            "course_id": self.course_id, "topic_id": self.topic_id,
            "level": "intermediate", "language": "english", "marks": 5, "mode": "exam"
        })
        ans1_id = res1.get_json()["answer_id"]

        res2 = self.client.post("/api/answers/generate", json={
            "course_id": self.course_id, "topic_id": self.topic_id,
            "level": "basic", "language": "english", "marks": 2, "mode": "exam"
        })
        ans2_id = res2.get_json()["answer_id"]

        # Approve answer 2
        self.client.post(f"/api/answers/{ans2_id}/approve")

        # Get all answers
        all_res = self.client.get("/api/answers")
        self.assertEqual(all_res.status_code, 200)
        all_answers = all_res.get_json()
        self.assertEqual(len(all_answers), 2)

        # Filter by pending
        pending_res = self.client.get("/api/answers?approval_status=pending")
        self.assertEqual(pending_res.status_code, 200)
        pending_list = pending_res.get_json()
        self.assertEqual(len(pending_list), 1)
        self.assertEqual(pending_list[0]["answer_id"], ans1_id)
        self.assertEqual(pending_list[0]["approval_status"], "pending")

        # Filter by approved
        approved_res = self.client.get("/api/answers?approval_status=approved")
        self.assertEqual(approved_res.status_code, 200)
        approved_list = approved_res.get_json()
        self.assertEqual(len(approved_list), 1)
        self.assertEqual(approved_list[0]["answer_id"], ans2_id)
        self.assertEqual(approved_list[0]["approval_status"], "approved")


if __name__ == "__main__":
    unittest.main()
