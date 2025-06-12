# backend/api/student/__init__.py
# Python package initialization
from .routes import student_bp
from .attendance_routes import student_attendance_bp

# Export both blueprints
__all__ = ['student_bp', 'student_attendance_bp']