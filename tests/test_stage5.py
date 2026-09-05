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


class Stage5AssessmentAPITestCase(unittest.TestCase):
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
        c_res = self.client.post("/api/courses", json={"course_name": "DBMS", "description": "Database Systems"})
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

    def test_generate_assessment_success(self):
        res = self.client.post("/api/assessment/generate", json={"topic_id": self.topic_id, "num_questions": 3})
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertIn("assessment_id", data)
        self.assertEqual(data["topic_id"], self.topic_id)
        self.assertEqual(data["total_questions"], 3)
        self.assertEqual(len(data["questions"]), 3)
        for q in data["questions"]:
            self.assertIn("question_id", q)
            self.assertIn("question_text", q)
            self.assertIn("options", q)
            self.assertEqual(len(q["options"]), 4)

    def test_generate_assessment_validation(self):
        # Missing topic_id
        res_no_topic = self.client.post("/api/assessment/generate", json={})
        self.assertEqual(res_no_topic.status_code, 400)

        # Non-existent topic_id
        res_bad_topic = self.client.post("/api/assessment/generate", json={"topic_id": 9999})
        self.assertEqual(res_bad_topic.status_code, 404)

    def test_submit_assessment_perfect_score(self):
        gen_res = self.client.post("/api/assessment/generate", json={"topic_id": self.topic_id, "num_questions": 3})
        gen_data = gen_res.get_json()
        assessment_id = gen_data["assessment_id"]
        questions = gen_data["questions"]

        # Provide all correct answers
        # From mock questions, answers are:
        # 1: "It is in 1NF and has no partial dependency"
        # 2: "Every determinant must be a candidate key"
        # 3: "Minimizing data redundancy and insertion/deletion anomalies"
        answers = {
            str(questions[0]["question_id"]): "It is in 1NF and has no partial dependency",
            str(questions[1]["question_id"]): "Every determinant must be a candidate key",
            str(questions[2]["question_id"]): "Minimizing data redundancy and insertion/deletion anomalies"
        }

        sub_res = self.client.post("/api/assessment/submit", json={
            "assessment_id": assessment_id,
            "answers": answers
        })
        self.assertEqual(sub_res.status_code, 200)
        sub_data = sub_res.get_json()
        self.assertEqual(sub_data["score"], 3)
        self.assertEqual(sub_data["total_questions"], 3)
        self.assertEqual(sub_data["percentage"], 100.0)
        self.assertFalse(sub_data["is_weak"])

        # Weak topics list should be empty
        wt_res = self.client.get("/api/assessment/weak-topics")
        self.assertEqual(wt_res.status_code, 200)
        self.assertEqual(len(wt_res.get_json()), 0)

    def test_submit_assessment_weak_score_and_topic_recording(self):
        gen_res = self.client.post("/api/assessment/generate", json={"topic_id": self.topic_id, "num_questions": 3})
        gen_data = gen_res.get_json()
        assessment_id = gen_data["assessment_id"]
        questions = gen_data["questions"]

        # Provide incorrect answers (score = 0)
        answers = {
            str(questions[0]["question_id"]): "Wrong Answer 1",
            str(questions[1]["question_id"]): "Wrong Answer 2",
            str(questions[2]["question_id"]): "Wrong Answer 3"
        }

        sub_res = self.client.post("/api/assessment/submit", json={
            "assessment_id": assessment_id,
            "answers": answers
        })
        self.assertEqual(sub_res.status_code, 200)
        sub_data = sub_res.get_json()
        self.assertEqual(sub_data["score"], 0)
        self.assertEqual(sub_data["total_questions"], 3)
        self.assertTrue(sub_data["is_weak"])

        # Check weak topics API
        wt_res = self.client.get("/api/assessment/weak-topics")
        self.assertEqual(wt_res.status_code, 200)
        wt_list = wt_res.get_json()
        self.assertEqual(len(wt_list), 1)
        self.assertEqual(wt_list[0]["topic_id"], self.topic_id)
        self.assertEqual(wt_list[0]["topic_name"], "Normalization")
        self.assertEqual(wt_list[0]["score"], 0)
        self.assertEqual(wt_list[0]["total"], 3)


if __name__ == "__main__":
    unittest.main()
