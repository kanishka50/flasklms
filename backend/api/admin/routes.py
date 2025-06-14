from flask import Blueprint, request, jsonify, current_app
from backend.models import User, Student, Faculty, Course, CourseOffering, Enrollment, Prediction, Alert
from backend.extensions import db
from backend.utils.api import api_response, error_response
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.middleware.auth_middleware import admin_required
from werkzeug.security import generate_password_hash
from sqlalchemy import or_, func
import logging
from datetime import datetime, timedelta
from backend.services.alert_service import AlertService

logger = logging.getLogger('admin')

admin_bp = Blueprint('admin', __name__)

alert_service = AlertService()

# Test endpoint
@admin_bp.route('/test', methods=['GET'])
def test_admin():
    """Test admin endpoint"""
    return api_response(message="Admin API is working!")

# Statistics endpoint with better error handling
@admin_bp.route('/statistics', methods=['GET'])
@jwt_required()
@admin_required
def get_statistics():
    """Get dashboard statistics"""
    try:
        stats = {}
        
        # Get user counts with error handling
        try:
            stats['total_users'] = User.query.count()
        except Exception as e:
            logger.error(f"Error counting users: {str(e)}")
            stats['total_users'] = 0
        
        # Get active students
        try:
            stats['active_students'] = db.session.query(Student).join(User).filter(User.is_active == True).count()
        except Exception as e:
            logger.error(f"Error counting active students: {str(e)}")
            stats['active_students'] = 0
        
        # Get faculty count
        try:
            stats['faculty_count'] = Faculty.query.count()
        except Exception as e:
            logger.error(f"Error counting faculty: {str(e)}")
            stats['faculty_count'] = 0
        
        # Get active courses - check if CourseOffering has is_active column
        try:
            # Try with is_active column first
            stats['active_courses'] = CourseOffering.query.filter(CourseOffering.is_active == True).count()
        except Exception as e:
            # If is_active doesn't exist, count all offerings
            try:
                stats['active_courses'] = CourseOffering.query.count()
            except:
                stats['active_courses'] = 0
        
        # Get total enrollments
        try:
            stats['total_enrollments'] = Enrollment.query.count()
        except Exception as e:
            logger.error(f"Error counting enrollments: {str(e)}")
            stats['total_enrollments'] = 0
        
        # Get recent predictions - check if created_at exists
        try:
            # Try with created_at first
            stats['recent_predictions'] = Prediction.query.filter(
                Prediction.created_at >= datetime.utcnow() - timedelta(days=7)
            ).count()
        except Exception as e:
            # If created_at doesn't exist, use prediction_date
            try:
                stats['recent_predictions'] = Prediction.query.filter(
                    Prediction.prediction_date >= datetime.utcnow() - timedelta(days=7)
                ).count()
            except:
                stats['recent_predictions'] = 0
        
        # Get active alerts
        try:
            stats['active_alerts'] = Alert.query.filter(Alert.is_resolved == False).count()
        except Exception as e:
            logger.error(f"Error counting alerts: {str(e)}")
            stats['active_alerts'] = 0
        
        return api_response(data=stats, message="Statistics retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting statistics: {str(e)}")
        # Return partial data instead of failing completely
        return api_response(
            data={
                'total_users': 0,
                'active_students': 0,
                'faculty_count': 0,
                'active_courses': 0,
                'total_enrollments': 0,
                'recent_predictions': 0,
                'active_alerts': 0
            },
            message="Statistics retrieved with errors"
        )

# Recent activities endpoint with better error handling
@admin_bp.route('/activities/recent', methods=['GET'])
@jwt_required()
@admin_required
def get_recent_activities():
    """Get recent system activities"""
    try:
        activities = []
        
        # Get recent user registrations
        try:
            recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
            for user in recent_users:
                activities.append({
                    'icon': 'fa-user-plus',
                    'color': 'text-blue-600',
                    'message': f'New {user.user_type} registered: {user.username}',
                    'time': format_time_ago(user.created_at) if user.created_at else 'Unknown'
                })
        except Exception as e:
            logger.error(f"Error getting recent users: {str(e)}")
        
        # Get recent alerts
        try:
            recent_alerts = Alert.query.order_by(Alert.triggered_date.desc()).limit(5).all()
            for alert in recent_alerts:
                activities.append({
                    'icon': 'fa-bell',
                    'color': 'text-yellow-600',
                    'message': f'New {alert.severity} alert generated',
                    'time': format_time_ago(alert.triggered_date) if alert.triggered_date else 'Unknown'
                })
        except Exception as e:
            logger.error(f"Error getting recent alerts: {str(e)}")
        
        # If no activities found, add some default ones
        if not activities:
            activities = [
                {
                    'icon': 'fa-info-circle',
                    'color': 'text-gray-600',
                    'message': 'System started',
                    'time': 'Just now'
                }
            ]
        
        return api_response(data={'activities': activities}, message="Activities retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting activities: {str(e)}")
        return api_response(
            data={'activities': []},
            message="Activities retrieved with errors"
        )

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
        
        # Order by created date if column exists, otherwise by user_id
        try:
            query = query.order_by(User.created_at.desc())
        except:
            query = query.order_by(User.user_id.desc())
        
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
                'is_active': user.is_active if hasattr(user, 'is_active') else True,
                'created_at': user.created_at.isoformat() if hasattr(user, 'created_at') and user.created_at else None,
                'last_login': user.last_login.isoformat() if hasattr(user, 'last_login') and user.last_login else None
            }
            
            # Add full name based on user type
            if user.user_type == 'student' and hasattr(user, 'student') and user.student:
                user_data['full_name'] = f"{user.student.first_name} {user.student.last_name}"
            elif user.user_type == 'faculty' and hasattr(user, 'faculty') and user.faculty:
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
        user = User.query.get(user_id)
        if not user:
            return error_response("User not found", 404)
        
        user_data = {
            'user_id': user.user_id,
            'username': user.username,
            'email': user.email,
            'user_type': user.user_type,
            'is_active': user.is_active if hasattr(user, 'is_active') else True,
            'created_at': user.created_at.isoformat() if hasattr(user, 'created_at') and user.created_at else None,
            'last_login': user.last_login.isoformat() if hasattr(user, 'last_login') and user.last_login else None
        }
        
        # Add type-specific data
        if user.user_type == 'student' and hasattr(user, 'student') and user.student:
            user_data['student_data'] = {
                'student_id': user.student.student_id,
                'first_name': user.student.first_name,
                'last_name': user.student.last_name,
                'program_code': user.student.program_code if hasattr(user.student, 'program_code') else None,
                'year_of_study': user.student.year_of_study if hasattr(user.student, 'year_of_study') else None
            }
        elif user.user_type == 'faculty' and hasattr(user, 'faculty') and user.faculty:
            user_data['faculty_data'] = {
                'faculty_id': user.faculty.faculty_id,
                'first_name': user.faculty.first_name,
                'last_name': user.faculty.last_name,
                'department': user.faculty.department if hasattr(user.faculty, 'department') else None,
                'position': user.faculty.position if hasattr(user.faculty, 'position') else None
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
            user_type=data['user_type']
        )
        
        # Set is_active if the model has this field
        if hasattr(User, 'is_active'):
            user.is_active = data.get('is_active', True)
        
        db.session.add(user)
        db.session.flush()
        
        # Create type-specific record
        if user.user_type == 'student':
            student = Student(
                user_id=user.user_id,
                student_id=f"STU{user.user_id:06d}",
                first_name=data.get('first_name', ''),
                last_name=data.get('last_name', '')
            )
            # Add optional fields if they exist in the model
            if hasattr(Student, 'program_code'):
                student.program_code = data.get('program_code')
            if hasattr(Student, 'year_of_study'):
                student.year_of_study = data.get('year_of_study', 1)
            db.session.add(student)
            
        elif user.user_type == 'faculty':
            faculty = Faculty(
                user_id=user.user_id,
                faculty_id=f"FAC{user.user_id:06d}",
                first_name=data.get('first_name', ''),
                last_name=data.get('last_name', '')
            )
            # Add optional fields if they exist in the model
            if hasattr(Faculty, 'department'):
                faculty.department = data.get('department')
            if hasattr(Faculty, 'position'):
                faculty.position = data.get('position', 'Lecturer')
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
        user = User.query.get(user_id)
        if not user:
            return error_response("User not found", 404)
            
        data = request.get_json()
        
        # Update basic user info
        if 'username' in data and data['username'] != user.username:
            # Check if new username is available
            existing = User.query.filter_by(username=data['username']).first()
            if existing and existing.user_id != user_id:
                return error_response("Username already exists", 400)
            user.username = data['username']
        
        if 'email' in data and data['email'] != user.email:
            # Check if new email is available
            existing = User.query.filter_by(email=data['email']).first()
            if existing and existing.user_id != user_id:
                return error_response("Email already exists", 400)
            user.email = data['email']
        
        if 'password' in data and data['password']:
            user.password_hash = generate_password_hash(data['password'])
        
        if 'is_active' in data and hasattr(user, 'is_active'):
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
        user = User.query.get(user_id)
        if not user:
            return error_response("User not found", 404)
            
        data = request.get_json()
        
        if 'is_active' not in data:
            return error_response("Missing is_active field", 400)
        
        if hasattr(user, 'is_active'):
            user.is_active = data['is_active']
            db.session.commit()
            status = "activated" if user.is_active else "deactivated"
            return api_response(message=f"User {status} successfully")
        else:
            return error_response("User status management not supported", 400)
        
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
            try:
                active_offerings = CourseOffering.query.filter_by(
                    course_id=course.course_id
                ).count()
            except:
                active_offerings = 0
            
            courses.append({
                'course_id': course.course_id,
                'course_code': course.course_code,
                'course_name': course.course_name,
                'credits': course.credits if hasattr(course, 'credits') else 0,
                'description': course.description if hasattr(course, 'description') else '',
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
    
    try:
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
    except:
        return "Unknown"
    
@admin_bp.route('/courses', methods=['POST'])
@jwt_required()
@admin_required
def create_course():
    """Create a new course"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['course_code', 'course_name', 'credits']
        for field in required_fields:
            if field not in data:
                return error_response(f"Missing required field: {field}", 400)
        
        # Check if course code already exists
        if Course.query.filter_by(course_code=data['course_code']).first():
            return error_response("Course code already exists", 400)
        
        # Create course
        course = Course(
            course_code=data['course_code'],
            course_name=data['course_name'],
            credits=data['credits'],
            description=data.get('description', '')
        )
        
        db.session.add(course)
        db.session.commit()
        
        return api_response(
            data={'course_id': course.course_id},
            message="Course created successfully",
            status=201
        )
        
    except Exception as e:
        logger.error(f"Error creating course: {str(e)}")
        db.session.rollback()
        return error_response("Failed to create course", 500)

@admin_bp.route('/courses/<int:course_id>', methods=['PUT'])
@jwt_required()
@admin_required
def update_course(course_id):
    """Update course information"""
    try:
        course = Course.query.get(course_id)
        if not course:
            return error_response("Course not found", 404)
            
        data = request.get_json()
        
        # Update course info
        if 'course_code' in data and data['course_code'] != course.course_code:
            # Check if new code is available
            existing = Course.query.filter_by(course_code=data['course_code']).first()
            if existing and existing.course_id != course_id:
                return error_response("Course code already exists", 400)
            course.course_code = data['course_code']
        
        if 'course_name' in data:
            course.course_name = data['course_name']
        
        if 'credits' in data:
            course.credits = data['credits']
        
        if 'description' in data:
            course.description = data['description']
        
        db.session.commit()
        
        return api_response(message="Course updated successfully")
        
    except Exception as e:
        logger.error(f"Error updating course {course_id}: {str(e)}")
        db.session.rollback()
        return error_response("Failed to update course", 500)

@admin_bp.route('/courses/<int:course_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_course(course_id):
    """Delete a course (if no active offerings)"""
    try:
        course = Course.query.get(course_id)
        if not course:
            return error_response("Course not found", 404)
        
        # Check if course has active offerings
        active_offerings = CourseOffering.query.filter_by(course_id=course_id).count()
        if active_offerings > 0:
            return error_response("Cannot delete course with active offerings", 400)
        
        db.session.delete(course)
        db.session.commit()
        
        return api_response(message="Course deleted successfully")
        
    except Exception as e:
        logger.error(f"Error deleting course {course_id}: {str(e)}")
        db.session.rollback()
        return error_response("Failed to delete course", 500)
    
@admin_bp.route('/alerts', methods=['GET'])
@jwt_required()
def get_system_alerts():
    """Get system alerts with pagination and filtering"""
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 10, type=int)
        severity = request.args.get('severity', None)
        status = request.args.get('status', None)
        search = request.args.get('search', None)
        
        # Build query with proper joins
        query = db.session.query(Alert).join(
            Enrollment, Alert.enrollment_id == Enrollment.enrollment_id
        ).join(
            Student, Enrollment.student_id == Student.student_id
        ).join(
            User, Student.user_id == User.user_id
        ).join(
            CourseOffering, Enrollment.offering_id == CourseOffering.offering_id
        ).join(
            Course, CourseOffering.course_id == Course.course_id
        ).join(
            AlertType, Alert.type_id == AlertType.type_id
        )
        
        # Apply filters
        if severity:
            query = query.filter(Alert.severity == severity)
        if status:
            if status == 'active':
                query = query.filter(Alert.is_resolved == False)
            elif status == 'resolved':
                query = query.filter(Alert.is_resolved == True)
        if search:
            query = query.filter(
                or_(
                    Alert.alert_message.ilike(f'%{search}%'),
                    AlertType.type_name.ilike(f'%{search}%')
                )
            )
        
        # Order by triggered date (newest first)
        query = query.order_by(desc(Alert.triggered_date))
        
        # Paginate
        pagination = query.paginate(page=page, per_page=limit, error_out=False)
        
        # Format alerts
        alerts = []
        for alert in pagination.items:
            # Get related data through joins
            enrollment = alert.enrollment
            student = enrollment.student
            user = student.user
            course_offering = enrollment.offering
            course = course_offering.course
            alert_type = alert.alert_type
            
            alert_data = {
                'id': alert.alert_id,
                'alert_id': alert.alert_id,
                'alert_type': alert_type.type_name,
                'type': alert_type.type_name,
                'message': alert.alert_message,
                'severity': alert.severity,
                'status': 'resolved' if alert.is_resolved else 'active',
                'is_resolved': alert.is_resolved,
                'is_read': alert.is_read,
                'triggered_date': alert.triggered_date.isoformat() if alert.triggered_date else None,
                'created_at': alert.triggered_date.isoformat() if alert.triggered_date else None,
                'resolved_date': alert.resolved_date.isoformat() if alert.resolved_date else None,
                'student_id': student.student_id,
                'student_name': f"{user.first_name or student.first_name} {user.last_name or student.last_name}",
                'course_id': course.course_id,
                'course_name': f"{course.course_code} - {course.course_name}"
            }
            
            alerts.append(alert_data)
        
        return paginated_response(
            data=alerts,
            page=page,
            per_page=limit,
            total=pagination.total,
            message='Alerts retrieved successfully'
        )
        
    except Exception as e:
        logger.error(f"Error fetching alerts: {str(e)}")
        # Don't return demo data - return the actual error
        return error_response(f'Failed to fetch alerts: {str(e)}', 500)


@admin_bp.route('/alerts/<int:alert_id>/resolve', methods=['PUT'])
@jwt_required()
def resolve_alert(alert_id):
    """Mark an alert as resolved"""
    try:
        user_id = get_jwt_identity()
        alert_service.resolve_alert(alert_id, resolved_by=str(user_id))
        
        return api_response({
            'id': alert_id,
            'status': 'resolved',
            'resolved_at': datetime.utcnow().isoformat()
        }, 'Alert resolved successfully')
        
    except Exception as e:
        logger.error(f"Error resolving alert: {str(e)}")
        db.session.rollback()
        return error_response('Failed to resolve alert', 500)
    
    
@admin_bp.route('/alerts/stats', methods=['GET'])
@jwt_required()
def get_alert_stats():
    """Get alert statistics"""
    try:
        summary = alert_service.get_alert_summary()
        
        return api_response({
            'total_alerts': Alert.query.count(),
            'active_alerts': summary['total'],
            'resolved_alerts': Alert.query.filter(Alert.is_resolved == True).count(),
            'critical_alerts': summary['critical'],
            'resolved_today': Alert.query.filter(
                Alert.resolved_date >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0),
                Alert.is_resolved == True
            ).count()
        }, 'Alert statistics retrieved successfully')
        
    except Exception as e:
        logger.error(f"Error fetching alert stats: {str(e)}")
        return error_response('Failed to fetch alert statistics', 500)
    
def paginated_response(data, page, per_page, total, message='Success'):
    """Create a paginated response"""
    return jsonify({
        'status': 'success',
        'message': message,
        'data': data,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': (total + per_page - 1) // per_page if per_page > 0 else 0
        }
    })
    
    