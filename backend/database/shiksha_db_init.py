import sqlite3
import os
import json
from pathlib import Path
from contextlib import contextmanager

DEFAULT_DB_PATH = str(Path(__file__).resolve().parent.parent.parent / "data" / "shiksha_sahayak.db")

def get_db_path():
    """Return database file path from configuration or environment, with safe fallback."""
    try:
        from backend.config import Config
        return Config.DATABASE_PATH
    except Exception:
        return os.environ.get("DATABASE_PATH", DEFAULT_DB_PATH)

def get_db_connection(db_path=None):
    """
    Create and return an SQLite connection with Row factory and foreign keys enabled.
    Supports passing an explicit database path or in-memory database.
    """
    path = db_path if db_path is not None else get_db_path()
    if path != ":memory:":
        os.makedirs(Path(path).parent, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

@contextmanager
def get_db_context(db_path=None, commit=True):
    """
    Context manager for database connections.
    Guarantees that connections are closed safely and rolls back transactions on error.
    """
    conn = get_db_connection(db_path)
    try:
        yield conn
        if commit:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db(db_path=None):
    """
    Initialize database tables and indexes strictly according to master specification Section 10.
    Enforces foreign keys, ON DELETE CASCADE, and performance indexes.
    """
    conn = get_db_connection(db_path)
    try:
        cursor = conn.cursor()

        # 1. courses
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            course_id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_name TEXT NOT NULL,
            description TEXT
        );
        """)

        # 2. units
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS units (
            unit_id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER NOT NULL,
            unit_number INTEGER NOT NULL,
            unit_name TEXT NOT NULL,
            FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE CASCADE
        );
        """)

        # 3. topics
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS topics (
            topic_id INTEGER PRIMARY KEY AUTOINCREMENT,
            unit_id INTEGER NOT NULL,
            topic_name TEXT NOT NULL,
            FOREIGN KEY (unit_id) REFERENCES units(unit_id) ON DELETE CASCADE
        );
        """)

        # 4. materials
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS materials (
            material_id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER NOT NULL,
            file_name TEXT NOT NULL,
            file_path TEXT NOT NULL,
            processing_status TEXT NOT NULL DEFAULT 'pending',
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE CASCADE
        );
        """)

        # 5. answers
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS answers (
            answer_id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic_id INTEGER NOT NULL,
            level TEXT NOT NULL,
            language TEXT NOT NULL,
            marks INTEGER NOT NULL,
            mode TEXT NOT NULL,
            answer_text TEXT NOT NULL,
            source_reference TEXT,
            source_verified INTEGER DEFAULT 0,
            keywords_verified INTEGER DEFAULT 0,
            approval_status TEXT DEFAULT 'pending',
            FOREIGN KEY (topic_id) REFERENCES topics(topic_id) ON DELETE CASCADE
        );
        """)

        # 6. assessments
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS assessments (
            assessment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic_id INTEGER NOT NULL,
            total_questions INTEGER NOT NULL,
            score INTEGER DEFAULT 0,
            FOREIGN KEY (topic_id) REFERENCES topics(topic_id) ON DELETE CASCADE
        );
        """)

        # 7. assessment_questions
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS assessment_questions (
            question_id INTEGER PRIMARY KEY AUTOINCREMENT,
            assessment_id INTEGER NOT NULL,
            question_text TEXT NOT NULL,
            options TEXT NOT NULL,
            correct_answer TEXT NOT NULL,
            topic_id INTEGER NOT NULL,
            FOREIGN KEY (assessment_id) REFERENCES assessments(assessment_id) ON DELETE CASCADE,
            FOREIGN KEY (topic_id) REFERENCES topics(topic_id) ON DELETE CASCADE
        );
        """)

        # 8. weak_topics
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS weak_topics (
            weak_topic_id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic_id INTEGER NOT NULL,
            score INTEGER NOT NULL,
            total INTEGER NOT NULL,
            FOREIGN KEY (topic_id) REFERENCES topics(topic_id) ON DELETE CASCADE
        );
        """)

        # Relational Indexes for query performance and fast joins
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_units_course_id ON units(course_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_topics_unit_id ON topics(unit_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_materials_course_id ON materials(course_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_answers_topic_id ON answers(topic_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_assessments_topic_id ON assessments(topic_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_assessment_questions_assessment_id ON assessment_questions(assessment_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_assessment_questions_topic_id ON assessment_questions(topic_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_weak_topics_topic_id ON weak_topics(topic_id);")

        conn.commit()
    finally:
        conn.close()

def seed_sample_data(db_path=None):
    """
    Seed canonical demonstration data (Section 6 & 22 Specification):
    Course: DBMS
    Unit: Unit 3 (Normalization & Functional Dependencies)
    Topic: Normalization
    Material: DBMS Unit 3 Approved Notes
    Answer: 5 Marks, Intermediate, English, Exam Mode
    Assessment: 3 Questions
    Weak Topic: Normalization identified for revision
    """
    init_db(db_path)
    conn = get_db_connection(db_path)
    try:
        cursor = conn.cursor()

        # Check if DBMS already exists
        cursor.execute("SELECT course_id FROM courses WHERE course_name = ?", ("DBMS",))
        existing_course = cursor.fetchone()
        if existing_course:
            course_id = existing_course["course_id"]
        else:
            cursor.execute(
                "INSERT INTO courses (course_name, description) VALUES (?, ?)",
                ("DBMS", "Database Management Systems (CS-301 Core Course)")
            )
            course_id = cursor.lastrowid

        # Unit 3
        cursor.execute(
            "SELECT unit_id FROM units WHERE course_id = ? AND unit_number = ?",
            (course_id, 3)
        )
        existing_unit = cursor.fetchone()
        if existing_unit:
            unit_id = existing_unit["unit_id"]
        else:
            cursor.execute(
                "INSERT INTO units (course_id, unit_number, unit_name) VALUES (?, ?, ?)",
                (course_id, 3, "Unit 3: Normalization & Functional Dependencies")
            )
            unit_id = cursor.lastrowid

        # Topic: Normalization
        cursor.execute(
            "SELECT topic_id FROM topics WHERE unit_id = ? AND topic_name = ?",
            (unit_id, "Normalization")
        )
        existing_topic = cursor.fetchone()
        if existing_topic:
            topic_id = existing_topic["topic_id"]
        else:
            cursor.execute(
                "INSERT INTO topics (unit_id, topic_name) VALUES (?, ?)",
                (unit_id, "Normalization")
            )
            topic_id = cursor.lastrowid

        # Material
        cursor.execute(
            "SELECT material_id FROM materials WHERE course_id = ? AND file_name = ?",
            (course_id, "dbms_unit3_normalization.pdf")
        )
        if not cursor.fetchone():
            cursor.execute(
                """INSERT INTO materials (course_id, file_name, file_path, processing_status)
                   VALUES (?, ?, ?, ?)""",
                (course_id, "dbms_unit3_normalization.pdf", "data/uploads/dbms_unit3_normalization.pdf", "processed")
            )

        # Answer
        cursor.execute(
            "SELECT answer_id FROM answers WHERE topic_id = ? AND marks = 5 AND level = 'intermediate'",
            (topic_id,)
        )
        if not cursor.fetchone():
            answer_content = (
                "Normalization is the systematic process of organizing data in a relational database "
                "to minimize data redundancy and prevent insertion, deletion, and update anomalies. "
                "It involves decomposing large unnormalized tables into smaller, well-structured relations "
                "by analyzing functional dependencies.\n\n"
                "Key Normal Forms:\n"
                "1. First Normal Form (1NF): Eliminates repeating groups and ensures every attribute contains atomic values.\n"
                "2. Second Normal Form (2NF): Must be in 1NF and eliminate partial dependency (every non-prime attribute is fully functionally dependent on candidate keys).\n"
                "3. Third Normal Form (3NF): Must be in 2NF and eliminate transitive dependency (no non-prime attribute depends on another non-prime attribute).\n"
                "4. Boyce-Codd Normal Form (BCNF): A stricter version of 3NF where for every functional dependency X -> Y, X must be a super key."
            )
            cursor.execute(
                """INSERT INTO answers (topic_id, level, language, marks, mode, answer_text,
                                        source_reference, source_verified, keywords_verified, approval_status)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    topic_id, "intermediate", "english", 5, "exam",
                    answer_content, "DBMS Unit 3 - Page 12", 1, 1, "approved"
                )
            )

        # Assessment & Questions
        cursor.execute(
            "SELECT assessment_id FROM assessments WHERE topic_id = ?",
            (topic_id,)
        )
        existing_assessment = cursor.fetchone()
        if not existing_assessment:
            cursor.execute(
                "INSERT INTO assessments (topic_id, total_questions, score) VALUES (?, ?, ?)",
                (topic_id, 3, 1)
            )
            assessment_id = cursor.lastrowid

            questions = [
                {
                    "question_text": "Which condition is required for a relational schema to be in 2NF regarding Normalization?",
                    "options": [
                        "It is in 1NF and has no partial dependency",
                        "It has transitive dependencies only",
                        "Every attribute is a primary key",
                        "It must contain multivalued dependencies"
                    ],
                    "correct_answer": "It is in 1NF and has no partial dependency"
                },
                {
                    "question_text": "In Normalization, what defines Boyce-Codd Normal Form (BCNF)?",
                    "options": [
                        "Every determinant must be a candidate key",
                        "Eliminating partial functional dependency only",
                        "Permitting non-trivial multivalued dependencies",
                        "Allowing composite primary keys without 1NF"
                    ],
                    "correct_answer": "Every determinant must be a candidate key"
                },
                {
                    "question_text": "What is the primary objective of Normalization in relational database design?",
                    "options": [
                        "Minimizing data redundancy and insertion/deletion anomalies",
                        "Increasing table file size for faster scanning",
                        "Converting all attributes to JSON text fields",
                        "Bypassing referential integrity checks"
                    ],
                    "correct_answer": "Minimizing data redundancy and insertion/deletion anomalies"
                }
            ]

            for q in questions:
                cursor.execute(
                    """INSERT INTO assessment_questions (assessment_id, question_text, options, correct_answer, topic_id)
                       VALUES (?, ?, ?, ?, ?)""",
                    (assessment_id, q["question_text"], json.dumps(q["options"]), q["correct_answer"], topic_id)
                )

        # Weak Topic
        cursor.execute(
            "SELECT weak_topic_id FROM weak_topics WHERE topic_id = ?",
            (topic_id,)
        )
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO weak_topics (topic_id, score, total) VALUES (?, ?, ?)",
                (topic_id, 1, 3)
            )

        conn.commit()
        return {
            "course_id": course_id,
            "unit_id": unit_id,
            "topic_id": topic_id
        }
    finally:
        conn.close()

if __name__ == "__main__":
    db_target = get_db_path()
    init_db(db_target)
    seed_sample_data(db_target)
    print(f"Shiksha Sahayak database successfully initialized and seeded at: {db_target}")
