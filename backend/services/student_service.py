from backend.models import (
    Student, Enrollment, Course, Assessment, Attendance, 
    CourseOffering, Prediction, AssessmentSubmission
)
from backend.extensions import db
from sqlalchemy import func, and_
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class StudentService:
    """Service class for student-related operations"""
    
    @staticmethod
    def get_student_by_user_id(user_id):
        """Get student record by user ID"""
        try:
            student = Student.query.filter_by(user_id=user_id).first()
            return student
        except Exception as e:
            logger.error(f"Error getting student: {str(e)}")
            return None
    
    @staticmethod  # FIXED: Added missing @staticmethod decorator
    def get_enrolled_courses(student_id, term_id=None):
        """Get all courses enrolled by a student"""
        try:
            logger.info(f"Getting courses for student: {student_id}")
            
            # Fixed query with proper joins and attributes
            query = db.session.query(
                Course.course_id,
                Course.course_code,
                Course.course_name,
                Course.credits,
                Enrollment.enrollment_id,
                Enrollment.enrollment_status,
                Enrollment.final_grade
            ).select_from(Enrollment).join(
                CourseOffering, Enrollment.offering_id == CourseOffering.offering_id
            ).join(
                Course, CourseOffering.course_id == Course.course_id
            ).filter(
                Enrollment.student_id == student_id,
                Enrollment.enrollment_status.in_(['enrolled', 'completed'])
            )
            
            # Filter by term if provided
            if term_id:
                query = query.filter(CourseOffering.term_id == term_id)
            
            courses = query.all()
            logger.info(f"Found {len(courses)} courses for student {student_id}")
            
            # Convert to dictionary
            result = []
            for course in courses:
                result.append({
                    'course_id': course.course_id,
                    'course_code': course.course_code,
                    'course_name': course.course_name,
                    'credits': course.credits,
                    'enrollment_id': course.enrollment_id,
                    'enrollment_status': course.enrollment_status,
                    'final_grade': course.final_grade
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting enrolled courses: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    @staticmethod
    def get_attendance_summary(student_id, course_id=None):
        """Get attendance summary for a student"""
        try:
            # Simplified query without func.case
            query = db.session.query(
                CourseOffering.course_id,
                Course.course_name,
                func.count(Attendance.attendance_id).label('total_classes')
            ).select_from(Enrollment).join(
                Attendance, Attendance.enrollment_id == Enrollment.enrollment_id
            ).join(
                CourseOffering, Enrollment.offering_id == CourseOffering.offering_id
            ).join(
                Course, CourseOffering.course_id == Course.course_id
            ).filter(
                Enrollment.student_id == student_id
            )
            
            # Filter by course if provided
            if course_id:
                query = query.filter(CourseOffering.course_id == course_id)
            
            # Group by course
            query = query.group_by(CourseOffering.course_id, Course.course_name)
            
            attendance_data = query.all()
            
            # Calculate attendance manually
            result = []
            for data in attendance_data:
                # Get attended count separately
                attended_query = db.session.query(
                    func.count(Attendance.attendance_id)
                ).select_from(Enrollment).join(
                    Attendance, Attendance.enrollment_id == Enrollment.enrollment_id
                ).join(
                    CourseOffering, Enrollment.offering_id == CourseOffering.offering_id
                ).filter(
                    Enrollment.student_id == student_id,
                    CourseOffering.course_id == data.course_id,
                    Attendance.status.in_(['present', 'late'])
                )
                
                attended_classes = attended_query.scalar() or 0
                
                attendance_rate = 0
                if data.total_classes > 0:
                    attendance_rate = (attended_classes / data.total_classes) * 100
                
                result.append({
                    'course_id': data.course_id,
                    'course_name': data.course_name,
                    'total_classes': data.total_classes,
                    'attended_classes': attended_classes,
                    'attendance_rate': round(attendance_rate, 2)
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting attendance summary: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    @staticmethod
    def get_assessments(student_id, course_id=None):
        """Get assessments for a student"""
        try:
            # Fixed query with proper joins
            query = db.session.query(
                Assessment.assessment_id,
                Assessment.title,
                Assessment.max_score,
                Assessment.due_date,
                Course.course_name,
                Course.course_code,
                AssessmentSubmission.score
            ).select_from(Assessment).join(
                CourseOffering, Assessment.offering_id == CourseOffering.offering_id
            ).join(
                Course, CourseOffering.course_id == Course.course_id
            ).join(
                Enrollment, Enrollment.offering_id == CourseOffering.offering_id
            ).outerjoin(
                AssessmentSubmission, 
                and_(
                    AssessmentSubmission.assessment_id == Assessment.assessment_id,
                    AssessmentSubmission.enrollment_id == Enrollment.enrollment_id
                )
            ).filter(
                Enrollment.student_id == student_id,
                Enrollment.enrollment_status == 'enrolled'
            )
            
            if course_id:
                query = query.filter(CourseOffering.course_id == course_id)
            
            assessments = query.all()
            
            # Format results
            result = []
            for assessment in assessments:
                result.append({
                    'assessment_id': assessment.assessment_id,
                    'title': assessment.title,
                    'max_score': float(assessment.max_score) if assessment.max_score else 0,
                    'due_date': assessment.due_date.isoformat() if assessment.due_date else None,
                    'course_name': assessment.course_name,
                    'course_code': assessment.course_code,
                    'score': float(assessment.score) if assessment.score else None,
                    'percentage': round((float(assessment.score) / float(assessment.max_score)) * 100, 2) if assessment.score and assessment.max_score else None
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting assessments: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    @staticmethod
    def get_grade_predictions(student_id):
        """Get grade predictions for a student"""
        try:
            predictions = db.session.query(
                Prediction.prediction_id,
                Prediction.predicted_grade,
                Prediction.confidence_score,
                Prediction.prediction_date,
                CourseOffering.course_id,
                Course.course_code,
                Course.course_name
            ).select_from(Prediction).join(
                Enrollment, Enrollment.enrollment_id == Prediction.enrollment_id
            ).join(
                CourseOffering, Enrollment.offering_id == CourseOffering.offering_id
            ).join(
                Course, CourseOffering.course_id == Course.course_id
            ).filter(
                Enrollment.student_id == student_id,
                Enrollment.enrollment_status == 'enrolled'
            ).order_by(
                Prediction.prediction_date.desc()
            ).all()
            
            # Get only the latest prediction for each course
            latest_predictions = {}
            for pred in predictions:
                if pred.course_id not in latest_predictions:
                    latest_predictions[pred.course_id] = {
                        'prediction_id': pred.prediction_id,
                        'course_id': pred.course_id,
                        'course_code': pred.course_code,
                        'course_name': pred.course_name,
                        'predicted_grade': pred.predicted_grade,
                        'confidence_score': float(pred.confidence_score),
                        'prediction_date': pred.prediction_date.isoformat()
                    }
            
            return list(latest_predictions.values())
            
        except Exception as e:
            logger.error(f"Error getting grade predictions: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    @staticmethod
    def get_dashboard_summary(student_id):
        """Get summary data for student dashboard"""
        try:
            # Get current GPA
            gpa = db.session.query(Student.gpa).filter_by(student_id=student_id).scalar() or 0.0
            
            # Get overall attendance rate
            attendance = StudentService.get_attendance_summary(student_id)
            overall_attendance = 0
            if attendance:
                total_attended = sum(a['attended_classes'] for a in attendance)
                total_classes = sum(a['total_classes'] for a in attendance)
                if total_classes > 0:
                    overall_attendance = (total_attended / total_classes) * 100
            
            # FIXED: Get upcoming assessments count with proper joins
            upcoming_assessments = db.session.query(
                func.count(Assessment.assessment_id)
            ).select_from(Assessment).join(
                CourseOffering, Assessment.offering_id == CourseOffering.offering_id
            ).join(
                Enrollment, Enrollment.offering_id == CourseOffering.offering_id
            ).filter(
                Enrollment.student_id == student_id,
                Enrollment.enrollment_status == 'enrolled',
                Assessment.due_date >= datetime.now(),
                Assessment.due_date <= datetime.now() + timedelta(days=7)
            ).scalar() or 0
            
            return {
                'gpa': round(float(gpa), 2),
                'attendance_rate': round(overall_attendance, 2),
                'upcoming_assessments': upcoming_assessments
            }
            
        except Exception as e:
            logger.error(f"Error getting dashboard summary: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'gpa': 0.0,
                'attendance_rate': 0.0,
                'upcoming_assessments': 0
            }


# Create service instance
student_service = StudentService()