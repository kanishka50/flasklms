from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.services.faculty_service import faculty_service
from backend.services.attendance_service import attendance_service
from backend.services.auth_service import get_user_by_id
from backend.services.assessment_service import assessment_service
from backend.middleware.auth_middleware import faculty_required
from backend.utils.api import api_response, error_response
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)

faculty_bp = Blueprint('faculty', __name__, url_prefix='/api/faculty')

# =====================================================
# DASHBOARD & BASIC ROUTES
# =====================================================

@faculty_bp.route('/dashboard', methods=['GET'])
@jwt_required()
@faculty_required
def get_dashboard():
    """Get faculty dashboard data"""
    try:
        # Get current user
        user_id = get_jwt_identity()
        user = get_user_by_id(user_id)
        
        if not user or not user.faculty:
            return jsonify({
                'status': 'error',
                'message': 'Faculty profile not found'
            }), 404
        
        faculty_id = user.faculty.faculty_id
        
        # Get dashboard summary
        summary = faculty_service.get_dashboard_summary(faculty_id)
        
        return jsonify({
            'status': 'success',
            'data': {
                'summary': summary,
                'faculty': {
                    'faculty_id': faculty_id,
                    'name': f"{user.faculty.first_name} {user.faculty.last_name}",
                    'email': user.email,
                    'department': user.faculty.department
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting dashboard: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to load dashboard data'
        }), 500

@faculty_bp.route('/courses', methods=['GET'])
@jwt_required()
@faculty_required
def get_courses():
    """Get courses taught by faculty"""
    try:
        # Get current user
        user_id = get_jwt_identity()
        user = get_user_by_id(user_id)
        
        if not user or not user.faculty:
            return jsonify({
                'status': 'error',
                'message': 'Faculty profile not found'
            }), 404
        
        faculty_id = user.faculty.faculty_id
        
        # Get term from query params (optional)
        term_id = request.args.get('term_id', type=int)
        
        # Get courses
        courses = faculty_service.get_teaching_courses(faculty_id, term_id)
        
        return jsonify({
            'status': 'success',
            'data': {
                'courses': courses
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting courses: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to load courses'
        }), 500

@faculty_bp.route('/students', methods=['GET'])
@jwt_required()
@faculty_required
def get_students():
    """Get students in faculty's courses"""
    try:
        # Get offering_id from query params
        offering_id = request.args.get('offering_id', type=int)
        
        if not offering_id:
            return jsonify({
                'status': 'error',
                'message': 'Course offering ID is required'
            }), 400
        
        # Verify faculty teaches this course
        user_id = get_jwt_identity()
        user = get_user_by_id(user_id)
        
        if not user or not user.faculty:
            return jsonify({
                'status': 'error',
                'message': 'Faculty profile not found'
            }), 404
        
        # Get students
        students = faculty_service.get_students_by_course(offering_id)
        
        return jsonify({
            'status': 'success',
            'data': {
                'students': students
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting students: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to load students'
        }), 500

@faculty_bp.route('/all-students', methods=['GET'])
@jwt_required()
@faculty_required
def get_all_students():
    """Get all students enrolled in faculty's courses"""
    try:
        # Get current user
        user_id = get_jwt_identity()
        user = get_user_by_id(user_id)
        
        if not user or not user.faculty:
            return jsonify({
                'status': 'error',
                'message': 'Faculty profile not found'
            }), 404
        
        faculty_id = user.faculty.faculty_id
        
        # Get all students across all courses
        all_students = faculty_service.get_all_students(faculty_id)
        
        # Get summary statistics
        total_students = len(all_students)
        active_students = len([s for s in all_students if s['current_grade'] != 'W'])
        at_risk_students = len([s for s in all_students if s['risk_level'] in ['medium', 'high']])
        
        # Calculate average attendance
        attendance_rates = [s['attendance_rate'] for s in all_students if s['attendance_rate'] is not None]
        avg_attendance = sum(attendance_rates) / len(attendance_rates) if attendance_rates else 0
        
        return jsonify({
            'status': 'success',
            'data': {
                'students': all_students,
                'summary': {
                    'total_students': total_students,
                    'active_students': active_students,
                    'at_risk_students': at_risk_students,
                    'average_attendance': round(avg_attendance, 1)
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting all students: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to load students'
        }), 500

@faculty_bp.route('/at-risk-students', methods=['GET'])
@jwt_required()
@faculty_required
def get_at_risk_students():
    """Get at-risk students in faculty's courses"""
    try:
        # Get current user
        user_id = get_jwt_identity()
        user = get_user_by_id(user_id)
        
        if not user or not user.faculty:
            return jsonify({
                'status': 'error',
                'message': 'Faculty profile not found'
            }), 404
        
        faculty_id = user.faculty.faculty_id
        
        # Get at-risk students
        at_risk_students = faculty_service.get_at_risk_students(faculty_id)
        
        # Get total student count for context
        summary = faculty_service.get_dashboard_summary(faculty_id)
        
        return jsonify({
            'status': 'success',
            'data': {
                'students': at_risk_students,
                'total_students': summary['student_count']
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting at-risk students: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to load at-risk students'
        }), 500

@faculty_bp.route('/assessments', methods=['GET'])
@jwt_required()
@faculty_required
def get_assessments():
    """Get recent assessments for faculty's courses"""
    try:
        # Get current user
        user_id = get_jwt_identity()
        user = get_user_by_id(user_id)
        
        if not user or not user.faculty:
            return jsonify({
                'status': 'error',
                'message': 'Faculty profile not found'
            }), 404
        
        faculty_id = user.faculty.faculty_id
        
        # Get assessments
        assessments = faculty_service.get_recent_assessments(faculty_id)
        
        return jsonify({
            'status': 'success',
            'data': {
                'assessments': assessments
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting assessments: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to load assessments'
        }), 500

@faculty_bp.route('/analytics', methods=['GET'])
@jwt_required()
@faculty_required
def get_analytics():
    """Get analytics data for faculty's courses"""
    try:
        # Get current user
        user_id = get_jwt_identity()
        user = get_user_by_id(user_id)
        
        if not user or not user.faculty:
            return jsonify({
                'status': 'error',
                'message': 'Faculty profile not found'
            }), 404
        
        faculty_id = user.faculty.faculty_id
        
        # For now, return basic analytics
        # This can be expanded with more detailed analytics
        courses = faculty_service.get_teaching_courses(faculty_id)
        
        analytics = {
            'total_courses': len(courses),
            'average_attendance': 85.5,  # Placeholder
            'average_grade': 'B',  # Placeholder
            'submission_rate': 92.3  # Placeholder
        }
        
        return jsonify({
            'status': 'success',
            'data': analytics
        })
        
    except Exception as e:
        logger.error(f"Error getting analytics: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to load analytics'
        }), 500

# =====================================================
# INDIVIDUAL STUDENT DETAIL ROUTES
# =====================================================

@faculty_bp.route('/students/<string:student_id>', methods=['GET'])
@jwt_required()
@faculty_required
def get_student_detail(student_id):
    """Get detailed information for a specific student"""
    try:
        # Get current user
        user_id = get_jwt_identity()
        user = get_user_by_id(user_id)
        
        if not user or not user.faculty:
            return jsonify({
                'status': 'error',
                'message': 'Faculty profile not found'
            }), 404
        
        faculty_id = user.faculty.faculty_id
        
        # Get student detail
        student_detail = faculty_service.get_student_detail(faculty_id, student_id)
        
        if not student_detail:
            return jsonify({
                'status': 'error',
                'message': 'Student not found or not enrolled in your courses'
            }), 404
        
        return jsonify({
            'status': 'success',
            'data': {
                'student': student_detail
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting student detail: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to load student details'
        }), 500

@faculty_bp.route('/students/<string:student_id>/grades', methods=['GET'])
@jwt_required()
@faculty_required
def get_student_grades(student_id):
    """Get grade data for a specific student"""
    try:
        # Get current user
        user_id = get_jwt_identity()
        user = get_user_by_id(user_id)
        
        if not user or not user.faculty:
            return jsonify({
                'status': 'error',
                'message': 'Faculty profile not found'
            }), 404
        
        faculty_id = user.faculty.faculty_id
        
        # Get offering_id from query params
        offering_id = request.args.get('offering_id', type=int)
        
        # Get student grade data
        grade_data = faculty_service.get_student_grade_detail(faculty_id, student_id, offering_id)
        
        return jsonify({
            'status': 'success',
            'data': grade_data
        })
        
    except Exception as e:
        logger.error(f"Error getting student grades: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to load grade data'
        }), 500

@faculty_bp.route('/students/<string:student_id>/attendance', methods=['GET'])
@jwt_required()
@faculty_required
def get_student_attendance(student_id):
    """Get attendance data for a specific student"""
    try:
        # Get current user
        user_id = get_jwt_identity()
        user = get_user_by_id(user_id)
        
        if not user or not user.faculty:
            return jsonify({
                'status': 'error',
                'message': 'Faculty profile not found'
            }), 404
        
        faculty_id = user.faculty.faculty_id
        
        # Get student attendance data
        attendance_data = faculty_service.get_student_attendance_detail(faculty_id, student_id)
        
        return jsonify({
            'status': 'success',
            'data': attendance_data
        })
        
    except Exception as e:
        logger.error(f"Error getting student attendance: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to load attendance data'
        }), 500

@faculty_bp.route('/students/<string:student_id>/interventions', methods=['GET'])
@jwt_required()
@faculty_required
def get_student_interventions(student_id):
    """Get intervention history for a specific student"""
    try:
        # Get current user
        user_id = get_jwt_identity()
        user = get_user_by_id(user_id)
        
        if not user or not user.faculty:
            return jsonify({
                'status': 'error',
                'message': 'Faculty profile not found'
            }), 404
        
        faculty_id = user.faculty.faculty_id
        
        # Get student interventions
        interventions = faculty_service.get_student_interventions(faculty_id, student_id)
        
        return jsonify({
            'status': 'success',
            'data': {
                'interventions': interventions
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting student interventions: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to load intervention data'
        }), 500

@faculty_bp.route('/interventions', methods=['POST'])
@jwt_required()
@faculty_required
def add_intervention():
    """Add new intervention for a student"""
    try:
        # Get current user
        user_id = get_jwt_identity()
        user = get_user_by_id(user_id)
        
        if not user or not user.faculty:
            return jsonify({
                'status': 'error',
                'message': 'Faculty profile not found'
            }), 404
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['student_id', 'offering_id', 'type', 'notes']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'status': 'error',
                    'message': f'Missing required field: {field}'
                }), 400
        
        # For now, just return success since intervention model might not be implemented yet
        # In a real implementation, you would save to database
        
        return jsonify({
            'status': 'success',
            'message': 'Intervention added successfully',
            'data': {
                'intervention_id': 'temp_id',  # Would be real ID from database
                'type': data['type'],
                'notes': data['notes'],
                'created_date': '2024-06-12'  # Would be actual timestamp
            }
        })
        
    except Exception as e:
        logger.error(f"Error adding intervention: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to add intervention'
        }), 500

# =====================================================
# ATTENDANCE ROUTES
# =====================================================

@faculty_bp.route('/attendance/roster/<int:offering_id>', methods=['GET'])
@jwt_required()
@faculty_required
def get_course_roster(offering_id):
    """Get course roster with attendance status for a specific date"""
    try:
        # Get date from query params (default to today)
        date_str = request.args.get('date')
        if date_str:
            try:
                attendance_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return error_response('Invalid date format. Use YYYY-MM-DD', 400)
        else:
            attendance_date = date.today()
        
        # Get roster
        roster = attendance_service.get_course_roster(offering_id, attendance_date)
        
        return api_response({
            'roster': roster,
            'date': attendance_date.isoformat(),
            'offering_id': offering_id
        }, 'Roster retrieved successfully')
        
    except Exception as e:
        logger.error(f"Error getting roster: {str(e)}")
        return error_response('Failed to get course roster', 500)

@faculty_bp.route('/attendance/mark', methods=['POST'])
@jwt_required()
@faculty_required
def mark_attendance():
    """Mark attendance for a single student"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['enrollment_id', 'attendance_date', 'status']
        for field in required_fields:
            if field not in data:
                return error_response(f'Missing required field: {field}', 400)
        
        # Validate status
        valid_statuses = ['present', 'absent', 'late', 'excused']
        if data['status'] not in valid_statuses:
            return error_response(f'Invalid status. Must be one of: {valid_statuses}', 400)
        
        # Parse date
        try:
            attendance_date = datetime.strptime(data['attendance_date'], '%Y-%m-%d').date()
        except ValueError:
            return error_response('Invalid date format. Use YYYY-MM-DD', 400)
        
        # Parse check-in time if provided
        check_in_time = None
        if data.get('check_in_time'):
            try:
                check_in_time = datetime.strptime(data['check_in_time'], '%H:%M').time()
            except ValueError:
                return error_response('Invalid time format. Use HH:MM', 400)
        
        # Get current user for recording
        user_id = get_jwt_identity()
        user = get_user_by_id(user_id)
        recorded_by = user.faculty.faculty_id if user and user.faculty else str(user_id)
        
        # Mark attendance
        attendance_record = attendance_service.mark_attendance(
            enrollment_id=data['enrollment_id'],
            attendance_date=attendance_date,
            status=data['status'],
            check_in_time=check_in_time,
            notes=data.get('notes'),
            recorded_by=recorded_by
        )
        
        if attendance_record:
            return api_response({
                'attendance_id': attendance_record.attendance_id,
                'status': attendance_record.status
            }, 'Attendance marked successfully')
        else:
            return error_response('Failed to mark attendance', 500)
        
    except Exception as e:
        logger.error(f"Error marking attendance: {str(e)}")
        return error_response('Failed to mark attendance', 500)

# =====================================================
# ASSESSMENT ROUTES
# =====================================================

@faculty_bp.route('/assessment-types', methods=['GET'])
@jwt_required()
@faculty_required
def get_assessment_types():
    """Get available assessment types"""
    try:
        assessment_types = assessment_service.get_assessment_types()
        
        return api_response({
            'assessment_types': assessment_types
        }, 'Assessment types retrieved successfully')
        
    except Exception as e:
        logger.error(f"Error getting assessment types: {str(e)}")
        return error_response('Failed to get assessment types', 500)

@faculty_bp.route('/assessments/<int:offering_id>', methods=['GET'])
@jwt_required()
@faculty_required
def get_course_assessments(offering_id):
    """Get all assessments for a course offering"""
    try:
        # TODO: Verify faculty teaches this course
        
        assessments = assessment_service.get_assessments_by_offering(offering_id)
        
        return api_response({
            'assessments': assessments,
            'offering_id': offering_id
        }, 'Assessments retrieved successfully')
        
    except Exception as e:
        logger.error(f"Error getting assessments: {str(e)}")
        return error_response('Failed to get assessments', 500)
    
    
@faculty_bp.route('/courses/<int:offering_id>/students', methods=['GET'])
@jwt_required()
@faculty_required
def get_course_students(offering_id):
    """Get students enrolled in a specific course offering"""
    try:
        # Get current user
        user_id = get_jwt_identity()
        user = get_user_by_id(user_id)
        
        if not user or not user.faculty:
            return jsonify({
                'status': 'error',
                'message': 'Faculty profile not found'
            }), 404
        
        faculty_id = user.faculty.faculty_id
        
        # Verify faculty teaches this course
        course_offering = CourseOffering.query.filter_by(
            offering_id=offering_id,
            faculty_id=faculty_id
        ).first()
        
        if not course_offering:
            return jsonify({
                'status': 'error',
                'message': 'You are not authorized to view this course'
            }), 403
        
        # Get students enrolled in this course
        students = faculty_service.get_students_by_course(offering_id)
        
        return jsonify({
            'status': 'success',
            'data': {
                'students': students,
                'offering_id': offering_id,
                'course_info': {
                    'course_code': course_offering.course.course_code,
                    'course_name': course_offering.course.course_name,
                    'section': course_offering.section_number
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting course students: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to load course students'
        }), 500

@faculty_bp.route('/dashboard/summary', methods=['GET'])
@jwt_required()
@faculty_required
def get_dashboard_summary():
    """Get dashboard summary for faculty"""
    try:
        user_id = get_jwt_identity()
        user = get_user_by_id(user_id)
        
        if not user or not user.faculty:
            return jsonify({
                'status': 'error',
                'message': 'Faculty profile not found'
            }), 404
        
        faculty_id = user.faculty.faculty_id
        
        # Get dashboard summary
        summary = faculty_service.get_dashboard_summary(faculty_id)
        
        return jsonify({
            'status': 'success',
            'data': summary
        })
        
    except Exception as e:
        logger.error(f"Error getting dashboard summary: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to load dashboard summary'
        }), 500