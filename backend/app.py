import os
from flask import Flask
from config import config
from backend.extensions import db, login_manager, jwt, cors, mail, migrate
from backend.utils.cors import configure_cors
from flask_jwt_extended import JWTManager
from backend.api.student.routes import student_bp

def create_app(config_name=None):
    """Create and configure the Flask application"""
    
    # Set default config if not provided
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'development')
    
    # Create Flask app
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Set up logging
    from backend.utils.logger import setup_app_logging
    app = setup_app_logging(app)
    
    # Initialize extensions
    initialize_extensions(app)
    
    # Configure CORS properly with our utility
    app = configure_cors(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register shell context
    register_shell_context(app)
    
    # Register commands
    register_commands(app)
    
    app.logger.info(f"Application started in {config_name} mode")

    # Initialize JWT
    jwt = JWTManager(app)
    
    # Import User model here before using it
    from backend.models import User
    
    @jwt.user_identity_loader
    def user_identity_lookup(user):
        return user.id if hasattr(user, 'id') else user
    
    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        identity = jwt_data["sub"]
        return User.query.filter_by(user_id=identity).one_or_none()  # Also note: should be user_id, not id
    
    return app

def initialize_extensions(app):
    """Initialize Flask extensions"""
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    jwt.init_app(app)
    # Remove cors.init_app(app) since we're using configure_cors
    mail.init_app(app)
    
    # Configure login manager
    from backend.models import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page'
    login_manager.login_message_category = 'info'

def register_blueprints(app):
    """Register Flask blueprints"""
    # Import blueprints
    from backend.api.auth import auth_bp
    from backend.api.student import student_bp
    from backend.api.faculty import faculty_bp
    from backend.api.admin import admin_bp
    from backend.api.prediction import prediction_bp
    from backend.api.common import common_bp
    
    # Register blueprints with URL prefixes
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(student_bp, url_prefix='/api/student')
    app.register_blueprint(faculty_bp, url_prefix='/api/faculty')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(prediction_bp, url_prefix='/api/prediction')
    app.register_blueprint(common_bp, url_prefix='/api/common')

def register_error_handlers(app):
    """Register error handlers"""
    from backend.middleware.error_handler import register_error_handlers as register
    register(app)

def register_shell_context(app):
    """Register shell context objects"""
    def shell_context():
        """Shell context objects"""
        return {
            'db': db,
            'User': User,
            'Student': Student,
            'Faculty': Faculty,
            'Course': Course,
            'CourseOffering': CourseOffering,
            'Enrollment': Enrollment,
            'Prediction': Prediction
        }
    
    # Import models for shell context
    from backend.models import (
        User, Student, Faculty, Course, CourseOffering, 
        Enrollment, Prediction
    )
    
    app.shell_context_processor(shell_context)

def register_commands(app):
    """Register custom commands"""
    # Skip command registration for now
    pass