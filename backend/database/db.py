import sqlite3
import os
from pathlib import Path
from backend.config import Config

def get_db_path():
    """Return database file path from configuration."""
    return Config.DATABASE_PATH

def get_db_connection():
    """Create and return an SQLite connection with Row factory and foreign keys enabled."""
    db_path = get_db_path()
    os.makedirs(Path(db_path).parent, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    """Initialize database tables strictly according to master specification Section 10."""
    conn = get_db_connection()
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

    conn.commit()
    conn.close()
