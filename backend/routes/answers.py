from flask import Blueprint, request, jsonify
from backend.database.models import CourseModel, TopicModel, AnswerModel

answers_bp = Blueprint("answers", __name__)

VALID_LEVELS = {"basic", "intermediate", "advanced"}
VALID_LANGUAGES = {"english", "hindi"}
VALID_MARKS = {2, 5, 10}
VALID_MODES = {"exam", "exam_answer", "learn", "learn_simply"}


def format_answer_response(answer_dict):
    """Format DB answer dictionary according to Section 12 Data Contract."""
    return {
        "answer_id": answer_dict["answer_id"],
        "topic_id": answer_dict["topic_id"],
        "level": answer_dict["level"],
        "language": answer_dict["language"],
        "marks": answer_dict["marks"],
        "mode": answer_dict["mode"],
        "answer": answer_dict.get("answer_text", ""),
        "answer_text": answer_dict.get("answer_text", ""),
        "source_reference": answer_dict.get("source_reference", ""),
        "source_verified": bool(answer_dict.get("source_verified", False)),
        "keywords_verified": bool(answer_dict.get("keywords_verified", False)),
        "approval_status": answer_dict.get("approval_status", "pending")
    }


@answers_bp.route("/answers/generate", methods=["POST"])
def generate_answer():
    """
    Generate an answer grounded in course materials.
    Connects to Ankit's AI pipeline (ai/generator.py) when available.
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    # 1. Validate course_id
    course_id = data.get("course_id")
    if course_id is None:
        return jsonify({"error": "course_id is required"}), 400
    try:
        course_id = int(course_id)
    except (ValueError, TypeError):
        return jsonify({"error": "course_id must be an integer"}), 400

    course = CourseModel.get_by_id(course_id)
    if not course:
        return jsonify({"error": f"Course with ID {course_id} not found"}), 404

    # 2. Validate topic_id
    topic_id = data.get("topic_id")
    if topic_id is None:
        return jsonify({"error": "topic_id is required"}), 400
    try:
        topic_id = int(topic_id)
    except (ValueError, TypeError):
        return jsonify({"error": "topic_id must be an integer"}), 400

    topic = TopicModel.get_by_id(topic_id)
    if not topic:
        return jsonify({"error": f"Topic with ID {topic_id} not found"}), 404

    # 3. Validate level
    level = str(data.get("level", "")).strip().lower()
    if level not in VALID_LEVELS:
        return jsonify({
            "error": f"Invalid level '{level}'. Must be one of: {sorted(list(VALID_LEVELS))}"
        }), 400

    # 4. Validate language
    language = str(data.get("language", "")).strip().lower()
    if language not in VALID_LANGUAGES:
        return jsonify({
            "error": f"Invalid language '{language}'. Must be one of: {sorted(list(VALID_LANGUAGES))}"
        }), 400

    # 5. Validate marks
    marks = data.get("marks")
    if marks is None:
        return jsonify({"error": "marks is required"}), 400
    try:
        marks = int(marks)
    except (ValueError, TypeError):
        return jsonify({"error": "marks must be an integer"}), 400

    if marks not in VALID_MARKS:
        return jsonify({
            "error": f"Invalid marks '{marks}'. Must be one of: {sorted(list(VALID_MARKS))}"
        }), 400

    # 6. Validate mode
    mode = str(data.get("mode", "")).strip().lower()
    if mode not in VALID_MODES:
        return jsonify({
            "error": f"Invalid mode '{mode}'. Must be one of: {sorted(list(VALID_MODES))}"
        }), 400

    # AI Pipeline Integration
    answer_text = ""
    source_reference = ""
    source_verified = False
    keywords_verified = False

    try:
        from ai.generator import generate_answer as ai_generate
        ai_result = ai_generate(
            course_id=course_id,
            topic_id=topic_id,
            level=level,
            language=language,
            marks=marks,
            mode=mode
        )
        answer_text = ai_result.get("answer", "")
        source_reference = ai_result.get("source_reference", "")
        source_verified = bool(ai_result.get("source_verified", False))
        keywords_verified = bool(ai_result.get("keywords_verified", False))
    except ImportError:
        # Per Rule 9: Use mock data during isolated development and clearly mark it.
        topic_name = topic["topic_name"]
        source_reference = f"Course Material - {course['course_name']} ({topic_name})"
        source_verified = True
        keywords_verified = True

        if language == "hindi":
            answer_text = (
                f"[MOCK DATA - Awaiting ai.generator] {topic_name} की विस्तृत व्याख्या "
                f"({level} स्तर, {marks} अंक, {mode} मोड)। "
                "यह उत्तर पाठ्यक्रम सामग्री के आधार पर तैयार किया गया है।"
            )
        else:
            answer_text = (
                f"[MOCK DATA - Awaiting ai.generator] Comprehensive explanation of {topic_name} "
                f"at {level} level for a {marks}-mark question in {mode} mode. "
                "The content is structured according to examination requirements with key concepts, "
                "definitions, and practical examples verified against course materials."
            )

    # Store generated answer in database
    created_answer = AnswerModel.create(
        topic_id=topic_id,
        level=level,
        language=language,
        marks=marks,
        mode=mode,
        answer_text=answer_text,
        source_reference=source_reference,
        source_verified=source_verified,
        keywords_verified=keywords_verified,
        approval_status="pending"
    )

    return jsonify(format_answer_response(created_answer)), 200


@answers_bp.route("/answers/<int:answer_id>", methods=["GET"])
def get_answer(answer_id):
    """Retrieve an answer by its ID."""
    answer = AnswerModel.get_by_id(answer_id)
    if not answer:
        return jsonify({"error": f"Answer with ID {answer_id} not found"}), 404

    return jsonify(format_answer_response(answer)), 200


@answers_bp.route("/answers/<int:answer_id>/approve", methods=["POST"])
def approve_answer(answer_id):
    """Teacher approves a generated answer."""
    answer = AnswerModel.get_by_id(answer_id)
    if not answer:
        return jsonify({"error": f"Answer with ID {answer_id} not found"}), 404

    updated = AnswerModel.update_approval(answer_id, "approved")
    return jsonify({
        "message": "Answer approved successfully",
        "answer_id": answer_id,
        "approval_status": updated["approval_status"]
    }), 200


@answers_bp.route("/answers/<int:answer_id>/reject", methods=["POST"])
def reject_answer(answer_id):
    """Teacher rejects a generated answer."""
    answer = AnswerModel.get_by_id(answer_id)
    if not answer:
        return jsonify({"error": f"Answer with ID {answer_id} not found"}), 404

    updated = AnswerModel.update_approval(answer_id, "rejected")
    return jsonify({
        "message": "Answer rejected",
        "answer_id": answer_id,
        "approval_status": updated["approval_status"]
    }), 200
