# backend/api/student/routes.py - CLEANED VERSION (Remove attendance routes)
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.services.student_service import student_service
from backend.services.assessment_service import assessment_service
from backend.services.auth_service import get_user_by_id
from backend.middleware.auth_middleware import student_required
from backend.services.course_service import course_service
from backend.models import Course, CourseOffering, Enrollment, Faculty, AcademicTerm, Prediction, Assessment, AssessmentSubmission
from sqlalchemy import func, desc
from backend.utils.api import api_response, error_response
from backend.models import User
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

# REMOVED ATTENDANCE ROUTE - Now handled by attendance_routes.py

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
    
@student_bp.route('/profile', methods=['GET'])
@jwt_required()
@student_required
def get_profile():
    """Get student profile"""
    try:
        # Get current user
        user_id = get_jwt_identity()
        user = get_user_by_id(user_id)
        
        if not user or not user.student:
            return error_response('Student profile not found', 404)
        
        student = user.student
        
        # Build profile response
        profile_data = {
            'user': {
                'user_id': user.user_id,
                'username': user.username,
                'email': user.email,
                'last_login': user.last_login.isoformat() if user.last_login else None
            },
            'student': {
                'student_id': student.student_id,
                'first_name': student.first_name,
                'last_name': student.last_name,
                'date_of_birth': student.date_of_birth.isoformat() if student.date_of_birth else None,
                'gender': student.gender,
                'program_code': student.program_code,
                'year_of_study': student.year_of_study,
                'enrollment_date': student.enrollment_date.isoformat() if student.enrollment_date else None,
                'expected_graduation': student.expected_graduation.isoformat() if student.expected_graduation else None,
                'gpa': float(student.gpa) if student.gpa else None,
                'status': student.status
            }
        }
        
        return api_response(profile_data, 'Profile retrieved successfully')
        
    except Exception as e:
        logger.error(f"Error getting profile: {str(e)}")
        return error_response('Failed to retrieve profile', 500)

@student_bp.route('/profile', methods=['PUT'])
@jwt_required()
@student_required
def update_profile():
    """Update student profile"""
    try:
        # Get current user
        user_id = get_jwt_identity()
        user = get_user_by_id(user_id)
        
        if not user or not user.student:
            return error_response('Student profile not found', 404)
        
        data = request.get_json()
        if not data:
            return error_response('No data provided', 400)
        
        student = user.student
        
        # Update allowed fields only
        allowed_student_fields = ['first_name', 'last_name', 'date_of_birth', 'gender']
        allowed_user_fields = ['email']
        
        # Update student fields
        for field in allowed_student_fields:
            if field in data:
                setattr(student, field, data[field])
        
        # Update user fields
        for field in allowed_user_fields:
            if field in data:
                # Check if email already exists
                if field == 'email' and data[field] != user.email:
                    existing = User.query.filter_by(email=data[field]).first()
                    if existing:
                        return error_response('Email already in use', 400)
                setattr(user, field, data[field])
        
        # Save changes
        db.session.commit()
        
        return api_response({'message': 'Profile updated successfully'})
        
    except Exception as e:
        logger.error(f"Error updating profile: {str(e)}")
        db.session.rollback()
        return error_response('Failed to update profile', 500)
    
@student_bp.route('/courses/available', methods=['GET'])
@jwt_required()
@student_required
def get_available_courses():
    """Get courses available for enrollment"""
    try:
        # Get current user
        user_id = get_jwt_identity()
        user = get_user_by_id(user_id)
        
        if not user or not user.student:
            return error_response('Student profile not found', 404)
        
        student_id = user.student.student_id
        
        # Get term from query params
        term_id = request.args.get('term_id', type=int)
        
        # Get available courses
        courses = course_service.get_available_courses(student_id, term_id)
        
        return api_response({
            'courses': courses,
            'count': len(courses)
        }, 'Available courses retrieved successfully')
        
    except Exception as e:
        logger.error(f"Error getting available courses: {str(e)}")
        return error_response('Failed to retrieve available courses', 500)

@student_bp.route('/courses/enroll', methods=['POST'])
@jwt_required()
@student_required
def enroll_in_course():
    """Enroll in a course"""
    try:
        # Get current user
        user_id = get_jwt_identity()
        user = get_user_by_id(user_id)
        
        if not user or not user.student:
            return error_response('Student profile not found', 404)
        
        data = request.get_json()
        if not data or 'offering_id' not in data:
            return error_response('Course offering ID is required', 400)
        
        student_id = user.student.student_id
        offering_id = data['offering_id']
        
        # Enroll student
        enrollment, error = course_service.enroll_student(student_id, offering_id)
        
        if error:
            return error_response(error, 400)
        
        return api_response({
            'message': 'Successfully enrolled in course',
            'enrollment_id': enrollment.enrollment_id
        })
        
    except Exception as e:
        logger.error(f"Error enrolling in course: {str(e)}")
        return error_response('Failed to enroll in course', 500)

@student_bp.route('/courses/drop', methods=['POST'])
@jwt_required()
@student_required
def drop_course():
    """Drop a course"""
    try:
        # Get current user
        user_id = get_jwt_identity()
        user = get_user_by_id(user_id)
        
        if not user or not user.student:
            return error_response('Student profile not found', 404)
        
        data = request.get_json()
        if not data or 'offering_id' not in data:
            return error_response('Course offering ID is required', 400)
        
        student_id = user.student.student_id
        offering_id = data['offering_id']
        
        # Drop course
        success, message = course_service.drop_course(student_id, offering_id)
        
        if not success:
            return error_response(message, 400)
        
        return api_response({'message': message})
        
    except Exception as e:
        logger.error(f"Error dropping course: {str(e)}")
        return error_response('Failed to drop course', 500)