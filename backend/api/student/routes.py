from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.services.student_service import student_service
from backend.services.assessment_service import assessment_service
from backend.services.auth_service import get_user_by_id
from backend.middleware.auth_middleware import student_required
from backend.models import Course, CourseOffering, Enrollment, Faculty, AcademicTerm, Prediction, Assessment, Attendance, AssessmentSubmission
from sqlalchemy import func, desc
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

student_bp = Blueprint('student', __name__, url_prefix='/api/student')

@student_bp.route('/dashboard', methods=['GET'])
@jwt_required()
@student_required
def get_dashboard():
    """Get comprehensive student dashboard data"""
    try:
        # Get current user
        user_id = get_jwt_identity()
        user = get_user_by_id(user_id)
        
        if not user or not user.student:
            return jsonify({
                'status': 'error',
                'message': 'Student profile not found'
            }), 404
        
        student_id = user.student.student_id
        
        # Get dashboard summary
        summary = student_service.get_dashboard_summary(student_id)
        
        # Get recent courses (for dashboard display)
        recent_courses = student_service.get_enrolled_courses(student_id)[:3]  # Limit to 3
        
        return jsonify({
            'status': 'success',
            'data': {
                'summary': summary,
                'recent_courses': recent_courses,
                'student': {
                    'student_id': student_id,
                    'name': f"{user.student.first_name} {user.student.last_name}",
                    'email': user.email,
                    'program_code': user.student.program_code,
                    'year_of_study': user.student.year_of_study
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting dashboard: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to load dashboard data'
        }), 500

@student_bp.route('/courses', methods=['GET'])
@jwt_required()
@student_required
def get_courses():
    """Get enrolled courses for the student with detailed information"""
    try:
        # Get current user
        user_id = get_jwt_identity()
        user = get_user_by_id(user_id)
        
        if not user or not user.student:
            return jsonify({
                'status': 'error',
                'message': 'Student profile not found'
            }), 404
        
        student_id = user.student.student_id
        
        # Get term from query params (optional)
        term_id = request.args.get('term_id', type=int)
        
        # Get courses using the enhanced service method
        courses = student_service.get_enrolled_courses(student_id, term_id)
        
        return jsonify({
            'status': 'success',
            'data': {
                'courses': courses,
                'student_info': {
                    'student_id': student_id,
                    'name': f"{user.student.first_name} {user.student.last_name}",
                    'email': user.email
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting courses: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to load courses'
        }), 500

@student_bp.route('/attendance', methods=['GET'])
@jwt_required()
@student_required
def get_attendance():
    """Get attendance data for the student"""
    try:
        # Get current user
        user_id = get_jwt_identity()
        user = get_user_by_id(user_id)
        
        if not user or not user.student:
            return jsonify({
                'status': 'error',
                'message': 'Student profile not found'
            }), 404
        
        student_id = user.student.student_id
        
        # Get course_id from query params (optional)
        course_id = request.args.get('course_id')
        
        # Get attendance summary
        attendance = student_service.get_attendance_summary(student_id, course_id)
        
        return jsonify({
            'status': 'success',
            'data': {
                'attendance': attendance
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting attendance: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to load attendance data'
        }), 500

@student_bp.route('/assessments', methods=['GET'])
@jwt_required()
@student_required
def get_assessments():
    """Get assessments for the student"""
    try:
        # Get current user
        user_id = get_jwt_identity()
        user = get_user_by_id(user_id)
        
        if not user or not user.student:
            return jsonify({
                'status': 'error',
                'message': 'Student profile not found'
            }), 404
        
        student_id = user.student.student_id
        
        # Get course_id from query params (optional)
        course_id = request.args.get('course_id')
        
        # Get assessments
        assessments = student_service.get_assessments(student_id, course_id)
        
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

@student_bp.route('/predictions', methods=['GET'])
@jwt_required()
@student_required
def get_predictions():
    """Get grade predictions for the student"""
    try:
        # Get current user
        user_id = get_jwt_identity()
        user = get_user_by_id(user_id)
        
        if not user or not user.student:
            return jsonify({
                'status': 'error',
                'message': 'Student profile not found'
            }), 404
        
        student_id = user.student.student_id
        
        # Get predictions
        predictions = student_service.get_grade_predictions(student_id)
        
        return jsonify({
            'status': 'success',
            'data': {
                'predictions': predictions
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting predictions: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to load predictions'
        }), 500
    


    
@student_bp.route('/assessments/<int:offering_id>', methods=['GET'])
@jwt_required()
@student_required
def get_student_course_assessments(offering_id):
    """Get assessments for a specific course"""
    try:
        # Get current user
        user_id = get_jwt_identity()
        user = get_user_by_id(user_id)
        
        if not user or not user.student:
            return jsonify({
                'status': 'error',
                'message': 'Student profile not found'
            }), 404
        
        student_id = user.student.student_id
        
        # Get assessments for this course
        assessments = assessment_service.get_student_assessments(student_id, offering_id)
        
        return jsonify({
            'status': 'success',
            'data': {
                'assessments': assessments,
                'offering_id': offering_id
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting student assessments: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to load assessments'
        }), 500

@student_bp.route('/assessments/all', methods=['GET'])
@jwt_required()
@student_required
def get_all_student_assessments():
    """Get all assessments for a student across all courses"""
    try:
        # Get current user
        user_id = get_jwt_identity()
        user = get_user_by_id(user_id)
        
        if not user or not user.student:
            return jsonify({
                'status': 'error',
                'message': 'Student profile not found'
            }), 404
        
        student_id = user.student.student_id
        
        # Get all assessments
        assessments = assessment_service.get_student_assessments(student_id)
        
        # Group by course for better organization
        courses = {}
        for assessment in assessments:
            course_key = f"{assessment['course_code']}"
            if course_key not in courses:
                courses[course_key] = {
                    'course_code': assessment['course_code'],
                    'course_name': assessment['course_name'],
                    'assessments': []
                }
            courses[course_key]['assessments'].append(assessment)
        
        return jsonify({
            'status': 'success',
            'data': {
                'courses': list(courses.values()),
                'total_assessments': len(assessments)
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting all student assessments: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to load assessments'
        }), 500

@student_bp.route('/grades/summary', methods=['GET'])
@jwt_required()
@student_required
def get_grade_summary():
    """Get grade summary for student"""
    try:
        # Get current user
        user_id = get_jwt_identity()
        user = get_user_by_id(user_id)
        
        if not user or not user.student:
            return jsonify({
                'status': 'error',
                'message': 'Student profile not found'
            }), 404
        
        student_id = user.student.student_id
        
        # Get all assessments with grades
        assessments = assessment_service.get_student_assessments(student_id)
        
        # Calculate summary statistics
        graded_assessments = [a for a in assessments if a['score'] is not None]
        
        if graded_assessments:
            total_points = sum(a['score'] for a in graded_assessments)
            total_possible = sum(a['max_score'] for a in graded_assessments)
            overall_percentage = (total_points / total_possible * 100) if total_possible > 0 else 0
            
            # Count by grade
            grade_counts = {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'F': 0}
            for assessment in graded_assessments:
                percentage = assessment['percentage']
                if percentage >= 90:
                    grade_counts['A'] += 1
                elif percentage >= 80:
                    grade_counts['B'] += 1
                elif percentage >= 70:
                    grade_counts['C'] += 1
                elif percentage >= 60:
                    grade_counts['D'] += 1
                else:
                    grade_counts['F'] += 1
        else:
            overall_percentage = 0
            grade_counts = {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'F': 0}
        
        summary = {
            'total_assessments': len(assessments),
            'graded_assessments': len(graded_assessments),
            'pending_assessments': len(assessments) - len(graded_assessments),
            'overall_percentage': round(overall_percentage, 2),
            'grade_distribution': grade_counts
        }
        
        return jsonify({
            'status': 'success',
            'data': summary
        })
        
    except Exception as e:
        logger.error(f"Error getting grade summary: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to load grade summary'
        }), 500
    
@student_bp.route('/courses/<string:course_id>', methods=['GET'])
@jwt_required()
@student_required
def get_course_details(course_id):
    """Get detailed information for a specific course"""
    try:
        # Get current user
        user_id = get_jwt_identity()
        user = get_user_by_id(user_id)
        
        if not user or not user.student:
            return jsonify({
                'status': 'error',
                'message': 'Student profile not found'
            }), 404
        
        student_id = user.student.student_id
        
        # Get the specific course enrollment
        enrollment = db.session.query(
            Enrollment, Course, CourseOffering, Faculty
        ).join(
            CourseOffering, CourseOffering.offering_id == Enrollment.offering_id
        ).join(
            Course, Course.course_id == CourseOffering.course_id
        ).outerjoin(
            Faculty, Faculty.faculty_id == CourseOffering.faculty_id
        ).filter(
            Enrollment.student_id == student_id,
            Course.course_id == course_id,
            Enrollment.enrollment_status == 'enrolled'
        ).first()
        
        if not enrollment:
            return jsonify({
                'status': 'error',
                'message': 'Course not found or not enrolled'
            }), 404
        
        enrollment_obj, course, offering, faculty = enrollment
        
        # Get detailed course information
        course_details = {
            'course_id': course.course_id,
            'course_code': course.course_code,
            'course_name': course.course_name,
            'credits': course.credits,
            'description': course.description,
            'section': offering.section_number,
            'meeting_pattern': offering.meeting_pattern,
            'location': offering.location,
            'instructor_name': f"{faculty.first_name} {faculty.last_name}" if faculty else 'TBA',
            'instructor_email': faculty.email if faculty else None,
            'enrollment_status': enrollment_obj.enrollment_status,
            'current_grade': enrollment_obj.final_grade
        }
        
        # Get attendance data
        attendance_summary = student_service.get_attendance_summary(student_id, course_id)
        
        # Get assessments for this course
        assessments = db.session.query(Assessment).join(
            CourseOffering, CourseOffering.offering_id == Assessment.offering_id
        ).join(
            Enrollment, Enrollment.offering_id == CourseOffering.offering_id
        ).filter(
            Enrollment.student_id == student_id,
            CourseOffering.course_id == course_id
        ).all()
        
        assessment_data = []
        for assessment in assessments:
            # Get submission if exists
            submission = AssessmentSubmission.query.filter_by(
                assessment_id=assessment.assessment_id,
                student_id=student_id
            ).first()
            
            assessment_data.append({
                'assessment_id': assessment.assessment_id,
                'title': assessment.title,
                'type': assessment.type_id,  # You may want to join with AssessmentType
                'max_score': assessment.max_score,
                'due_date': assessment.due_date.isoformat() if assessment.due_date else None,
                'weight': float(assessment.weight),
                'submission_score': submission.score if submission else None,
                'submitted_at': submission.submitted_at.isoformat() if submission and submission.submitted_at else None
            })
        
        return jsonify({
            'status': 'success',
            'data': {
                'course': course_details,
                'attendance': attendance_summary,
                'assessments': assessment_data
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting course details: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to load course details'
        }), 500