import json
from backend.database.db import get_db_connection

class CourseModel:
    @staticmethod
    def create(course_name, description=""):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO courses (course_name, description) VALUES (?, ?)",
            (course_name.strip(), description.strip() if description else "")
        )
        course_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return CourseModel.get_by_id(course_id)

    @staticmethod
    def get_all():
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT course_id, course_name, description FROM courses ORDER BY course_id ASC")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    @staticmethod
    def get_by_id(course_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT course_id, course_name, description FROM courses WHERE course_id = ?",
            (course_id,)
        )
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def get_with_units(course_id):
        course = CourseModel.get_by_id(course_id)
        if not course:
            return None
        course["units"] = UnitModel.get_by_course(course_id)
        return course


class UnitModel:
    @staticmethod
    def create(course_id, unit_number, unit_name):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO units (course_id, unit_number, unit_name) VALUES (?, ?, ?)",
            (course_id, int(unit_number), unit_name.strip())
        )
        unit_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return UnitModel.get_by_id(unit_id)

    @staticmethod
    def get_by_id(unit_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT unit_id, course_id, unit_number, unit_name FROM units WHERE unit_id = ?",
            (unit_id,)
        )
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def get_by_course(course_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT unit_id, course_id, unit_number, unit_name FROM units WHERE course_id = ? ORDER BY unit_number ASC",
            (course_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        units = []
        for row in rows:
            u = dict(row)
            u["topics"] = TopicModel.get_by_unit(u["unit_id"])
            units.append(u)
        return units


class TopicModel:
    @staticmethod
    def create(unit_id, topic_name):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO topics (unit_id, topic_name) VALUES (?, ?)",
            (unit_id, topic_name.strip())
        )
        topic_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return TopicModel.get_by_id(topic_id)

    @staticmethod
    def get_by_id(topic_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT topic_id, unit_id, topic_name FROM topics WHERE topic_id = ?",
            (topic_id,)
        )
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def get_by_unit(unit_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT topic_id, unit_id, topic_name FROM topics WHERE unit_id = ? ORDER BY topic_id ASC",
            (unit_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    @staticmethod
    def get_by_course(course_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT t.topic_id, t.topic_name, t.unit_id, u.unit_number, u.unit_name, u.course_id
            FROM topics t
            JOIN units u ON t.unit_id = u.unit_id
            WHERE u.course_id = ?
            ORDER BY u.unit_number ASC, t.topic_id ASC
        """, (course_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]


class MaterialModel:
    @staticmethod
    def create(course_id, file_name, file_path, processing_status="pending"):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO materials (course_id, file_name, file_path, processing_status)
            VALUES (?, ?, ?, ?)
        """, (course_id, file_name, file_path, processing_status))
        material_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return MaterialModel.get_by_id(material_id)

    @staticmethod
    def get_by_id(material_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT material_id, course_id, file_name, file_path, processing_status, uploaded_at
            FROM materials
            WHERE material_id = ?
        """, (material_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def get_all(course_id=None):
        conn = get_db_connection()
        cursor = conn.cursor()
        if course_id is not None:
            cursor.execute("""
                SELECT material_id, course_id, file_name, file_path, processing_status, uploaded_at
                FROM materials
                WHERE course_id = ?
                ORDER BY material_id DESC
            """, (course_id,))
        else:
            cursor.execute("""
                SELECT material_id, course_id, file_name, file_path, processing_status, uploaded_at
                FROM materials
                ORDER BY material_id DESC
            """)
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    @staticmethod
    def update_status(material_id, processing_status):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE materials
            SET processing_status = ?
            WHERE material_id = ?
        """, (processing_status, material_id))
        conn.commit()
        conn.close()
        return MaterialModel.get_by_id(material_id)


class AnswerModel:
    @staticmethod
    def create(topic_id, level, language, marks, mode, answer_text,
               source_reference="", source_verified=False, keywords_verified=False, approval_status="pending"):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO answers (topic_id, level, language, marks, mode, answer_text,
                                source_reference, source_verified, keywords_verified, approval_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            topic_id,
            level.lower(),
            language.lower(),
            int(marks),
            mode.lower(),
            answer_text,
            source_reference,
            1 if source_verified else 0,
            1 if keywords_verified else 0,
            approval_status
        ))
        answer_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return AnswerModel.get_by_id(answer_id)

    @staticmethod
    def get_by_id(answer_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT answer_id, topic_id, level, language, marks, mode, answer_text,
                   source_reference, source_verified, keywords_verified, approval_status
            FROM answers
            WHERE answer_id = ?
        """, (answer_id,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        d = dict(row)
        d["source_verified"] = bool(d["source_verified"])
        d["keywords_verified"] = bool(d["keywords_verified"])
        return d

    @staticmethod
    def get_all(approval_status=None):
        conn = get_db_connection()
        cursor = conn.cursor()
        if approval_status is not None:
            cursor.execute("""
                SELECT answer_id, topic_id, level, language, marks, mode, answer_text,
                       source_reference, source_verified, keywords_verified, approval_status
                FROM answers
                WHERE approval_status = ?
                ORDER BY answer_id DESC
            """, (str(approval_status).strip().lower(),))
        else:
            cursor.execute("""
                SELECT answer_id, topic_id, level, language, marks, mode, answer_text,
                       source_reference, source_verified, keywords_verified, approval_status
                FROM answers
                ORDER BY answer_id DESC
            """)
        rows = cursor.fetchall()
        conn.close()
        results = []
        for row in rows:
            d = dict(row)
            d["source_verified"] = bool(d["source_verified"])
            d["keywords_verified"] = bool(d["keywords_verified"])
            results.append(d)
        return results

    @staticmethod
    def update_approval(answer_id, approval_status):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE answers
            SET approval_status = ?
            WHERE answer_id = ?
        """, (approval_status, answer_id))
        conn.commit()
        conn.close()
        return AnswerModel.get_by_id(answer_id)


class AssessmentModel:
    @staticmethod
    def create(topic_id, total_questions, score=0):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO assessments (topic_id, total_questions, score)
            VALUES (?, ?, ?)
        """, (topic_id, int(total_questions), int(score)))
        assessment_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return AssessmentModel.get_by_id(assessment_id)

    @staticmethod
    def get_by_id(assessment_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT assessment_id, topic_id, total_questions, score
            FROM assessments
            WHERE assessment_id = ?
        """, (assessment_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def update_score(assessment_id, score):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE assessments
            SET score = ?
            WHERE assessment_id = ?
        """, (int(score), assessment_id))
        conn.commit()
        conn.close()
        return AssessmentModel.get_by_id(assessment_id)


class AssessmentQuestionModel:
    @staticmethod
    def create(assessment_id, question_text, options, correct_answer, topic_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        opts_str = json.dumps(options) if isinstance(options, (list, dict)) else str(options)
        cursor.execute("""
            INSERT INTO assessment_questions (assessment_id, question_text, options, correct_answer, topic_id)
            VALUES (?, ?, ?, ?, ?)
        """, (assessment_id, question_text, opts_str, str(correct_answer), topic_id))
        question_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return AssessmentQuestionModel.get_by_id(question_id)

    @staticmethod
    def get_by_id(question_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT question_id, assessment_id, question_text, options, correct_answer, topic_id
            FROM assessment_questions
            WHERE question_id = ?
        """, (question_id,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        d = dict(row)
        try:
            d["options"] = json.loads(d["options"])
        except Exception:
            pass
        return d

    @staticmethod
    def get_by_assessment(assessment_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT question_id, assessment_id, question_text, options, correct_answer, topic_id
            FROM assessment_questions
            WHERE assessment_id = ?
            ORDER BY question_id ASC
        """, (assessment_id,))
        rows = cursor.fetchall()
        conn.close()
        result = []
        for r in rows:
            d = dict(r)
            try:
                d["options"] = json.loads(d["options"])
            except Exception:
                pass
            result.append(d)
        return result


class WeakTopicModel:
    @staticmethod
    def record(topic_id, score, total):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO weak_topics (topic_id, score, total)
            VALUES (?, ?, ?)
        """, (topic_id, int(score), int(total)))
        weak_topic_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return WeakTopicModel.get_by_id(weak_topic_id)

    @staticmethod
    def get_by_id(weak_topic_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT w.weak_topic_id, w.topic_id, w.score, w.total, t.topic_name, u.unit_number, u.unit_name, u.course_id
            FROM weak_topics w
            JOIN topics t ON w.topic_id = t.topic_id
            JOIN units u ON t.unit_id = u.unit_id
            WHERE w.weak_topic_id = ?
        """, (weak_topic_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def get_all():
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT w.weak_topic_id, w.topic_id, w.score, w.total, t.topic_name, u.unit_number, u.unit_name, u.course_id
            FROM weak_topics w
            JOIN topics t ON w.topic_id = t.topic_id
            JOIN units u ON t.unit_id = u.unit_id
            ORDER BY w.weak_topic_id DESC
        """)
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
