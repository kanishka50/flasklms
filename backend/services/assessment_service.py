from backend.models import (
    Assessment, AssessmentType, AssessmentSubmission, Enrollment, 
    Student, CourseOffering, Course
)
from backend.extensions import db
from datetime import datetime, date
from sqlalchemy import func, and_, desc
import logging

logger = logging.getLogger(__name__)

class AssessmentService:
    """Service class for assessment-related operations"""
    
    @staticmethod
    def get_assessment_types():
        """Get all available assessment types"""
        try:
            assessment_types = AssessmentType.query.all()
            return [at.to_dict() for at in assessment_types]
        except Exception as e:
            logger.error(f"Error getting assessment types: {str(e)}")
            return []
    
    @staticmethod
    def create_assessment(offering_id, type_id, title, max_score, due_date=None, weight=None, description=None, created_by=None):
        """Create a new assessment"""
        try:
            # Parse due_date if it's a string
            if isinstance(due_date, str):
                due_date = datetime.strptime(due_date, '%Y-%m-%d %H:%M')
            
            assessment = Assessment(
                offering_id=offering_id,
                type_id=type_id,
                title=title,
                max_score=max_score,
                due_date=due_date,
                weight=weight,
                description=description,
                is_published=True
            )
            
            db.session.add(assessment)
            db.session.commit()
            
            logger.info(f"Assessment created: {title} for offering {offering_id}")
            return assessment
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating assessment: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    def get_assessments_by_offering(offering_id, include_unpublished=False):
        """Get all assessments for a course offering"""
        try:
            query = db.session.query(
                Assessment.assessment_id,
                Assessment.title,
                Assessment.max_score,
                Assessment.due_date,
                Assessment.weight,
                Assessment.description,
                Assessment.is_published,
                Assessment.created_at,
                AssessmentType.type_name,
                AssessmentType.type_id
            ).join(
                AssessmentType, AssessmentType.type_id == Assessment.type_id
            ).filter(
                Assessment.offering_id == offering_id
            )
            
            if not include_unpublished:
                query = query.filter(Assessment.is_published == True)
            
            assessments = query.order_by(Assessment.due_date.asc()).all()
            
            result = []
            for assessment in assessments:
                # Get submission statistics
                total_students = Enrollment.query.filter_by(
                    offering_id=offering_id,
                    enrollment_status='enrolled'
                ).count()
                
                submitted_count = AssessmentSubmission.query.filter_by(
                    assessment_id=assessment.assessment_id
                ).count()
                
                graded_count = AssessmentSubmission.query.filter_by(
                    assessment_id=assessment.assessment_id
                ).filter(
                    AssessmentSubmission.score.isnot(None)
                ).count()
                
                # Calculate average score
                avg_score = db.session.query(
                    func.avg(AssessmentSubmission.score)
                ).filter_by(
                    assessment_id=assessment.assessment_id
                ).filter(
                    AssessmentSubmission.score.isnot(None)
                ).scalar()
                
                result.append({
                    'assessment_id': assessment.assessment_id,
                    'title': assessment.title,
                    'type_name': assessment.type_name,
                    'type_id': assessment.type_id,
                    'max_score': float(assessment.max_score),
                    'due_date': assessment.due_date.isoformat() if assessment.due_date else None,
                    'weight': float(assessment.weight) if assessment.weight else None,
                    'description': assessment.description,
                    'is_published': assessment.is_published,
                    'created_at': assessment.created_at.isoformat() if assessment.created_at else None,
                    'statistics': {
                        'total_students': total_students,
                        'submitted_count': submitted_count,
                        'graded_count': graded_count,
                        'submission_rate': round((submitted_count / total_students * 100) if total_students > 0 else 0, 2),
                        'grading_progress': round((graded_count / total_students * 100) if total_students > 0 else 0, 2),
                        'average_score': round(float(avg_score), 2) if avg_score else None
                    }
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting assessments: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    @staticmethod
    def get_assessment_roster(assessment_id):
        """Get roster of students for grade entry"""
        try:
            # Get the assessment and course info
            assessment = Assessment.query.get(assessment_id)
            if not assessment:
                return None
            
            # Get all enrolled students with their submissions
            students = db.session.query(
                Student.student_id,
                Student.first_name,
                Student.last_name,
                Enrollment.enrollment_id,
                AssessmentSubmission.submission_id,
                AssessmentSubmission.score,
                AssessmentSubmission.percentage,
                AssessmentSubmission.submission_date,
                AssessmentSubmission.is_late,
                AssessmentSubmission.feedback
            ).select_from(Enrollment).join(
                Student, Student.student_id == Enrollment.student_id
            ).outerjoin(
                AssessmentSubmission,
                and_(
                    AssessmentSubmission.enrollment_id == Enrollment.enrollment_id,
                    AssessmentSubmission.assessment_id == assessment_id
                )
            ).filter(
                Enrollment.offering_id == assessment.offering_id,
                Enrollment.enrollment_status == 'enrolled'
            ).order_by(Student.last_name, Student.first_name).all()
            
            # Format results
            roster = []
            for student in students:
                roster.append({
                    'student_id': student.student_id,
                    'enrollment_id': student.enrollment_id,
                    'name': f"{student.first_name} {student.last_name}",
                    'first_name': student.first_name,
                    'last_name': student.last_name,
                    'submission_id': student.submission_id,
                    'score': float(student.score) if student.score else None,
                    'percentage': float(student.percentage) if student.percentage else None,
                    'submission_date': student.submission_date.isoformat() if student.submission_date else None,
                    'is_late': student.is_late,
                    'feedback': student.feedback,
                    'status': 'graded' if student.score is not None else ('submitted' if student.submission_id else 'not_submitted')
                })
            
            return {
                'assessment': {
                    'assessment_id': assessment.assessment_id,
                    'title': assessment.title,
                    'max_score': float(assessment.max_score),
                    'due_date': assessment.due_date.isoformat() if assessment.due_date else None
                },
                'roster': roster
            }
            
        except Exception as e:
            logger.error(f"Error getting assessment roster: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    def enter_grade(enrollment_id, assessment_id, score, feedback=None, graded_by=None):
        """Enter or update a grade for a student"""
        try:
            # Get the assessment to validate score
            assessment = Assessment.query.get(assessment_id)
            if not assessment:
                return None, "Assessment not found"
            
            # Validate score
            if score < 0 or score > float(assessment.max_score):
                return None, f"Score must be between 0 and {assessment.max_score}"
            
            # Check if submission already exists
            existing_submission = AssessmentSubmission.query.filter_by(
                enrollment_id=enrollment_id,
                assessment_id=assessment_id
            ).first()
            
            if existing_submission:
                # Update existing submission
                existing_submission.score = score
                existing_submission.percentage = (score / float(assessment.max_score)) * 100
                existing_submission.feedback = feedback
                existing_submission.graded_date = datetime.utcnow()
                existing_submission.graded_by = graded_by
                submission = existing_submission
            else:
                # Create new submission
                submission = AssessmentSubmission(
                    enrollment_id=enrollment_id,
                    assessment_id=assessment_id,
                    submission_date=datetime.utcnow(),  # Auto-submit when graded
                    score=score,
                    percentage=(score / float(assessment.max_score)) * 100,
                    feedback=feedback,
                    graded_date=datetime.utcnow(),
                    graded_by=graded_by
                )
                db.session.add(submission)
            
            db.session.commit()
            return submission, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error entering grade: {str(e)}")
            import traceback
            traceback.print_exc()
            return None, str(e)
    
    @staticmethod
    def bulk_enter_grades(grades_data, graded_by=None):
        """Enter grades for multiple students"""
        try:
            results = []
            
            for grade_data in grades_data:
                submission, error = AssessmentService.enter_grade(
                    enrollment_id=grade_data['enrollment_id'],
                    assessment_id=grade_data['assessment_id'],
                    score=grade_data['score'],
                    feedback=grade_data.get('feedback'),
                    graded_by=graded_by
                )
                
                if submission:
                    results.append({
                        'enrollment_id': grade_data['enrollment_id'],
                        'success': True,
                        'submission_id': submission.submission_id
                    })
                else:
                    results.append({
                        'enrollment_id': grade_data['enrollment_id'],
                        'success': False,
                        'error': error
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Error in bulk grade entry: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    @staticmethod
    def get_student_assessments(student_id, offering_id=None):
        """Get all assessments for a student"""
        try:
            query = db.session.query(
                Assessment.assessment_id,
                Assessment.title,
                Assessment.max_score,
                Assessment.due_date,
                Assessment.weight,
                Assessment.description,
                AssessmentType.type_name,
                Course.course_code,
                Course.course_name,
                AssessmentSubmission.score,
                AssessmentSubmission.percentage,
                AssessmentSubmission.submission_date,
                AssessmentSubmission.feedback,
                AssessmentSubmission.is_late
            ).select_from(Assessment).join(
                CourseOffering, CourseOffering.offering_id == Assessment.offering_id
            ).join(
                Course, Course.course_id == CourseOffering.course_id
            ).join(
                AssessmentType, AssessmentType.type_id == Assessment.type_id
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
                Enrollment.enrollment_status == 'enrolled',
                Assessment.is_published == True
            )
            
            if offering_id:
                query = query.filter(Assessment.offering_id == offering_id)
            
            assessments = query.order_by(Assessment.due_date.desc()).all()
            
            result = []
            for assessment in assessments:
                result.append({
                    'assessment_id': assessment.assessment_id,
                    'title': assessment.title,
                    'type_name': assessment.type_name,
                    'course_code': assessment.course_code,
                    'course_name': assessment.course_name,
                    'max_score': float(assessment.max_score),
                    'due_date': assessment.due_date.isoformat() if assessment.due_date else None,
                    'weight': float(assessment.weight) if assessment.weight else None,
                    'description': assessment.description,
                    'score': float(assessment.score) if assessment.score else None,
                    'percentage': float(assessment.percentage) if assessment.percentage else None,
                    'submission_date': assessment.submission_date.isoformat() if assessment.submission_date else None,
                    'feedback': assessment.feedback,
                    'is_late': assessment.is_late,
                    'status': 'graded' if assessment.score is not None else 'pending'
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting student assessments: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    @staticmethod
    def get_assessment_statistics(assessment_id):
        """Get detailed statistics for an assessment"""
        try:
            assessment = Assessment.query.get(assessment_id)
            if not assessment:
                return None
            
            # Get all submissions with scores
            submissions = AssessmentSubmission.query.filter_by(
                assessment_id=assessment_id
            ).filter(
                AssessmentSubmission.score.isnot(None)
            ).all()
            
            if not submissions:
                return {
                    'assessment_id': assessment_id,
                    'title': assessment.title,
                    'total_submissions': 0,
                    'statistics': None
                }
            
            scores = [float(s.score) for s in submissions]
            max_score = float(assessment.max_score)
            
            # Calculate statistics
            stats = {
                'total_submissions': len(scores),
                'average_score': round(sum(scores) / len(scores), 2),
                'average_percentage': round((sum(scores) / len(scores)) / max_score * 100, 2),
                'highest_score': max(scores),
                'lowest_score': min(scores),
                'median_score': round(sorted(scores)[len(scores) // 2], 2),
                'grade_distribution': {}
            }
            
            # Calculate grade distribution
            for score in scores:
                percentage = (score / max_score) * 100
                if percentage >= 90:
                    grade = 'A'
                elif percentage >= 80:
                    grade = 'B'
                elif percentage >= 70:
                    grade = 'C'
                elif percentage >= 60:
                    grade = 'D'
                else:
                    grade = 'F'
                
                stats['grade_distribution'][grade] = stats['grade_distribution'].get(grade, 0) + 1
            
            return {
                'assessment_id': assessment_id,
                'title': assessment.title,
                'max_score': max_score,
                'statistics': stats
            }
            
        except Exception as e:
            logger.error(f"Error getting assessment statistics: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    def delete_assessment(assessment_id):
        """Delete an assessment (if no submissions exist)"""
        try:
            assessment = Assessment.query.get(assessment_id)
            if not assessment:
                return False, "Assessment not found"
            
            # Check if there are any submissions
            submission_count = AssessmentSubmission.query.filter_by(
                assessment_id=assessment_id
            ).count()
            
            if submission_count > 0:
                return False, "Cannot delete assessment with existing submissions"
            
            db.session.delete(assessment)
            db.session.commit()
            return True, "Assessment deleted successfully"
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting assessment: {str(e)}")
            return False, str(e)

# Create service instance
assessment_service = AssessmentService()