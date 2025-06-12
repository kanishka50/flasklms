from backend.models import (
    Attendance, Enrollment, Student, CourseOffering, Course
)
from backend.extensions import db
from datetime import datetime, date, timedelta
from sqlalchemy import func, case, desc, and_
import logging

logger = logging.getLogger(__name__)

class AttendanceService:
    """Service class for attendance-related operations"""
    
    @staticmethod
    def get_course_roster(offering_id, attendance_date=None):
        """Get roster of students for a course with attendance status"""
        try:
            if attendance_date is None:
                attendance_date = date.today()
            
            # Get all enrolled students for this course offering
            students = db.session.query(
                Student.student_id,
                Student.first_name,
                Student.last_name,
                Enrollment.enrollment_id,
                Attendance.status.label('attendance_status'),
                Attendance.attendance_id,
                Attendance.check_in_time,
                Attendance.notes
            ).select_from(Enrollment).join(
                Student, Student.student_id == Enrollment.student_id
            ).outerjoin(
                Attendance, 
                and_(
                    Attendance.enrollment_id == Enrollment.enrollment_id,
                    Attendance.attendance_date == attendance_date
                )
            ).filter(
                Enrollment.offering_id == offering_id,
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
                    'attendance_id': student.attendance_id,
                    'status': student.attendance_status or 'not_marked',
                    'check_in_time': student.check_in_time.strftime('%H:%M') if student.check_in_time else None,
                    'notes': student.notes
                })
            
            return roster
            
        except Exception as e:
            logger.error(f"Error getting course roster: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    @staticmethod
    def mark_attendance(enrollment_id, attendance_date, status, check_in_time=None, notes=None, recorded_by=None):
        """Mark or update attendance for a student"""
        try:
            # Check if attendance already exists
            existing_attendance = Attendance.query.filter_by(
                enrollment_id=enrollment_id,
                attendance_date=attendance_date
            ).first()
            
            if existing_attendance:
                # Update existing record
                existing_attendance.status = status
                existing_attendance.check_in_time = check_in_time
                existing_attendance.notes = notes
                existing_attendance.recorded_by = recorded_by
                attendance_record = existing_attendance
            else:
                # Create new record
                attendance_record = Attendance(
                    enrollment_id=enrollment_id,
                    attendance_date=attendance_date,
                    status=status,
                    check_in_time=check_in_time,
                    notes=notes,
                    recorded_by=recorded_by
                )
                db.session.add(attendance_record)
            
            db.session.commit()
            return attendance_record
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error marking attendance: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    def bulk_mark_attendance(attendance_data, recorded_by=None):
        """Mark attendance for multiple students"""
        try:
            results = []
            
            for data in attendance_data:
                result = AttendanceService.mark_attendance(
                    enrollment_id=data['enrollment_id'],
                    attendance_date=data['attendance_date'],
                    status=data['status'],
                    check_in_time=data.get('check_in_time'),
                    notes=data.get('notes'),
                    recorded_by=recorded_by
                )
                
                if result:
                    results.append({
                        'enrollment_id': data['enrollment_id'],
                        'success': True,
                        'attendance_id': result.attendance_id
                    })
                else:
                    results.append({
                        'enrollment_id': data['enrollment_id'],
                        'success': False,
                        'error': 'Failed to save attendance'
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Error in bulk attendance marking: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    @staticmethod
    def get_attendance_summary(offering_id, start_date=None, end_date=None):
        """Get attendance summary for a course offering"""
        try:
            # Default date range (last 30 days)
            if not start_date:
                start_date = date.today() - timedelta(days=30)
            if not end_date:
                end_date = date.today()
            
            # Get attendance records
            attendance_summary = db.session.query(
                Student.student_id,
                Student.first_name,
                Student.last_name,
                func.count(Attendance.attendance_id).label('total_records'),
                func.sum(case([(Attendance.status.in_(['present', 'late']), 1)], else_=0)).label('present_count'),
                func.sum(case([(Attendance.status == 'absent', 1)], else_=0)).label('absent_count'),
                func.sum(case([(Attendance.status == 'late', 1)], else_=0)).label('late_count'),
                func.sum(case([(Attendance.status == 'excused', 1)], else_=0)).label('excused_count')
            ).select_from(Enrollment).join(
                Student, Student.student_id == Enrollment.student_id
            ).outerjoin(
                Attendance, Attendance.enrollment_id == Enrollment.enrollment_id
            ).filter(
                Enrollment.offering_id == offering_id,
                Enrollment.enrollment_status == 'enrolled'
            ).group_by(
                Student.student_id, Student.first_name, Student.last_name
            ).all()
            
            # Format results
            summary = []
            for record in attendance_summary:
                total = record.total_records or 0
                present = record.present_count or 0
                attendance_rate = (present / total * 100) if total > 0 else 0
                
                summary.append({
                    'student_id': record.student_id,
                    'name': f"{record.first_name} {record.last_name}",
                    'total_classes': total,
                    'present_count': present,
                    'absent_count': record.absent_count or 0,
                    'late_count': record.late_count or 0,
                    'excused_count': record.excused_count or 0,
                    'attendance_rate': round(attendance_rate, 2)
                })
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting attendance summary: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    @staticmethod
    def get_course_attendance_dates(offering_id, limit=30):
        """Get list of dates when attendance was taken for a course"""
        try:
            dates = db.session.query(
                Attendance.attendance_date
            ).join(
                Enrollment, Enrollment.enrollment_id == Attendance.enrollment_id
            ).filter(
                Enrollment.offering_id == offering_id
            ).distinct().order_by(
                desc(Attendance.attendance_date)
            ).limit(limit).all()
            
            return [d.attendance_date for d in dates]
            
        except Exception as e:
            logger.error(f"Error getting attendance dates: {str(e)}")
            return []
    
    @staticmethod
    def delete_attendance(attendance_id):
        """Delete an attendance record"""
        try:
            attendance = Attendance.query.get(attendance_id)
            if attendance:
                db.session.delete(attendance)
                db.session.commit()
                return True
            return False
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting attendance: {str(e)}")
            return False

# Create service instance
attendance_service = AttendanceService()