from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.services.attendance_service import attendance_service
from backend.services.auth_service import get_user_by_id
from backend.middleware.auth_middleware import faculty_required
from backend.utils.api import api_response, error_response
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)

attendance_bp = Blueprint('attendance', __name__)

@attendance_bp.route('/roster/<int:offering_id>', methods=['GET'])
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
        
        # TODO: Verify faculty teaches this course (security check)
        
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

@attendance_bp.route('/mark', methods=['POST'])
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

@attendance_bp.route('/bulk-mark', methods=['POST'])
@jwt_required()
@faculty_required
def bulk_mark_attendance():
    """Mark attendance for multiple students"""
    try:
        data = request.get_json()
        
        if 'attendance_records' not in data:
            return error_response('Missing attendance_records field', 400)
        
        attendance_data = data['attendance_records']
        
        # Validate each record
        for record in attendance_data:
            required_fields = ['enrollment_id', 'attendance_date', 'status']
            for field in required_fields:
                if field not in record:
                    return error_response(f'Missing required field: {field} in attendance record', 400)
        
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
            
            # Parse check-in time if provided
            check_in_time = None
            if record.get('check_in_time'):
                try:
                    check_in_time = datetime.strptime(record['check_in_time'], '%H:%M').time()
                except ValueError:
                    return error_response('Invalid time format in record. Use HH:MM', 400)
            
            processed_data.append({
                'enrollment_id': record['enrollment_id'],
                'attendance_date': attendance_date,
                'status': record['status'],
                'check_in_time': check_in_time,
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

@attendance_bp.route('/summary/<int:offering_id>', methods=['GET'])
@jwt_required()
@faculty_required
def get_attendance_summary(offering_id):
    """Get attendance summary for a course"""
    try:
        # Get date range from query params
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        start_date = None
        end_date = None
        
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            except ValueError:
                return error_response('Invalid start_date format. Use YYYY-MM-DD', 400)
        
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except ValueError:
                return error_response('Invalid end_date format. Use YYYY-MM-DD', 400)
        
        # Get summary
        summary = attendance_service.get_attendance_summary(offering_id, start_date, end_date)
        
        return api_response({
            'summary': summary,
            'offering_id': offering_id,
            'date_range': {
                'start_date': start_date.isoformat() if start_date else None,
                'end_date': end_date.isoformat() if end_date else None
            }
        }, 'Attendance summary retrieved successfully')
        
    except Exception as e:
        logger.error(f"Error getting attendance summary: {str(e)}")
        return error_response('Failed to get attendance summary', 500)

@attendance_bp.route('/dates/<int:offering_id>', methods=['GET'])
@jwt_required()
@faculty_required
def get_attendance_dates(offering_id):
    """Get list of dates when attendance was taken"""
    try:
        dates = attendance_service.get_course_attendance_dates(offering_id)
        
        return api_response({
            'dates': [d.isoformat() for d in dates],
            'offering_id': offering_id
        }, 'Attendance dates retrieved successfully')
        
    except Exception as e:
        logger.error(f"Error getting attendance dates: {str(e)}")
        return error_response('Failed to get attendance dates', 500)

@attendance_bp.route('/<int:attendance_id>', methods=['DELETE'])
@jwt_required()
@faculty_required
def delete_attendance(attendance_id):
    """Delete an attendance record"""
    try:
        # TODO: Add security check to ensure faculty can delete this record
        
        success = attendance_service.delete_attendance(attendance_id)
        
        if success:
            return api_response(message='Attendance record deleted successfully')
        else:
            return error_response('Attendance record not found', 404)
        
    except Exception as e:
        logger.error(f"Error deleting attendance: {str(e)}")
        return error_response('Failed to delete attendance record', 500)