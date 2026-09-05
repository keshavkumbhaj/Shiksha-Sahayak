from flask import Blueprint, request, jsonify
from backend.database.models import CourseModel, UnitModel, TopicModel

syllabus_bp = Blueprint("syllabus", __name__)


@syllabus_bp.route("/courses/<int:course_id>/units", methods=["POST"])
def add_unit(course_id):
    """Add a new unit under an existing course."""
    try:
        course = CourseModel.get_by_id(course_id)
        if not course:
            return jsonify({"error": f"Course with ID {course_id} not found"}), 404

        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": "Request body must be valid JSON"}), 400

        unit_number = data.get("unit_number")
        if unit_number is None:
            return jsonify({"error": "unit_number is required"}), 400
        try:
            unit_number = int(unit_number)
        except (ValueError, TypeError):
            return jsonify({"error": "unit_number must be an integer"}), 400

        unit_name = data.get("unit_name")
        if not unit_name or not str(unit_name).strip():
            return jsonify({"error": "unit_name is required"}), 400

        unit = UnitModel.create(course_id, unit_number, str(unit_name).strip())
        return jsonify(unit), 201
    except Exception as e:
        return jsonify({"error": "Failed to add unit", "details": str(e)}), 500


@syllabus_bp.route("/units/<int:unit_id>/topics", methods=["POST"])
def add_topic(unit_id):
    """Add a new topic under an existing unit."""
    try:
        unit = UnitModel.get_by_id(unit_id)
        if not unit:
            return jsonify({"error": f"Unit with ID {unit_id} not found"}), 404

        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": "Request body must be valid JSON"}), 400

        topic_name = data.get("topic_name")
        if not topic_name or not str(topic_name).strip():
            return jsonify({"error": "topic_name is required"}), 400

        topic = TopicModel.create(unit_id, str(topic_name).strip())
        return jsonify(topic), 201
    except Exception as e:
        return jsonify({"error": "Failed to add topic", "details": str(e)}), 500


@syllabus_bp.route("/courses/<int:course_id>/topics", methods=["GET"])
def get_course_topics(course_id):
    """Get all topics across all units for a given course."""
    try:
        course = CourseModel.get_by_id(course_id)
        if not course:
            return jsonify({"error": f"Course with ID {course_id} not found"}), 404

        topics = TopicModel.get_by_course(course_id)
        return jsonify(topics), 200
    except Exception as e:
        return jsonify({"error": "Failed to fetch topics", "details": str(e)}), 500
