from flask import Blueprint, request, jsonify, current_app
from backend.models import User, Student, Faculty, Course, CourseOffering, Enrollment, Prediction, Alert
from backend.extensions import db
from backend.utils.api import api_response, error_response, paginated_response
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.middleware.auth_middleware import admin_required
from werkzeug.security import generate_password_hash
from sqlalchemy import or_, func
import logging
from datetime import datetime, timedelta

logger = logging.getLogger('app')

admin_bp = Blueprint('admin', __name__)

# Test endpoint
@admin_bp.route('/test', methods=['GET'])
def test_admin():
    """Test admin endpoint"""
    return api_response(message="Admin API is working!")

# Statistics endpoint
@admin_bp.route('/statistics', methods=['GET'])
@jwt_required()
@admin_required
def get_statistics():
    """Get dashboard statistics"""
    try:
        # Get counts
        total_users = User.query.count()
        active_students = db.session.query(Student).join(User).filter(User.is_active == True).count()
        faculty_count = Faculty.query.count()
        active_courses = CourseOffering.query.filter(CourseOffering.is_active == True).count()
        
        # Additional statistics
        total_enrollments = Enrollment.query.count()
        recent_predictions = Prediction.query.filter(
            Prediction.created_at >= datetime.utcnow() - timedelta(days=7)
        ).count()
        active_alerts = Alert.query.filter(Alert.is_resolved == False).count()
        
        stats = {
            'total_users': total_users,
            'active_students': active_students,
            'faculty_count': faculty_count,
            'active_courses': active_courses,
            'total_enrollments': total_enrollments,
            'recent_predictions': recent_predictions,
            'active_alerts': active_alerts
        }
        
        return api_response(data=stats, message="Statistics retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting statistics: {str(e)}")
        return error_response("Failed to get statistics", 500)

# Recent activities endpoint
@admin_bp.route('/activities/recent', methods=['GET'])
@jwt_required()
@admin_required
def get_recent_activities():
    """Get recent system activities"""
    try:
        activities = []
        
        # Get recent user registrations
        recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
        for user in recent_users:
            activities.append({
                'icon': 'fa-user-plus',
                'color': 'text-blue-600',
                'message': f'New {user.user_type} registered: {user.username}',
                'time': format_time_ago(user.created_at)
            })
        
        # Get recent alerts
        recent_alerts = db.session.query(Alert).order_by(Alert.triggered_date.desc()).limit(5).all()
        for alert in recent_alerts:
            activities.append({
                'icon': 'fa-bell',
                'color': 'text-yellow-600',
                'message': f'New {alert.severity} alert generated',
                'time': format_time_ago(alert.triggered_date)
            })
        
        # Sort by time and limit
        activities = sorted(activities, key=lambda x: x['time'], reverse=True)[:10]
        
        return api_response(data={'activities': activities}, message="Activities retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting activities: {str(e)}")
        return error_response("Failed to get activities", 500)

# User management endpoints
@admin_bp.route('/users', methods=['GET'])
@jwt_required()
@admin_required
def get_users():
    """Get all users with pagination and filters"""
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 10, type=int)
        search = request.args.get('search', '')
        user_type = request.args.get('user_type', '')
        status = request.args.get('status', '')
        
        # Build query
        query = User.query
        
        # Apply filters
        if search:
            query = query.filter(or_(
                User.username.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%')
            ))
        
        if user_type:
            query = query.filter(User.user_type == user_type)
        
        if status:
            is_active = status == 'active'
            query = query.filter(User.is_active == is_active)
        
        # Order by created date
        query = query.order_by(User.created_at.desc())
        
        # Paginate
        paginated = query.paginate(page=page, per_page=limit, error_out=False)
        
        # Format users
        users = []
        for user in paginated.items:
            user_data = {
                'user_id': user.user_id,
                'username': user.username,
                'email': user.email,
                'user_type': user.user_type,
                'is_active': user.is_active,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'last_login': user.last_login.isoformat() if user.last_login else None
            }
            
            # Add full name based on user type
            if user.user_type == 'student' and user.student:
                user_data['full_name'] = f"{user.student.first_name} {user.student.last_name}"
            elif user.user_type == 'faculty' and user.faculty:
                user_data['full_name'] = f"{user.faculty.first_name} {user.faculty.last_name}"
            else:
                user_data['full_name'] = user.username
            
            users.append(user_data)
        
        return api_response(
            data={
                'users': users,
                'total': paginated.total,
                'current_page': page,
                'per_page': limit,
                'total_pages': paginated.pages
            },
            message="Users retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error getting users: {str(e)}")
        return error_response("Failed to get users", 500)

@admin_bp.route('/users/<int:user_id>', methods=['GET'])
@jwt_required()
@admin_required
def get_user(user_id):
    """Get user by ID"""
    try:
        user = User.query.get_or_404(user_id)
        
        user_data = {
            'user_id': user.user_id,
            'username': user.username,
            'email': user.email,
            'user_type': user.user_type,
            'is_active': user.is_active,
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'last_login': user.last_login.isoformat() if user.last_login else None
        }
        
        # Add type-specific data
        if user.user_type == 'student' and user.student:
            user_data['student_data'] = {
                'student_id': user.student.student_id,
                'first_name': user.student.first_name,
                'last_name': user.student.last_name,
                'program_code': user.student.program_code,
                'year_of_study': user.student.year_of_study
            }
        elif user.user_type == 'faculty' and user.faculty:
            user_data['faculty_data'] = {
                'faculty_id': user.faculty.faculty_id,
                'first_name': user.faculty.first_name,
                'last_name': user.faculty.last_name,
                'department': user.faculty.department,
                'position': user.faculty.position
            }
        
        return api_response(data=user_data, message="User retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting user {user_id}: {str(e)}")
        return error_response("Failed to get user", 500)

@admin_bp.route('/users', methods=['POST'])
@jwt_required()
@admin_required
def create_user():
    """Create a new user"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['username', 'email', 'password', 'user_type']
        for field in required_fields:
            if field not in data:
                return error_response(f"Missing required field: {field}", 400)
        
        # Check if username or email already exists
        if User.query.filter_by(username=data['username']).first():
            return error_response("Username already exists", 400)
        
        if User.query.filter_by(email=data['email']).first():
            return error_response("Email already exists", 400)
        
        # Create user
        user = User(
            username=data['username'],
            email=data['email'],
            password_hash=generate_password_hash(data['password']),
            user_type=data['user_type'],
            is_active=data.get('is_active', True)
        )
        
        db.session.add(user)
        db.session.flush()
        
        # Create type-specific record
        if user.user_type == 'student':
            student = Student(
                user_id=user.user_id,
                student_id=f"STU{user.user_id:06d}",
                first_name=data.get('first_name', ''),
                last_name=data.get('last_name', ''),
                program_code=data.get('program_code'),
                year_of_study=data.get('year_of_study', 1)
            )
            db.session.add(student)
        elif user.user_type == 'faculty':
            faculty = Faculty(
                user_id=user.user_id,
                faculty_id=f"FAC{user.user_id:06d}",
                first_name=data.get('first_name', ''),
                last_name=data.get('last_name', ''),
                department=data.get('department'),
                position=data.get('position', 'Lecturer')
            )
            db.session.add(faculty)
        
        db.session.commit()
        
        return api_response(
            data={'user_id': user.user_id},
            message="User created successfully",
            status=201
        )
        
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        db.session.rollback()
        return error_response("Failed to create user", 500)

@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
@jwt_required()
@admin_required
def update_user(user_id):
    """Update user information"""
    try:
        user = User.query.get_or_404(user_id)
        data = request.get_json()
        
        # Update basic user info
        if 'username' in data and data['username'] != user.username:
            # Check if new username is available
            if User.query.filter_by(username=data['username']).first():
                return error_response("Username already exists", 400)
            user.username = data['username']
        
        if 'email' in data and data['email'] != user.email:
            # Check if new email is available
            if User.query.filter_by(email=data['email']).first():
                return error_response("Email already exists", 400)
            user.email = data['email']
        
        if 'password' in data and data['password']:
            user.password_hash = generate_password_hash(data['password'])
        
        if 'is_active' in data:
            user.is_active = data['is_active']
        
        db.session.commit()
        
        return api_response(message="User updated successfully")
        
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {str(e)}")
        db.session.rollback()
        return error_response("Failed to update user", 500)

@admin_bp.route('/users/<int:user_id>/status', methods=['PUT'])
@jwt_required()
@admin_required
def update_user_status(user_id):
    """Update user active status"""
    try:
        user = User.query.get_or_404(user_id)
        data = request.get_json()
        
        if 'is_active' not in data:
            return error_response("Missing is_active field", 400)
        
        user.is_active = data['is_active']
        db.session.commit()
        
        status = "activated" if user.is_active else "deactivated"
        
        return api_response(message=f"User {status} successfully")
        
    except Exception as e:
        logger.error(f"Error updating user status {user_id}: {str(e)}")
        db.session.rollback()
        return error_response("Failed to update user status", 500)

# Course management endpoints
@admin_bp.route('/courses', methods=['GET'])
@jwt_required()
@admin_required
def get_courses():
    """Get all courses"""
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 10, type=int)
        search = request.args.get('search', '')
        
        # Build query
        query = Course.query
        
        if search:
            query = query.filter(or_(
                Course.course_code.ilike(f'%{search}%'),
                Course.course_name.ilike(f'%{search}%')
            ))
        
        # Order by course code
        query = query.order_by(Course.course_code)
        
        # Paginate
        paginated = query.paginate(page=page, per_page=limit, error_out=False)
        
        # Format courses
        courses = []
        for course in paginated.items:
            # Get active offerings count
            active_offerings = CourseOffering.query.filter_by(
                course_id=course.course_id,
                is_active=True
            ).count()
            
            courses.append({
                'course_id': course.course_id,
                'course_code': course.course_code,
                'course_name': course.course_name,
                'credits': course.credits,
                'description': course.description,
                'active_offerings': active_offerings
            })
        
        return api_response(
            data={
                'courses': courses,
                'total': paginated.total,
                'current_page': page,
                'per_page': limit,
                'total_pages': paginated.pages
            },
            message="Courses retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error getting courses: {str(e)}")
        return error_response("Failed to get courses", 500)

@admin_bp.route('/system/config', methods=['GET'])
@jwt_required()
@admin_required
def get_system_config():
    """Get system configuration"""
    try:
        config = {
            'attendance_threshold': 70,
            'prediction_frequency': 'daily',
            'alert_email_enabled': True,
            'model_version': 'v1.0',
            'max_file_upload_size': 10485760,  # 10MB
            'session_timeout': 3600,  # 1 hour
            'password_min_length': 8,
            'maintenance_mode': False
        }
        
        return api_response(data=config, message="System configuration retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting system config: {str(e)}")
        return error_response("Failed to get system configuration", 500)

@admin_bp.route('/system/config', methods=['PUT'])
@jwt_required()
@admin_required
def update_system_config():
    """Update system configuration"""
    try:
        data = request.get_json()
        
        # In a real implementation, this would update a configuration table
        # For now, just return success
        
        return api_response(message="System configuration updated successfully")
        
    except Exception as e:
        logger.error(f"Error updating system config: {str(e)}")
        return error_response("Failed to update system configuration", 500)

# Helper functions
def format_time_ago(timestamp):
    """Format timestamp as 'X time ago'"""
    if not timestamp:
        return "Unknown"
    
    now = datetime.utcnow()
    diff = now - timestamp
    
    if diff.days > 7:
        return timestamp.strftime("%b %d, %Y")
    elif diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    else:
        return "Just now"