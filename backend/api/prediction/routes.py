from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from backend.models import Enrollment, Student, Faculty, CourseOffering
from backend.services.prediction_service import PredictionService
from backend.services.model_service import ModelService
from backend.utils.api import api_response, error_response
from backend.utils.decorators import role_required
from backend.extensions import db
import logging

logger = logging.getLogger(__name__)

prediction_bp = Blueprint('prediction', __name__)

# Initialize services
prediction_service = PredictionService()
model_service = ModelService()

@prediction_bp.route('/health', methods=['GET'])
def health_check():
    """Check if prediction system is healthy"""
    try:
        model_info = model_service.get_model_info()
        return api_response({
            'status': 'healthy',
            'model': model_info
        }, message="Prediction system is operational")
    except Exception as e:
        return error_response(f"Prediction system error: {str(e)}", 503)

@prediction_bp.route('/model/info', methods=['GET'])
@jwt_required()
def get_model_info():
    """Get information about the loaded model"""
    try:
        model_info = model_service.get_model_info()
        feature_importance = model_service.get_feature_importance()
        
        return api_response({
            'model_info': model_info,
            'features': {
                'count': len(model_service.get_feature_list()),
                'names': model_service.get_feature_list(),
                'importance': feature_importance
            }
        })
    except Exception as e:
        return error_response(f"Error getting model info: {str(e)}")

@prediction_bp.route('/student/<string:enrollment_id>/generate', methods=['POST'])
@jwt_required()
def generate_student_prediction(enrollment_id):
    """Generate a new prediction for a student enrollment"""
    try:
        # Verify access rights
        user_id = get_jwt_identity()
        enrollment = Enrollment.query.get(enrollment_id)
        
        if not enrollment:
            return error_response("Enrollment not found", 404)
        
        # Check if user has access (student can view own, faculty can view their students)
        if not _has_access_to_enrollment(user_id, enrollment):
            return error_response("Access denied", 403)
        
        # Generate prediction
        prediction = prediction_service.generate_prediction(int(enrollment_id))
        
        return api_response({
            'prediction': prediction,
            'student': {
                'id': enrollment.student_id,
                'name': f"{enrollment.student.first_name} {enrollment.student.last_name}"
            }
        }, message="Prediction generated successfully")
        
    except Exception as e:
        logger.error(f"Error generating prediction: {str(e)}")
        return error_response(f"Error generating prediction: {str(e)}")

@prediction_bp.route('/student/<string:enrollment_id>', methods=['GET'])
@jwt_required()
def get_student_predictions(enrollment_id):
    """Get prediction history for a student enrollment"""
    try:
        # Verify access rights
        user_id = get_jwt_identity()
        enrollment = Enrollment.query.get(enrollment_id)
        
        if not enrollment:
            return error_response("Enrollment not found", 404)
        
        if not _has_access_to_enrollment(user_id, enrollment):
            return error_response("Access denied", 403)
        
        # Get prediction history
        limit = request.args.get('limit', 10, type=int)
        predictions = prediction_service.get_prediction_history(int(enrollment_id), limit)
        
        # Get latest prediction with explanation
        latest = prediction_service.get_latest_prediction(int(enrollment_id))
        
        return api_response({
            'enrollment_id': enrollment_id,
            'student': {
                'id': enrollment.student_id,
                'name': f"{enrollment.student.first_name} {enrollment.student.last_name}"
            },
            'latest_prediction': latest,
            'history': predictions,
            'count': len(predictions)
        })
        
    except Exception as e:
        return error_response(f"Error retrieving predictions: {str(e)}")

@prediction_bp.route('/course/<int:offering_id>/generate', methods=['POST'])
@jwt_required()
@role_required(['faculty', 'admin'])
def generate_course_predictions(offering_id):
    """Generate predictions for all students in a course (faculty/admin only)"""
    try:
        # Verify course exists and user has access
        offering = CourseOffering.query.get(offering_id)
        if not offering:
            return error_response("Course offering not found", 404)
        
        user_id = get_jwt_identity()
        # Check if faculty teaches this course
        if not _has_access_to_course(user_id, offering):
            return error_response("Access denied to this course", 403)
        
        # Generate batch predictions
        results = prediction_service.batch_generate_predictions(offering_id)
        
        # Summary statistics
        success_count = sum(1 for r in results if r['status'] == 'success')
        at_risk_count = sum(
            1 for r in results 
            if r['status'] == 'success' and 
            r['prediction']['risk_level'] in ['medium', 'high']
        )
        
        return api_response({
            'offering_id': offering_id,
            'course': {
                'code': offering.course.course_code,
                'name': offering.course.course_name
            },
            'summary': {
                'total_students': len(results),
                'predictions_generated': success_count,
                'at_risk_students': at_risk_count,
                'errors': len(results) - success_count
            },
            'results': results
        }, message="Batch predictions completed")
        
    except Exception as e:
        logger.error(f"Error in batch prediction: {str(e)}")
        return error_response(f"Error generating predictions: {str(e)}")

@prediction_bp.route('/course/<int:offering_id>', methods=['GET'])
@jwt_required()
def get_course_predictions(offering_id):
    """Get all predictions for students in a course"""
    try:
        # Verify access
        offering = CourseOffering.query.get(offering_id)
        if not offering:
            return error_response("Course offering not found", 404)
        
        user_id = get_jwt_identity()
        if not _has_access_to_course(user_id, offering):
            return error_response("Access denied", 403)
        
        # Get enrollments with latest predictions
        enrollments = Enrollment.query.filter_by(
            offering_id=offering_id,
            enrollment_status='enrolled'
        ).all()
        
        predictions = []
        for enrollment in enrollments:
            latest_pred = prediction_service.get_latest_prediction(enrollment.enrollment_id)
            if latest_pred:
                predictions.append({
                    'student': {
                        'id': enrollment.student_id,
                        'name': f"{enrollment.student.first_name} {enrollment.student.last_name}"
                    },
                    'enrollment_id': enrollment.enrollment_id,
                    'prediction': latest_pred
                })
        
        # Sort by risk level (high risk first)
        risk_order = {'high': 0, 'medium': 1, 'low': 2}
        predictions.sort(
            key=lambda x: risk_order.get(x['prediction']['risk_level'], 3)
        )
        
        return api_response({
            'offering_id': offering_id,
            'course': {
                'code': offering.course.course_code,
                'name': offering.course.course_name
            },
            'predictions': predictions,
            'count': len(predictions)
        })
        
    except Exception as e:
        return error_response(f"Error retrieving predictions: {str(e)}")

@prediction_bp.route('/at-risk', methods=['GET'])
@jwt_required()
@role_required(['faculty', 'admin'])
def get_at_risk_students():
    """Get all at-risk students (faculty/admin only)"""
    try:
        # Get query parameters
        offering_id = request.args.get('offering_id', type=int)
        risk_levels = request.args.getlist('risk_level') or ['high', 'medium']
        
        # Get at-risk students
        at_risk = prediction_service.get_at_risk_students(offering_id, risk_levels)
        
        return api_response({
            'filters': {
                'offering_id': offering_id,
                'risk_levels': risk_levels
            },
            'students': at_risk,
            'count': len(at_risk)
        })
        
    except Exception as e:
        return error_response(f"Error retrieving at-risk students: {str(e)}")

@prediction_bp.route('/features/<string:enrollment_id>', methods=['GET'])
@jwt_required()
def get_student_features(enrollment_id):
    """Get calculated features for a student (for debugging/transparency)"""
    try:
        # Verify access
        user_id = get_jwt_identity()
        enrollment = Enrollment.query.get(enrollment_id)
        
        if not enrollment:
            return error_response("Enrollment not found", 404)
        
        if not _has_access_to_enrollment(user_id, enrollment):
            return error_response("Access denied", 403)
        
        # Get cached features if available
        from backend.models import FeatureCache
        cached = FeatureCache.query.filter_by(
            enrollment_id=enrollment_id
        ).order_by(FeatureCache.calculated_at.desc()).first()
        
        if cached:
            return api_response({
                'enrollment_id': enrollment_id,
                'features': cached.to_dict(),
                'cached': True
            })
        else:
            # Calculate features on demand
            from backend.services.feature_calculator import FeatureCalculator
            calculator = FeatureCalculator()
            features = calculator.calculate_features_for_enrollment(int(enrollment_id))
            
            # Convert numpy array to list for JSON serialization
            feature_dict = {
                name: float(value) 
                for name, value in zip(calculator.get_feature_names(), features.flatten())
            }
            
            return api_response({
                'enrollment_id': enrollment_id,
                'features': feature_dict,
                'cached': False
            })
            
    except Exception as e:
        return error_response(f"Error calculating features: {str(e)}")

@prediction_bp.route('/compare/<string:enrollment_id>', methods=['POST'])
@jwt_required()
def compare_predictions(enrollment_id):
    """Compare predictions between two dates"""
    try:
        # Verify access
        user_id = get_jwt_identity()
        enrollment = Enrollment.query.get(enrollment_id)
        
        if not enrollment:
            return error_response("Enrollment not found", 404)
        
        if not _has_access_to_enrollment(user_id, enrollment):
            return error_response("Access denied", 403)
        
        # Get dates from request
        data = request.get_json()
        date1 = datetime.fromisoformat(data.get('date1'))
        date2 = datetime.fromisoformat(data.get('date2'))
        
        # Compare predictions
        comparison = prediction_service.compare_predictions(
            int(enrollment_id), date1, date2
        )
        
        return api_response({
            'enrollment_id': enrollment_id,
            'comparison': comparison
        })
        
    except Exception as e:
        return error_response(f"Error comparing predictions: {str(e)}")

# Helper functions
def _has_access_to_enrollment(user_id: str, enrollment: Enrollment) -> bool:
    """Check if user has access to an enrollment"""
    # Students can view their own
    if enrollment.student.user_id == int(user_id):
        return True
    
    # Faculty can view students in their courses
    faculty = Faculty.query.filter_by(user_id=int(user_id)).first()
    if faculty and enrollment.course_offering.faculty_id == faculty.faculty_id:
        return True
    
    # Admins can view all (handled by role_required decorator)
    return False

def _has_access_to_course(user_id: str, offering: CourseOffering) -> bool:
    """Check if user has access to a course offering"""
    # Faculty teaching the course
    faculty = Faculty.query.filter_by(user_id=int(user_id)).first()
    if faculty and offering.faculty_id == faculty.faculty_id:
        return True
    
    # Admins can access all (handled by role_required decorator)
    return False