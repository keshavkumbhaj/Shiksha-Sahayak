from flask import Blueprint, request, jsonify
from backend.database.models import (
    TopicModel,
    AssessmentModel,
    AssessmentQuestionModel,
    WeakTopicModel
)

assessment_bp = Blueprint("assessment", __name__)


def generate_mock_questions_for_topic(topic_name):
    """
    Provide topic-relevant mock MCQs when Ankit's AI assessment module is not yet present.
    Adheres to Rule 9 (clearly marked during isolated development).
    """
    return [
        {
            "question_text": f"Which condition is required for a relational schema to be in 2NF regarding {topic_name}?",
            "options": [
                "It is in 1NF and has no partial dependency",
                "It has transitive dependencies only",
                "Every attribute is a primary key",
                "It must contain multivalue dependencies"
            ],
            "correct_answer": "It is in 1NF and has no partial dependency"
        },
        {
            "question_text": f"In {topic_name}, what defines Boyce-Codd Normal Form (BCNF)?",
            "options": [
                "Every determinant must be a candidate key",
                "Eliminating partial functional dependency only",
                "Permitting non-trivial multivalued dependencies",
                "Allowing composite primary keys without 1NF"
            ],
            "correct_answer": "Every determinant must be a candidate key"
        },
        {
            "question_text": f"What is the primary objective of {topic_name} in relational database design?",
            "options": [
                "Minimizing data redundancy and insertion/deletion anomalies",
                "Increasing table file size for faster scanning",
                "Converting all attributes to JSON text fields",
                "Bypassing referential integrity checks"
            ],
            "correct_answer": "Minimizing data redundancy and insertion/deletion anomalies"
        }
    ]


@assessment_bp.route("/assessment/generate", methods=["POST"])
def generate_assessment():
    """
    Generate an MCQ assessment for a given topic.
    Integrates with Ankit's AI assessment pipeline (ai/assessment.py) when available.
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be valid JSON"}), 400

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

    num_questions = data.get("num_questions", 3)
    try:
        num_questions = int(num_questions)
        if num_questions <= 0:
            num_questions = 3
    except (ValueError, TypeError):
        num_questions = 3

    # Generate questions via AI or clearly marked fallback
    questions_data = []
    try:
        from ai.assessment import generate_mcqs
        questions_data = generate_mcqs(topic_id=topic_id, num_questions=num_questions)
    except ImportError:
        questions_data = generate_mock_questions_for_topic(topic["topic_name"])[:num_questions]

    # Create assessment record in DB
    assessment = AssessmentModel.create(
        topic_id=topic_id,
        total_questions=len(questions_data),
        score=0
    )
    assessment_id = assessment["assessment_id"]

    # Save questions in DB
    saved_questions = []
    for q in questions_data:
        saved_q = AssessmentQuestionModel.create(
            assessment_id=assessment_id,
            question_text=q["question_text"],
            options=q["options"],
            correct_answer=q["correct_answer"],
            topic_id=topic_id
        )
        saved_questions.append({
            "question_id": saved_q["question_id"],
            "assessment_id": assessment_id,
            "question_text": saved_q["question_text"],
            "options": saved_q["options"],
            "topic_id": topic_id
        })

    return jsonify({
        "assessment_id": assessment_id,
        "topic_id": topic_id,
        "total_questions": len(saved_questions),
        "questions": saved_questions
    }), 201


@assessment_bp.route("/assessment/submit", methods=["POST"])
def submit_assessment():
    """
    Submit student answers, grade assessment, and record weak topic if threshold is not met.
    Accepts answers either as a dict {question_id: answer} or list [{question_id, selected_option}].
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    assessment_id = data.get("assessment_id")
    if assessment_id is None:
        return jsonify({"error": "assessment_id is required"}), 400
    try:
        assessment_id = int(assessment_id)
    except (ValueError, TypeError):
        return jsonify({"error": "assessment_id must be an integer"}), 400

    assessment = AssessmentModel.get_by_id(assessment_id)
    if not assessment:
        return jsonify({"error": f"Assessment with ID {assessment_id} not found"}), 404

    # Normalize submitted answers
    raw_answers = data.get("answers", {})
    user_answers = {}
    if isinstance(raw_answers, dict):
        for k, v in raw_answers.items():
            try:
                user_answers[int(k)] = str(v).strip()
            except (ValueError, TypeError):
                pass
    elif isinstance(raw_answers, list):
        for item in raw_answers:
            if isinstance(item, dict) and "question_id" in item:
                try:
                    qid = int(item["question_id"])
                    ans = item.get("selected_option", item.get("answer", ""))
                    user_answers[qid] = str(ans).strip()
                except (ValueError, TypeError):
                    pass

    # Retrieve all questions for this assessment
    db_questions = AssessmentQuestionModel.get_by_assessment(assessment_id)
    if not db_questions:
        return jsonify({"error": "No questions found for this assessment"}), 400

    score = 0
    total = len(db_questions)
    results = []

    for q in db_questions:
        qid = q["question_id"]
        correct_ans = str(q["correct_answer"]).strip()
        student_ans = user_answers.get(qid, "")
        is_correct = (student_ans.lower() == correct_ans.lower())

        if is_correct:
            score += 1

        results.append({
            "question_id": qid,
            "question_text": q["question_text"],
            "selected_option": student_ans,
            "correct_answer": correct_ans,
            "is_correct": is_correct
        })

    # Update assessment score in DB
    AssessmentModel.update_score(assessment_id, score)

    # Determine weak topic: threshold < 60% (or score < 2 for a 3-question quiz)
    percentage = round((score / total) * 100, 1) if total > 0 else 0
    is_weak = percentage < 60.0

    if is_weak:
        WeakTopicModel.record(
            topic_id=assessment["topic_id"],
            score=score,
            total=total
        )

    return jsonify({
        "assessment_id": assessment_id,
        "topic_id": assessment["topic_id"],
        "score": score,
        "total_questions": total,
        "percentage": percentage,
        "is_weak": is_weak,
        "weak_topic": is_weak,
        "recommendation": "Revision recommended" if is_weak else "Good mastery of topic",
        "results": results
    }), 200


@assessment_bp.route("/assessment/weak-topics", methods=["GET"])
def get_weak_topics():
    """Retrieve all identified weak topics."""
    weak_topics = WeakTopicModel.get_all()
    return jsonify(weak_topics), 200
