from flask import Blueprint, request, jsonify
from backend.database.models import CourseModel

courses_bp = Blueprint("courses", __name__)


@courses_bp.route("/courses", methods=["GET"])
def get_courses():
    """Retrieve all available courses."""
    try:
        courses = CourseModel.get_all()
        return jsonify(courses), 200
    except Exception as e:
        return jsonify({"error": "Failed to fetch courses", "details": str(e)}), 500


@courses_bp.route("/courses", methods=["POST"])
def create_course():
    """Create a new course."""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    course_name = data.get("course_name")
    if not course_name or not str(course_name).strip():
        return jsonify({"error": "course_name is required"}), 400

    description = data.get("description", "")
    if description is None:
        description = ""

    try:
        course = CourseModel.create(str(course_name).strip(), str(description).strip())
        return jsonify(course), 201
    except Exception as e:
        return jsonify({"error": "Failed to create course", "details": str(e)}), 500


@courses_bp.route("/courses/<int:course_id>", methods=["GET"])
def get_course(course_id):
    """Retrieve a course by its ID including its syllabus units and topics."""
    try:
        course = CourseModel.get_with_units(course_id)
        if not course:
            return jsonify({"error": f"Course with ID {course_id} not found"}), 404
        return jsonify(course), 200
    except Exception as e:
        return jsonify({"error": "Failed to fetch course", "details": str(e)}), 500
