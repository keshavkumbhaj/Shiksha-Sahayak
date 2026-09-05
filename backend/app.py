import sys
from pathlib import Path
from flask import Flask, jsonify
from flask_cors import CORS

# Add root project directory to sys.path so 'backend' can be imported cleanly
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend.config import Config
from backend.database.db import init_db


def create_app(config_class=Config):
    """Application factory for Shiksha Sahayak backend."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Initialize SQLite database schema
    with app.app_context():
        init_db()

    # Register API Blueprints
    from backend.routes.courses import courses_bp
    from backend.routes.syllabus import syllabus_bp

    app.register_blueprint(courses_bp, url_prefix="/api")
    app.register_blueprint(syllabus_bp, url_prefix="/api")

    # Conditionally register future stage blueprints if available
    try:
        from backend.routes.materials import materials_bp
        app.register_blueprint(materials_bp, url_prefix="/api")
    except ImportError:
        pass

    try:
        from backend.routes.answers import answers_bp
        app.register_blueprint(answers_bp, url_prefix="/api")
    except ImportError:
        pass

    try:
        from backend.routes.assessment import assessment_bp
        app.register_blueprint(assessment_bp, url_prefix="/api")
    except ImportError:
        pass

    # Health check route
    @app.route("/api/health", methods=["GET"])
    def health():
        return jsonify({
            "status": "online",
            "service": "Shiksha Sahayak Backend API"
        }), 200

    # Global Error Handlers
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"error": "Bad Request", "message": str(e.description if hasattr(e, "description") else e)}), 400

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Resource Not Found", "message": str(e.description if hasattr(e, "description") else e)}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"error": "Method Not Allowed"}), 405

    @app.errorhandler(413)
    def request_entity_too_large(e):
        return jsonify({"error": "Payload Too Large", "message": "File exceeds maximum permitted size (16 MB)"}), 413

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({"error": "Internal Server Error", "message": "An unexpected server error occurred"}), 500

    return app


app = create_app()

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=Config.PORT,
        debug=Config.DEBUG
    )
