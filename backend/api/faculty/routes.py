from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.services.faculty_service import faculty_service
from backend.services.attendance_service import attendance_service  # ADD THIS
from backend.services.auth_service import get_user_by_id
from backend.services.assessment_service import assessment_service
from backend.middleware.auth_middleware import faculty_required
from backend.utils.api import api_response, error_response  # ADD THIS
from datetime import datetime, date  # ADD THIS
import logging

logger = logging.getLogger(__name__)

faculty_bp = Blueprint('faculty', __name__, url_prefix='/api/faculty')

# =====================================================
# EXISTING ROUTES (keep your current routes as they are)
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
# NEW ATTENDANCE ROUTES (ADD THESE)
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

@faculty_bp.route('/attendance/bulk-mark', methods=['POST'])
@jwt_required()
@faculty_required
def bulk_mark_attendance():
    """Mark attendance for multiple students"""
    try:
        data = request.get_json()
        
        if 'attendance_records' not in data:
            return error_response('Missing attendance_records field', 400)
        
        attendance_data = data['attendance_records']
        
        # Get current user for recording
        user_id = get_jwt_identity()
        user = get_user_by_id(user_id)
        recorded_by = user.faculty.faculty_id if user and user.faculty else str(user_id)
        
        # Process attendance data
        processed_data = []
        for record in attendance_data:
            # Parse date
            try:
                attendance_date = datetime.strptime(record['attendance_date'], '%Y-%m-%d').date()
            except ValueError:
                return error_response('Invalid date format in record. Use YYYY-MM-DD', 400)
            
            processed_data.append({
                'enrollment_id': record['enrollment_id'],
                'attendance_date': attendance_date,
                'status': record['status'],
                'check_in_time': None,
                'notes': record.get('notes')
            })
        
        # Bulk mark attendance
        results = attendance_service.bulk_mark_attendance(processed_data, recorded_by)
        
        # Count successes and failures
        successful = sum(1 for r in results if r['success'])
        failed = len(results) - successful
        
        return api_response({
            'results': results,
            'summary': {
                'total': len(results),
                'successful': successful,
                'failed': failed
            }
        }, f'Bulk attendance completed: {successful} successful, {failed} failed')
        
    except Exception as e:
        logger.error(f"Error in bulk attendance marking: {str(e)}")
        return error_response('Failed to process bulk attendance', 500)

@faculty_bp.route('/attendance/summary/<int:offering_id>', methods=['GET'])
@jwt_required()
@faculty_required
def get_attendance_summary(offering_id):
    """Get attendance summary for a course"""
    try:
        # Get summary
        summary = attendance_service.get_attendance_summary(offering_id)
        
        return api_response({
            'summary': summary,
            'offering_id': offering_id
        }, 'Attendance summary retrieved successfully')
        
    except Exception as e:
        logger.error(f"Error getting attendance summary: {str(e)}")
        return error_response('Failed to get attendance summary', 500)
    



    # =====================================================
# ASSESSMENT MANAGEMENT ROUTES
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

@faculty_bp.route('/assessments', methods=['POST'])
@jwt_required()
@faculty_required
def create_assessment():
    """Create a new assessment"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['offering_id', 'type_id', 'title', 'max_score']
        for field in required_fields:
            if field not in data:
                return error_response(f'Missing required field: {field}', 400)
        
        # Get current user for tracking
        user_id = get_jwt_identity()
        user = get_user_by_id(user_id)
        created_by = user.faculty.faculty_id if user and user.faculty else str(user_id)
        
        # Create assessment
        assessment = assessment_service.create_assessment(
            offering_id=data['offering_id'],
            type_id=data['type_id'],
            title=data['title'],
            max_score=data['max_score'],
            due_date=data.get('due_date'),
            weight=data.get('weight'),
            description=data.get('description'),
            created_by=created_by
        )
        
        if assessment:
            return api_response({
                'assessment_id': assessment.assessment_id,
                'title': assessment.title
            }, 'Assessment created successfully')
        else:
            return error_response('Failed to create assessment', 500)
        
    except Exception as e:
        logger.error(f"Error creating assessment: {str(e)}")
        return error_response('Failed to create assessment', 500)

@faculty_bp.route('/assessments/<int:assessment_id>/roster', methods=['GET'])
@jwt_required()
@faculty_required
def get_assessment_roster(assessment_id):
    """Get roster for grade entry"""
    try:
        # TODO: Verify faculty teaches this course
        
        roster_data = assessment_service.get_assessment_roster(assessment_id)
        
        if roster_data:
            return api_response(roster_data, 'Assessment roster retrieved successfully')
        else:
            return error_response('Assessment not found', 404)
        
    except Exception as e:
        logger.error(f"Error getting assessment roster: {str(e)}")
        return error_response('Failed to get assessment roster', 500)

@faculty_bp.route('/assessments/grade', methods=['POST'])
@jwt_required()
@faculty_required
def enter_single_grade():
    """Enter grade for a single student"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['enrollment_id', 'assessment_id', 'score']
        for field in required_fields:
            if field not in data:
                return error_response(f'Missing required field: {field}', 400)
        
        # Get current user for tracking
        user_id = get_jwt_identity()
        user = get_user_by_id(user_id)
        graded_by = user.faculty.faculty_id if user and user.faculty else str(user_id)
        
        # Enter grade
        submission, error = assessment_service.enter_grade(
            enrollment_id=data['enrollment_id'],
            assessment_id=data['assessment_id'],
            score=data['score'],
            feedback=data.get('feedback'),
            graded_by=graded_by
        )
        
        if submission:
            return api_response({
                'submission_id': submission.submission_id,
                'score': float(submission.score),
                'percentage': float(submission.percentage)
            }, 'Grade entered successfully')
        else:
            return error_response(error or 'Failed to enter grade', 400)
        
    except Exception as e:
        logger.error(f"Error entering grade: {str(e)}")
        return error_response('Failed to enter grade', 500)

@faculty_bp.route('/assessments/bulk-grade', methods=['POST'])
@jwt_required()
@faculty_required
def enter_bulk_grades():
    """Enter grades for multiple students"""
    try:
        data = request.get_json()
        
        if 'grades' not in data:
            return error_response('Missing grades field', 400)
        
        grades_data = data['grades']
        
        # Get current user for tracking
        user_id = get_jwt_identity()
        user = get_user_by_id(user_id)
        graded_by = user.faculty.faculty_id if user and user.faculty else str(user_id)
        
        # Enter grades
        results = assessment_service.bulk_enter_grades(grades_data, graded_by)
        
        # Count successes and failures
        successful = sum(1 for r in results if r['success'])
        failed = len(results) - successful
        
        return api_response({
            'results': results,
            'summary': {
                'total': len(results),
                'successful': successful,
                'failed': failed
            }
        }, f'Bulk grading completed: {successful} successful, {failed} failed')
        
    except Exception as e:
        logger.error(f"Error in bulk grading: {str(e)}")
        return error_response('Failed to process bulk grading', 500)

@faculty_bp.route('/assessments/<int:assessment_id>/statistics', methods=['GET'])
@jwt_required()
@faculty_required
def get_assessment_statistics(assessment_id):
    """Get assessment statistics"""
    try:
        # TODO: Verify faculty teaches this course
        
        statistics = assessment_service.get_assessment_statistics(assessment_id)
        
        if statistics:
            return api_response(statistics, 'Statistics retrieved successfully')
        else:
            return error_response('Assessment not found', 404)
        
    except Exception as e:
        logger.error(f"Error getting assessment statistics: {str(e)}")
        return error_response('Failed to get assessment statistics', 500)

@faculty_bp.route('/assessments/<int:assessment_id>', methods=['DELETE'])
@jwt_required()
@faculty_required
def delete_assessment(assessment_id):
    """Delete an assessment"""
    try:
        # TODO: Verify faculty teaches this course
        
        success, message = assessment_service.delete_assessment(assessment_id)
        
        if success:
            return api_response(message='Assessment deleted successfully')
        else:
            return error_response(message, 400)
        
    except Exception as e:
        logger.error(f"Error deleting assessment: {str(e)}")
        return error_response('Failed to delete assessment', 500)