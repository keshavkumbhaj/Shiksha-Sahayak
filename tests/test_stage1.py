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
from backend.database.db import init_db


class Stage1APITestCase(unittest.TestCase):
    def setUp(self):
        # Create a temporary database for test isolation
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        self.original_db_path = Config.DATABASE_PATH
        Config.DATABASE_PATH = self.db_path
        
        class TestConfig(Config):
            TESTING = True
            DATABASE_PATH = self.db_path
            
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()

    def tearDown(self):
        Config.DATABASE_PATH = self.original_db_path
        os.close(self.db_fd)
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_health(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "online")

    def test_get_courses_empty(self):
        response = self.client.get("/api/courses")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), [])

    def test_create_course_success(self):
        payload = {
            "course_name": "Database Management Systems",
            "description": "CS-301 Core Course"
        }
        response = self.client.post("/api/courses", json=payload)
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertIn("course_id", data)
        self.assertEqual(data["course_name"], "Database Management Systems")
        self.assertEqual(data["description"], "CS-301 Core Course")

    def test_create_course_validation(self):
        # Empty payload
        response = self.client.post("/api/courses", json={})
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.get_json())

        # Whitespace only
        response = self.client.post("/api/courses", json={"course_name": "   "})
        self.assertEqual(response.status_code, 400)

    def test_get_course_by_id(self):
        # Create course first
        c_res = self.client.post("/api/courses", json={"course_name": "Operating Systems", "description": "CS-302"})
        course_id = c_res.get_json()["course_id"]

        # Fetch valid course
        response = self.client.get(f"/api/courses/{course_id}")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["course_id"], course_id)
        self.assertEqual(data["course_name"], "Operating Systems")
        self.assertEqual(data["units"], [])

        # Fetch non-existent course
        not_found = self.client.get("/api/courses/9999")
        self.assertEqual(not_found.status_code, 404)

    def test_add_unit_and_topic(self):
        # 1. Create Course
        c_res = self.client.post("/api/courses", json={"course_name": "DBMS", "description": "DBMS Course"})
        course_id = c_res.get_json()["course_id"]

        # 2. Add Unit
        u_res = self.client.post(f"/api/courses/{course_id}/units", json={
            "unit_number": 3,
            "unit_name": "Normalization & Functional Dependencies"
        })
        self.assertEqual(u_res.status_code, 201)
        unit_data = u_res.get_json()
        self.assertIn("unit_id", unit_data)
        self.assertEqual(unit_data["unit_number"], 3)
        self.assertEqual(unit_data["unit_name"], "Normalization & Functional Dependencies")
        unit_id = unit_data["unit_id"]

        # 3. Add Unit with invalid course_id
        invalid_u = self.client.post("/api/courses/9999/units", json={"unit_number": 1, "unit_name": "Unit 1"})
        self.assertEqual(invalid_u.status_code, 404)

        # 4. Add Unit validation failure
        bad_u = self.client.post(f"/api/courses/{course_id}/units", json={"unit_number": "not_an_int", "unit_name": "Unit"})
        self.assertEqual(bad_u.status_code, 400)

        # 5. Add Topic
        t_res = self.client.post(f"/api/units/{unit_id}/topics", json={
            "topic_name": "Normalization"
        })
        self.assertEqual(t_res.status_code, 201)
        topic_data = t_res.get_json()
        self.assertIn("topic_id", topic_data)
        self.assertEqual(topic_data["topic_name"], "Normalization")

        # 6. Add Topic with invalid unit_id
        invalid_t = self.client.post("/api/units/9999/topics", json={"topic_name": "Topic"})
        self.assertEqual(invalid_t.status_code, 404)

        # 7. Add Topic validation failure
        bad_t = self.client.post(f"/api/units/{unit_id}/topics", json={"topic_name": "  "})
        self.assertEqual(bad_t.status_code, 400)

        # 8. Fetch Course Topics
        topics_res = self.client.get(f"/api/courses/{course_id}/topics")
        self.assertEqual(topics_res.status_code, 200)
        topics = topics_res.get_json()
        self.assertEqual(len(topics), 1)
        self.assertEqual(topics[0]["topic_name"], "Normalization")
        self.assertEqual(topics[0]["unit_number"], 3)

        # 9. Fetch Course with Units/Topics
        full_course = self.client.get(f"/api/courses/{course_id}").get_json()
        self.assertEqual(len(full_course["units"]), 1)
        self.assertEqual(len(full_course["units"][0]["topics"]), 1)
        self.assertEqual(full_course["units"][0]["topics"][0]["topic_name"], "Normalization")


if __name__ == "__main__":
    unittest.main()
