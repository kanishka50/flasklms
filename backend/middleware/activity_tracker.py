from functools import wraps
from flask import request, g
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request_optional
from backend.models import LMSSession, LMSActivity, User, Enrollment
from backend.extensions import db
from datetime import datetime
import logging

logger = logging.getLogger('activity_tracker')

class ActivityTracker:
    """Middleware to track user activities in the LMS"""
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize the activity tracker with the Flask app"""
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        logger.info("Activity tracker initialized")
    
    def before_request(self):
        """Called before each request"""
        # Track request start time
        g.request_start_time = datetime.now()
        
        # Try to get current user
        try:
            verify_jwt_in_request_optional()
            user_id = get_jwt_identity()
            
            if user_id:
                user = User.query.get(user_id)
                if user:
                    g.current_user = user
                    
                    # Get or create session for student
                    if user.user_type == 'student' and user.student:
                        self._ensure_session(user.student.student_id)
        except:
            # No valid JWT or other error
            pass
    
    def after_request(self, response):
        """Called after each request"""
        # Only track for authenticated students
        if hasattr(g, 'current_user') and g.current_user and g.current_user.user_type == 'student':
            # Skip tracking for API calls that shouldn't be tracked
            if not self._should_track_request():
                return response
            
            try:
                # Track the activity
                self._track_activity()
            except Exception as e:
                logger.error(f"Error tracking activity: {str(e)}")
        
        return response
    
    def _should_track_request(self):
        """Determine if this request should be tracked"""
        # Don't track auth endpoints
        if request.path.startswith('/api/auth'):
            return False
        
        # Don't track static files
        if request.path.startswith('/static'):
            return False
        
        # Don't track prediction generation
        if '/predictions/generate' in request.path:
            return False
        
        # Track these specific paths
        tracked_paths = [
            '/student/',  # Student pages
            '/api/student/courses',  # Course views
            '/api/student/assessments',  # Assessment views
            '/api/student/resources',  # Resource access
        ]
        
        return any(request.path.startswith(path) for path in tracked_paths)
    
    def _ensure_session(self, student_id):
        """Ensure there's an active session for the student"""
        # Check for active session in last 30 minutes
        last_session = LMSSession.query.filter(
            LMSSession.student_id == student_id,
            LMSSession.logout_time.is_(None)
        ).order_by(LMSSession.login_time.desc()).first()
        
        now = datetime.now()
        
        # Create new session if needed
        if not last_session or (now - last_session.login_time).seconds > 1800:  # 30 minutes
            # Close old session if exists
            if last_session:
                last_session.logout_time = now
                db.session.commit()
            
            # Create new session for each active enrollment
            enrollments = Enrollment.query.filter(
                Enrollment.student_id == student_id,
                Enrollment.enrollment_status == 'enrolled'
            ).all()
            
            for enrollment in enrollments:
                session = LMSSession(
                    enrollment_id=enrollment.enrollment_id,
                    login_time=now,
                    ip_address=request.remote_addr or 'unknown'
                )
                db.session.add(session)
            
            db.session.commit()
            
            # Store session IDs in g
            g.lms_sessions = {e.enrollment_id: session.session_id for e, session in 
                            zip(enrollments, LMSSession.query.filter(
                                LMSSession.enrollment_id.in_([e.enrollment_id for e in enrollments]),
                                LMSSession.logout_time.is_(None)
                            ).all())}
        else:
            # Get all active sessions for this student
            active_sessions = LMSSession.query.join(
                Enrollment, LMSSession.enrollment_id == Enrollment.enrollment_id
            ).filter(
                Enrollment.student_id == student_id,
                LMSSession.logout_time.is_(None)
            ).all()
            
            g.lms_sessions = {s.enrollment_id: s.session_id for s in active_sessions}
    
    def _track_activity(self):
        """Track the current activity"""
        if not hasattr(g, 'lms_sessions') or not g.lms_sessions:
            return
        
        # Determine activity type based on request
        activity_type = self._determine_activity_type()
        if not activity_type:
            return
        
        # Get resource ID if applicable
        resource_id = self._extract_resource_id()
        
        # Calculate duration
        duration = None
        if hasattr(g, 'request_start_time'):
            duration = (datetime.now() - g.request_start_time).seconds
        
        # Create activity for each active session
        for enrollment_id, session_id in g.lms_sessions.items():
            # Check if this activity is relevant to this enrollment
            if self._is_activity_relevant(enrollment_id):
                activity = LMSActivity(
                    session_id=session_id,
                    activity_type=activity_type,
                    resource_id=resource_id,
                    activity_timestamp=datetime.now(),
                    duration_seconds=duration
                )
                db.session.add(activity)
        
        try:
            db.session.commit()
            logger.debug(f"Tracked activity: {activity_type} for user {g.current_user.username}")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error saving activity: {str(e)}")
    
    def _determine_activity_type(self):
        """Determine the type of activity based on the request"""
        path = request.path.lower()
        method = request.method
        
        # Page views
        if method == 'GET':
            if 'dashboard' in path:
                return 'dashboard_view'
            elif 'course' in path:
                return 'course_view'
            elif 'assessment' in path or 'assignment' in path:
                return 'assignment_view'
            elif 'grade' in path:
                return 'grade_view'
            elif 'resource' in path:
                return 'resource_view'
            elif 'forum' in path:
                return 'forum_view'
            else:
                return 'page_view'
        
        # Actions
        elif method == 'POST':
            if 'forum' in path:
                return 'forum_post'
            elif 'submit' in path:
                return 'assignment_submit'
            elif 'download' in path:
                return 'file_download'
        
        return None
    
    def _extract_resource_id(self):
        """Extract resource ID from the request"""
        # Try to get ID from path
        path_parts = request.path.split('/')
        for i, part in enumerate(path_parts):
            if part.isdigit() and i > 0:
                # Previous part might indicate resource type
                return f"{path_parts[i-1]}_{part}"
        
        # Try to get from query parameters
        if 'id' in request.args:
            return str(request.args.get('id'))
        
        return request.path
    
    def _is_activity_relevant(self, enrollment_id):
        """Check if this activity is relevant to the enrollment"""
        # For now, track all activities for all enrollments
        # In the future, you might want to filter by course
        return True

# Function to track specific actions
def track_action(activity_type, resource_id=None, enrollment_id=None):
    """Manually track a specific action"""
    try:
        if hasattr(g, 'current_user') and g.current_user.user_type == 'student':
            if enrollment_id and hasattr(g, 'lms_sessions'):
                session_id = g.lms_sessions.get(enrollment_id)
                if session_id:
                    activity = LMSActivity(
                        session_id=session_id,
                        activity_type=activity_type,
                        resource_id=resource_id,
                        activity_timestamp=datetime.now()
                    )
                    db.session.add(activity)
                    db.session.commit()
    except Exception as e:
        logger.error(f"Error tracking action: {str(e)}")