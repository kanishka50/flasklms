from backend.models import (
    Faculty, Course, CourseOffering, Enrollment, Student, 
    Assessment, Attendance, Prediction, AssessmentSubmission,
    AssessmentType  
)
from backend.extensions import db
from sqlalchemy import func, and_, or_, desc
from datetime import datetime, timedelta
import logging
from sqlalchemy import distinct  


logger = logging.getLogger(__name__)

class FacultyService:
    """Service class for faculty-related operations"""
    
    @staticmethod
    def get_faculty_by_user_id(user_id):
        """Get faculty record by user ID"""
        try:
            faculty = Faculty.query.filter_by(user_id=user_id).first()
            return faculty
        except Exception as e:
            logger.error(f"Error getting faculty: {str(e)}")
            return None
    
    @staticmethod
    def get_teaching_courses(faculty_id, term_id=None):
        """Get all courses taught by a faculty member"""
        try:
            query = db.session.query(
                CourseOffering.offering_id,
                Course.course_id,
                Course.course_code,
                Course.course_name,
                Course.credits,
                CourseOffering.section_number,
                CourseOffering.capacity,
                CourseOffering.enrolled_count,
                CourseOffering.meeting_pattern,
                CourseOffering.location
            ).join(
                Course, Course.course_id == CourseOffering.course_id
            ).filter(
                CourseOffering.faculty_id == faculty_id
            )
            
            # Filter by term if provided
            if term_id:
                query = query.filter(CourseOffering.term_id == term_id)
            
            courses = query.all()
            
            # Convert to dictionary and add student count
            result = []
            for course in courses:
                # Get actual enrolled student count
                student_count = Enrollment.query.filter_by(
                    offering_id=course.offering_id,
                    enrollment_status='enrolled'
                ).count()
                
                result.append({
                    'offering_id': course.offering_id,
                    'course_id': course.course_id,
                    'course_code': course.course_code,
                    'course_name': course.course_name,
                    'credits': course.credits,
                    'section': course.section_number,
                    'capacity': course.capacity,
                    'enrolled_count': course.enrolled_count,
                    'student_count': student_count,
                    'meeting_pattern': course.meeting_pattern,
                    'location': course.location
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting teaching courses: {str(e)}")
            return []
    
    @staticmethod
    def get_students_by_course(offering_id):
        """Get all students enrolled in a course offering"""
        try:
            students = db.session.query(
                Student.student_id,
                Student.first_name,
                Student.last_name,
                Student.email,
                Student.program_code,
                Student.year_of_study,
                Enrollment.enrollment_id,
                Enrollment.final_grade
            ).join(
                Enrollment, Enrollment.student_id == Student.student_id
            ).filter(
                Enrollment.offering_id == offering_id,
                Enrollment.enrollment_status == 'enrolled'
            ).all()
            
            result = []
            for student in students:
                # Get attendance rate
                attendance_rate = FacultyService._calculate_student_attendance_rate(
                    student.enrollment_id
                )
                
                # Get latest prediction
                latest_prediction = Prediction.query.filter_by(
                    enrollment_id=student.enrollment_id
                ).order_by(desc(Prediction.prediction_date)).first()
                
                result.append({
                    'student_id': student.student_id,
                    'name': f"{student.first_name} {student.last_name}",
                    'email': student.email,
                    'program_code': student.program_code,
                    'year_of_study': student.year_of_study,
                    'enrollment_id': student.enrollment_id,
                    'attendance_rate': attendance_rate,
                    'current_grade': student.final_grade,
                    'predicted_grade': latest_prediction.predicted_grade if latest_prediction else None,
                    'risk_level': latest_prediction.risk_level if latest_prediction else None
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting students by course: {str(e)}")
            return []
    
    @staticmethod
    def get_at_risk_students(faculty_id):
        """Get all at-risk students in faculty's courses"""
        try:
            # Get all offerings taught by this faculty
            offerings = CourseOffering.query.filter_by(faculty_id=faculty_id).all()
            offering_ids = [o.offering_id for o in offerings]
            
            # Get at-risk students (predicted grade D or F, or high risk level)
            at_risk_enrollments = db.session.query(
                Enrollment.enrollment_id,
                Student.student_id,
                Student.first_name,
                Student.last_name,
                Course.course_id,
                Course.course_code,
                Course.course_name,
                Prediction.predicted_grade,
                Prediction.confidence_score,
                Prediction.risk_level
            ).join(
                Student, Student.student_id == Enrollment.student_id
            ).join(
                CourseOffering, CourseOffering.offering_id == Enrollment.offering_id
            ).join(
                Course, Course.course_id == CourseOffering.course_id
            ).join(
                Prediction, Prediction.enrollment_id == Enrollment.enrollment_id
            ).filter(
                CourseOffering.offering_id.in_(offering_ids),
                Enrollment.enrollment_status == 'enrolled',
                or_(
                    Prediction.predicted_grade.in_(['D', 'F']),
                    Prediction.risk_level.in_(['medium', 'high'])
                )
            ).distinct().all()
            
            result = []
            for enrollment in at_risk_enrollments:
                # Get risk factors
                risk_factors = FacultyService._identify_risk_factors(enrollment.enrollment_id)
                
                result.append({
                    'student_id': enrollment.student_id,
                    'name': f"{enrollment.first_name} {enrollment.last_name}",
                    'course_id': enrollment.course_id,
                    'course_code': enrollment.course_code,
                    'course_name': enrollment.course_name,
                    'predicted_grade': enrollment.predicted_grade,
                    'confidence_score': float(enrollment.confidence_score),
                    'risk_level': enrollment.risk_level,
                    'risk_factors': risk_factors
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting at-risk students: {str(e)}")
            return []
    
    @staticmethod
    def get_recent_assessments(faculty_id):
        """Get recent assessments for faculty's courses"""
        try:
            # Get assessments from last 30 days or upcoming
            cutoff_date = datetime.now() - timedelta(days=30)
            
            assessments = db.session.query(
                Assessment.assessment_id,
                Assessment.title,
                Assessment.max_score,
                Assessment.due_date,
                Assessment.weight,
                Course.course_id,
                Course.course_code,
                Course.course_name,
                CourseOffering.offering_id,
                AssessmentType.type_name  # ✅ FIXED: Get type name from AssessmentType
            ).join(
                CourseOffering, CourseOffering.offering_id == Assessment.offering_id
            ).join(
                Course, Course.course_id == CourseOffering.course_id
            ).join(
                AssessmentType, AssessmentType.type_id == Assessment.type_id  # ✅ FIXED: Join with AssessmentType
            ).filter(
                CourseOffering.faculty_id == faculty_id,
                or_(
                    Assessment.due_date >= cutoff_date,
                    Assessment.due_date >= datetime.now()
                )
            ).order_by(desc(Assessment.due_date)).all()
            
            result = []
            for assessment in assessments:
                # Get submission statistics
                total_students = Enrollment.query.filter_by(
                    offering_id=assessment.offering_id,
                    enrollment_status='enrolled'
                ).count()
                
                submissions = db.session.query(
                    func.count(AssessmentSubmission.submission_id)
                ).filter_by(
                    assessment_id=assessment.assessment_id
                ).scalar() or 0
                
                result.append({
                    'assessment_id': assessment.assessment_id,
                    'title': assessment.title,
                    'type': assessment.type_name,  # ✅ FIXED: Use type_name from join
                    'max_score': float(assessment.max_score),
                    'due_date': assessment.due_date.isoformat() if assessment.due_date else None,
                    'weight': float(assessment.weight) if assessment.weight else None,
                    'course_id': assessment.course_id,
                    'course_code': assessment.course_code,
                    'course_name': assessment.course_name,
                    'total_students': total_students,
                    'submission_count': submissions,
                    'submission_rate': round((submissions / total_students * 100) if total_students > 0 else 0, 2)
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting recent assessments: {str(e)}")
            # ✅ ADDED: Print the actual error for debugging
            import traceback
            traceback.print_exc()
            return []
    
    @staticmethod
    def get_dashboard_summary(faculty_id):
        """Get summary data for faculty dashboard"""
        try:
            # Get course count
            course_count = CourseOffering.query.filter_by(
                faculty_id=faculty_id
            ).count()
            
            # Get total student count
            offerings = CourseOffering.query.filter_by(faculty_id=faculty_id).all()
            offering_ids = [o.offering_id for o in offerings]
            
            student_count = Enrollment.query.filter(
                Enrollment.offering_id.in_(offering_ids),
                Enrollment.enrollment_status == 'enrolled'
            ).count()
            
            # Get at-risk student count
            at_risk_count = db.session.query(
                func.count(distinct(Enrollment.student_id))
            ).join(
                Prediction, Prediction.enrollment_id == Enrollment.enrollment_id
            ).filter(
                Enrollment.offering_id.in_(offering_ids),
                Enrollment.enrollment_status == 'enrolled',
                or_(
                    Prediction.predicted_grade.in_(['D', 'F']),
                    Prediction.risk_level.in_(['medium', 'high'])
                )
            ).scalar() or 0
            
            return {
                'course_count': course_count,
                'student_count': student_count,
                'at_risk_count': at_risk_count
            }
            
        except Exception as e:
            logger.error(f"Error getting dashboard summary: {str(e)}")
            return {
                'course_count': 0,
                'student_count': 0,
                'at_risk_count': 0
            }
    
    @staticmethod
    def _calculate_student_attendance_rate(enrollment_id):
        """Calculate attendance rate for a student enrollment"""
        try:
            total_classes = Attendance.query.filter_by(
                enrollment_id=enrollment_id
            ).count()
            
            attended_classes = Attendance.query.filter_by(
                enrollment_id=enrollment_id
            ).filter(
                Attendance.status.in_(['present', 'late'])
            ).count()
            
            if total_classes > 0:
                return round((attended_classes / total_classes) * 100, 2)
            return 0.0
            
        except Exception as e:
            logger.error(f"Error calculating attendance rate: {str(e)}")
            return 0.0
    
    @staticmethod
    def _identify_risk_factors(enrollment_id):
        """Identify risk factors for a student enrollment"""
        risk_factors = []
        
        try:
            # Check attendance
            attendance_rate = FacultyService._calculate_student_attendance_rate(enrollment_id)
            if attendance_rate < 70:
                risk_factors.append(f"Low attendance ({attendance_rate}%)")
            
            # Check missing assignments
            # This would need the AssessmentSubmission model
            # For now, we'll add a placeholder
            risk_factors.append("Assignment submission issues")
            
            # Check recent quiz/test scores
            # Add more checks as needed
            
            return risk_factors
            
        except Exception as e:
            logger.error(f"Error identifying risk factors: {str(e)}")
            return ["Unable to determine risk factors"]


# Create service instance
faculty_service = FacultyService()