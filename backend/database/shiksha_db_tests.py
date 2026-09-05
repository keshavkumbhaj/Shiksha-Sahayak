import json
from backend.database.db import get_db_connection


class CourseModel:
    @staticmethod
    def create(course_name, description="", db_path=None):
        conn = get_db_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO courses (course_name, description) VALUES (?, ?)",
                (str(course_name).strip(), str(description).strip() if description else "")
            )
            course_id = cursor.lastrowid
            conn.commit()
            return CourseModel.get_by_id(course_id, db_path=db_path)
        finally:
            conn.close()

    @staticmethod
    def get_all(db_path=None):
        conn = get_db_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT course_id, course_name, description FROM courses ORDER BY course_id ASC")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    @staticmethod
    def get_by_id(course_id, db_path=None):
        conn = get_db_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT course_id, course_name, description FROM courses WHERE course_id = ?",
                (course_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    @staticmethod
    def get_with_units(course_id, db_path=None):
        course = CourseModel.get_by_id(course_id, db_path=db_path)
        if not course:
            return None
        course["units"] = UnitModel.get_by_course(course_id, db_path=db_path)
        return course

    @staticmethod
    def delete(course_id, db_path=None):
        conn = get_db_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM courses WHERE course_id = ?", (course_id,))
            deleted = cursor.rowcount > 0
            conn.commit()
            return deleted
        finally:
            conn.close()


class UnitModel:
    @staticmethod
    def create(course_id, unit_number, unit_name, db_path=None):
        conn = get_db_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO units (course_id, unit_number, unit_name) VALUES (?, ?, ?)",
                (course_id, int(unit_number), str(unit_name).strip())
            )
            unit_id = cursor.lastrowid
            conn.commit()
            return UnitModel.get_by_id(unit_id, db_path=db_path)
        finally:
            conn.close()

    @staticmethod
    def get_by_id(unit_id, db_path=None):
        conn = get_db_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT unit_id, course_id, unit_number, unit_name FROM units WHERE unit_id = ?",
                (unit_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    @staticmethod
    def get_by_course(course_id, db_path=None):
        conn = get_db_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT unit_id, course_id, unit_number, unit_name FROM units WHERE course_id = ? ORDER BY unit_number ASC",
                (course_id,)
            )
            rows = cursor.fetchall()
            units = []
            for row in rows:
                u = dict(row)
                u["topics"] = TopicModel.get_by_unit(u["unit_id"], db_path=db_path)
                units.append(u)
            return units
        finally:
            conn.close()

    @staticmethod
    def delete(unit_id, db_path=None):
        conn = get_db_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM units WHERE unit_id = ?", (unit_id,))
            deleted = cursor.rowcount > 0
            conn.commit()
            return deleted
        finally:
            conn.close()


class TopicModel:
    @staticmethod
    def create(unit_id, topic_name, db_path=None):
        conn = get_db_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO topics (unit_id, topic_name) VALUES (?, ?)",
                (unit_id, str(topic_name).strip())
            )
            topic_id = cursor.lastrowid
            conn.commit()
            return TopicModel.get_by_id(topic_id, db_path=db_path)
        finally:
            conn.close()

    @staticmethod
    def get_by_id(topic_id, db_path=None):
        conn = get_db_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT topic_id, unit_id, topic_name FROM topics WHERE topic_id = ?",
                (topic_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    @staticmethod
    def get_by_unit(unit_id, db_path=None):
        conn = get_db_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT topic_id, unit_id, topic_name FROM topics WHERE unit_id = ? ORDER BY topic_id ASC",
                (unit_id,)
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    @staticmethod
    def get_by_course(course_id, db_path=None):
        conn = get_db_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT t.topic_id, t.topic_name, t.unit_id, u.unit_number, u.unit_name, u.course_id
                FROM topics t
                JOIN units u ON t.unit_id = u.unit_id
                WHERE u.course_id = ?
                ORDER BY u.unit_number ASC, t.topic_id ASC
            """, (course_id,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    @staticmethod
    def delete(topic_id, db_path=None):
        conn = get_db_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM topics WHERE topic_id = ?", (topic_id,))
            deleted = cursor.rowcount > 0
            conn.commit()
            return deleted
        finally:
            conn.close()


class MaterialModel:
    @staticmethod
    def create(course_id, file_name, file_path, processing_status="pending", db_path=None):
        conn = get_db_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO materials (course_id, file_name, file_path, processing_status)
                VALUES (?, ?, ?, ?)
            """, (course_id, file_name, file_path, processing_status))
            material_id = cursor.lastrowid
            conn.commit()
            return MaterialModel.get_by_id(material_id, db_path=db_path)
        finally:
            conn.close()

    @staticmethod
    def get_by_id(material_id, db_path=None):
        conn = get_db_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT material_id, course_id, file_name, file_path, processing_status, uploaded_at
                FROM materials
                WHERE material_id = ?
            """, (material_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    @staticmethod
    def get_all(course_id=None, db_path=None):
        conn = get_db_connection(db_path)
        try:
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
            return [dict(row) for row in rows]
        finally:
            conn.close()

    @staticmethod
    def update_status(material_id, processing_status, db_path=None):
        conn = get_db_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE materials
                SET processing_status = ?
                WHERE material_id = ?
            """, (processing_status, material_id))
            conn.commit()
            return MaterialModel.get_by_id(material_id, db_path=db_path)
        finally:
            conn.close()

    @staticmethod
    def delete(material_id, db_path=None):
        conn = get_db_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM materials WHERE material_id = ?", (material_id,))
            deleted = cursor.rowcount > 0
            conn.commit()
            return deleted
        finally:
            conn.close()


class AnswerModel:
    @staticmethod
    def create(topic_id, level, language, marks, mode, answer_text,
               source_reference="", source_verified=False, keywords_verified=False,
               approval_status="pending", db_path=None):
        conn = get_db_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO answers (topic_id, level, language, marks, mode, answer_text,
                                    source_reference, source_verified, keywords_verified, approval_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                topic_id,
                str(level).strip().lower(),
                str(language).strip().lower(),
                int(marks),
                str(mode).strip().lower(),
                str(answer_text),
                str(source_reference),
                1 if source_verified else 0,
                1 if keywords_verified else 0,
                str(approval_status).strip().lower()
            ))
            answer_id = cursor.lastrowid
            conn.commit()
            return AnswerModel.get_by_id(answer_id, db_path=db_path)
        finally:
            conn.close()

    @staticmethod
    def get_by_id(answer_id, db_path=None):
        conn = get_db_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT answer_id, topic_id, level, language, marks, mode, answer_text,
                       source_reference, source_verified, keywords_verified, approval_status
                FROM answers
                WHERE answer_id = ?
            """, (answer_id,))
            row = cursor.fetchone()
            if not row:
                return None
            d = dict(row)
            d["source_verified"] = bool(d["source_verified"])
            d["keywords_verified"] = bool(d["keywords_verified"])
            return d
        finally:
            conn.close()

    @staticmethod
    def get_by_topic(topic_id, db_path=None):
        conn = get_db_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT answer_id, topic_id, level, language, marks, mode, answer_text,
                       source_reference, source_verified, keywords_verified, approval_status
                FROM answers
                WHERE topic_id = ?
                ORDER BY answer_id DESC
            """, (topic_id,))
            rows = cursor.fetchall()
            results = []
            for r in rows:
                d = dict(r)
                d["source_verified"] = bool(d["source_verified"])
                d["keywords_verified"] = bool(d["keywords_verified"])
                results.append(d)
            return results
        finally:
            conn.close()

    @staticmethod
    def update_approval(answer_id, approval_status, db_path=None):
        conn = get_db_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE answers
                SET approval_status = ?
                WHERE answer_id = ?
            """, (str(approval_status).strip().lower(), answer_id))
            conn.commit()
            return AnswerModel.get_by_id(answer_id, db_path=db_path)
        finally:
            conn.close()

    @staticmethod
    def delete(answer_id, db_path=None):
        conn = get_db_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM answers WHERE answer_id = ?", (answer_id,))
            deleted = cursor.rowcount > 0
            conn.commit()
            return deleted
        finally:
            conn.close()


class AssessmentModel:
    @staticmethod
    def create(topic_id, total_questions, score=0, db_path=None):
        conn = get_db_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO assessments (topic_id, total_questions, score)
                VALUES (?, ?, ?)
            """, (topic_id, int(total_questions), int(score)))
            assessment_id = cursor.lastrowid
            conn.commit()
            return AssessmentModel.get_by_id(assessment_id, db_path=db_path)
        finally:
            conn.close()

    @staticmethod
    def get_by_id(assessment_id, db_path=None):
        conn = get_db_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT assessment_id, topic_id, total_questions, score
                FROM assessments
                WHERE assessment_id = ?
            """, (assessment_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    @staticmethod
    def get_by_topic(topic_id, db_path=None):
        conn = get_db_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT assessment_id, topic_id, total_questions, score
                FROM assessments
                WHERE topic_id = ?
                ORDER BY assessment_id DESC
            """, (topic_id,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    @staticmethod
    def update_score(assessment_id, score, db_path=None):
        conn = get_db_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE assessments
                SET score = ?
                WHERE assessment_id = ?
            """, (int(score), assessment_id))
            conn.commit()
            return AssessmentModel.get_by_id(assessment_id, db_path=db_path)
        finally:
            conn.close()

    @staticmethod
    def delete(assessment_id, db_path=None):
        conn = get_db_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM assessments WHERE assessment_id = ?", (assessment_id,))
            deleted = cursor.rowcount > 0
            conn.commit()
            return deleted
        finally:
            conn.close()


class AssessmentQuestionModel:
    @staticmethod
    def create(assessment_id, question_text, options, correct_answer, topic_id, db_path=None):
        conn = get_db_connection(db_path)
        try:
            cursor = conn.cursor()
            opts_str = json.dumps(options) if isinstance(options, (list, dict)) else str(options)
            cursor.execute("""
                INSERT INTO assessment_questions (assessment_id, question_text, options, correct_answer, topic_id)
                VALUES (?, ?, ?, ?, ?)
            """, (assessment_id, str(question_text), opts_str, str(correct_answer), topic_id))
            question_id = cursor.lastrowid
            conn.commit()
            return AssessmentQuestionModel.get_by_id(question_id, db_path=db_path)
        finally:
            conn.close()

    @staticmethod
    def get_by_id(question_id, db_path=None):
        conn = get_db_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT question_id, assessment_id, question_text, options, correct_answer, topic_id
                FROM assessment_questions
                WHERE question_id = ?
            """, (question_id,))
            row = cursor.fetchone()
            if not row:
                return None
            d = dict(row)
            try:
                d["options"] = json.loads(d["options"])
            except Exception:
                pass
            return d
        finally:
            conn.close()

    @staticmethod
    def get_by_assessment(assessment_id, db_path=None):
        conn = get_db_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT question_id, assessment_id, question_text, options, correct_answer, topic_id
                FROM assessment_questions
                WHERE assessment_id = ?
                ORDER BY question_id ASC
            """, (assessment_id,))
            rows = cursor.fetchall()
            result = []
            for r in rows:
                d = dict(r)
                try:
                    d["options"] = json.loads(d["options"])
                except Exception:
                    pass
                result.append(d)
            return result
        finally:
            conn.close()

    @staticmethod
    def get_by_topic(topic_id, db_path=None):
        conn = get_db_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT question_id, assessment_id, question_text, options, correct_answer, topic_id
                FROM assessment_questions
                WHERE topic_id = ?
                ORDER BY question_id ASC
            """, (topic_id,))
            rows = cursor.fetchall()
            result = []
            for r in rows:
                d = dict(r)
                try:
                    d["options"] = json.loads(d["options"])
                except Exception:
                    pass
                result.append(d)
            return result
        finally:
            conn.close()

    @staticmethod
    def delete(question_id, db_path=None):
        conn = get_db_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM assessment_questions WHERE question_id = ?", (question_id,))
            deleted = cursor.rowcount > 0
            conn.commit()
            return deleted
        finally:
            conn.close()


class WeakTopicModel:
    @staticmethod
    def record(topic_id, score, total, db_path=None):
        conn = get_db_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO weak_topics (topic_id, score, total)
                VALUES (?, ?, ?)
            """, (topic_id, int(score), int(total)))
            weak_topic_id = cursor.lastrowid
            conn.commit()
            return WeakTopicModel.get_by_id(weak_topic_id, db_path=db_path)
        finally:
            conn.close()

    @staticmethod
    def get_by_id(weak_topic_id, db_path=None):
        conn = get_db_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT w.weak_topic_id, w.topic_id, w.score, w.total, t.topic_name,
                       u.unit_number, u.unit_name, u.course_id, c.course_name
                FROM weak_topics w
                JOIN topics t ON w.topic_id = t.topic_id
                JOIN units u ON t.unit_id = u.unit_id
                JOIN courses c ON u.course_id = c.course_id
                WHERE w.weak_topic_id = ?
            """, (weak_topic_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    @staticmethod
    def get_by_topic(topic_id, db_path=None):
        conn = get_db_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT w.weak_topic_id, w.topic_id, w.score, w.total, t.topic_name,
                       u.unit_number, u.unit_name, u.course_id, c.course_name
                FROM weak_topics w
                JOIN topics t ON w.topic_id = t.topic_id
                JOIN units u ON t.unit_id = u.unit_id
                JOIN courses c ON u.course_id = c.course_id
                WHERE w.topic_id = ?
                ORDER BY w.weak_topic_id DESC
            """, (topic_id,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    @staticmethod
    def get_all(db_path=None):
        conn = get_db_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT w.weak_topic_id, w.topic_id, w.score, w.total, t.topic_name,
                       u.unit_number, u.unit_name, u.course_id, c.course_name
                FROM weak_topics w
                JOIN topics t ON w.topic_id = t.topic_id
                JOIN units u ON t.unit_id = u.unit_id
                JOIN courses c ON u.course_id = c.course_id
                ORDER BY w.weak_topic_id DESC
            """)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    @staticmethod
    def delete(weak_topic_id, db_path=None):
        conn = get_db_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM weak_topics WHERE weak_topic_id = ?", (weak_topic_id,))
            deleted = cursor.rowcount > 0
            conn.commit()
            return deleted
        finally:
            conn.close()

