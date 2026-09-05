import os
import time
from pathlib import Path
from werkzeug.utils import secure_filename
from flask import Blueprint, request, jsonify
from backend.config import Config
from backend.database.models import CourseModel, MaterialModel

materials_bp = Blueprint("materials", __name__)


def allowed_file(filename):
    """Check if uploaded file has an allowed extension (PDF)."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in Config.ALLOWED_EXTENSIONS


@materials_bp.route("/materials/upload", methods=["POST"])
def upload_material():
    """Upload an approved course PDF document."""
    # Check course_id form field
    course_id = request.form.get("course_id")
    if not course_id:
        return jsonify({"error": "course_id is required"}), 400

    try:
        course_id = int(course_id)
    except (ValueError, TypeError):
        return jsonify({"error": "course_id must be an integer"}), 400

    # Verify course exists
    course = CourseModel.get_by_id(course_id)
    if not course:
        return jsonify({"error": f"Course with ID {course_id} not found"}), 404

    # Check file field
    if "file" not in request.files:
        return jsonify({"error": "file field is required in form-data"}), 400

    file = request.files["file"]
    if not file or not file.filename or not file.filename.strip():
        return jsonify({"error": "No file selected for upload"}), 400

    if not allowed_file(file.filename):
        return jsonify({
            "error": "Invalid file type. Only PDF files are accepted."
        }), 400

    # Sanitize and create unique filename
    original_name = secure_filename(file.filename)
    if not original_name:
        original_name = f"upload_{int(time.time())}.pdf"

    unique_filename = f"{int(time.time())}_{original_name}"
    upload_dir = Path(Config.UPLOAD_FOLDER)
    os.makedirs(upload_dir, exist_ok=True)
    destination_path = upload_dir / unique_filename

    try:
        file.save(str(destination_path))
        material = MaterialModel.create(
            course_id=course_id,
            file_name=original_name,
            file_path=str(destination_path),
            processing_status="pending"
        )
        return jsonify(material), 201
    except Exception as e:
        return jsonify({"error": "Failed to save uploaded file", "details": str(e)}), 500


@materials_bp.route("/materials/<int:material_id>/process", methods=["POST"])
def process_material(material_id):
    """
    Trigger processing of uploaded material.
    Integrates with Ankit's AI document processing pipeline when available.
    Does not fake document processing if the module is not ready.
    """
    material = MaterialModel.get_by_id(material_id)
    if not material:
        return jsonify({"error": f"Material with ID {material_id} not found"}), 404

    # Check if the document processing module exists in ai/
    try:
        from ai.document_processor import process_document
        try:
            # Module exists, invoke pipeline
            MaterialModel.update_status(material_id, "processing")
            result = process_document(material["file_path"], material["course_id"])
            updated = MaterialModel.update_status(material_id, "processed")
            return jsonify({
                "material_id": material_id,
                "processing_status": "processed",
                "message": "Document processed successfully by AI pipeline",
                "details": result
            }), 200
        except Exception as proc_err:
            MaterialModel.update_status(material_id, "failed")
            return jsonify({
                "material_id": material_id,
                "processing_status": "failed",
                "error": "Document processing failed",
                "details": str(proc_err)
            }), 500
    except ImportError:
        # Document processing module is not implemented yet
        # Strictly adhere to: "Do not fake document processing if the AI/document-processing module is not ready yet."
        return jsonify({
            "material_id": material_id,
            "processing_status": material["processing_status"],
            "message": "AI document-processing module (ai/document_processor.py) is not implemented yet. Document remains queued.",
            "file_name": material["file_name"]
        }), 200


@materials_bp.route("/materials", methods=["GET"])
def get_materials():
    """Retrieve materials, optionally filtered by course_id."""
    course_id = request.args.get("course_id")
    if course_id:
        try:
            course_id = int(course_id)
        except (ValueError, TypeError):
            return jsonify({"error": "course_id must be an integer"}), 400

        course = CourseModel.get_by_id(course_id)
        if not course:
            return jsonify({"error": f"Course with ID {course_id} not found"}), 404

        materials = MaterialModel.get_all(course_id=course_id)
    else:
        materials = MaterialModel.get_all()

    return jsonify(materials), 200
