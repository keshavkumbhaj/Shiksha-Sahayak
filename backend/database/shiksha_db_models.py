"""
Shiksha Sahayak Database Package (Tanu's Responsibility)
Exposes database initialization, connection handling, and all entity models.
"""

from backend.database.db import (
    get_db_path,
    get_db_connection,
    get_db_context,
    init_db,
    seed_sample_data,
)
from backend.database.models import (
    CourseModel,
    UnitModel,
    TopicModel,
    MaterialModel,
    AnswerModel,
    AssessmentModel,
    AssessmentQuestionModel,
    WeakTopicModel,
)

__all__ = [
    "get_db_path",
    "get_db_connection",
    "get_db_context",
    "init_db",
    "seed_sample_data",
    "CourseModel",
    "UnitModel",
    "TopicModel",
    "MaterialModel",
    "AnswerModel",
    "AssessmentModel",
    "AssessmentQuestionModel",
    "WeakTopicModel",
]
