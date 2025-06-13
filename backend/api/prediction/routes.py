# backend/api/prediction/routes.py (REPLACE EXISTING FILE)
from flask import Blueprint, request, jsonify, current_app
from backend.models import Prediction, Student, Enrollment
from backend.extensions import db
from backend.services.prediction_service import MLPredictionService
from backend.services.feature_calculator_service import WebAppFeatureCalculator
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import text
import logging
from datetime import datetime

logger = logging.getLogger('prediction')

prediction_bp = Blueprint('prediction', __name__)

# Initialize services (lazy loading)
_prediction_service = None
_feature_calculator = None

def get_prediction_service():
    global _prediction_service
    if _prediction_service is None:
        _prediction_service = MLPredictionService()
    return _prediction_service

def get_feature_calculator():
    global _feature_calculator
    if _feature_calculator is None:
        _feature_calculator = WebAppFeatureCalculator()
    return _feature_calculator

@prediction_bp.route('/health', methods=['GET'])
def health_check():
    """Check if prediction service is working"""
    try:
        prediction_service = get_prediction_service()
        model_info = prediction_service.get_model_info()
        return jsonify({
            'status': 'success',
            'message': 'Prediction service is healthy',
            'data': model_info
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Prediction service error: {str(e)}'
        }), 500

@prediction_bp.route('/model/info', methods=['GET'])
@jwt_required()
def get_model_info():
    """Get information about the loaded model"""
    try:
        prediction_service = get_prediction_service()
        model_info = prediction_service.get_model_info()
        return jsonify({
            'status': 'success',
            'message': 'Model information retrieved successfully',
            'data': model_info
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to get model info: {str(e)}'
        }), 500

@prediction_bp.route('/student/<int:enrollment_id>', methods=['GET'])
@jwt_required()
def get_student_prediction(enrollment_id):
    """Get latest prediction for a student"""
    try:
        # Get latest prediction from database
        latest_prediction = db.session.query(Prediction)\
            .filter_by(enrollment_id=enrollment_id)\
            .order_by(Prediction.prediction_date.desc())\
            .first()
        
        if not latest_prediction:
            return jsonify({
                'status': 'error',
                'message': 'No predictions found for this enrollment'
            }), 404
        
        return jsonify({
            'status': 'success',
            'message': 'Prediction retrieved successfully',
            'data': latest_prediction.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error retrieving prediction for enrollment {enrollment_id}: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve prediction'
        }), 500

@prediction_bp.route('/student/<int:enrollment_id>/generate', methods=['POST'])
@jwt_required()
def generate_student_prediction(enrollment_id):
    """Generate new prediction for a student"""
    try:
        # Check if enrollment exists
        enrollment = db.session.get(Enrollment, enrollment_id)
        if not enrollment:
            return jsonify({
                'status': 'error',
                'message': 'Enrollment not found'
            }), 404
        
        # Generate prediction
        prediction_service = get_prediction_service()
        prediction_result = prediction_service.predict_student_grade(enrollment_id)
        
        return jsonify({
            'status': 'success',
            'message': 'Prediction generated successfully',
            'data': prediction_result
        })
        
    except Exception as e:
        logger.error(f"Error generating prediction for enrollment {enrollment_id}: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to generate prediction: {str(e)}'
        }), 500

@prediction_bp.route('/features/<int:enrollment_id>', methods=['GET'])
@jwt_required()
def get_student_features(enrollment_id):
    """Calculate and return features for a student (for debugging)"""
    try:
        feature_calculator = get_feature_calculator()
        features = feature_calculator.calculate_features_for_student(enrollment_id)
        
        # Validate features
        prediction_service = get_prediction_service()
        validation = prediction_service.validate_features(features)
        
        return jsonify({
            'status': 'success',
            'message': 'Features calculated successfully',
            'data': {
                'enrollment_id': enrollment_id,
                'features': features,
                'validation': validation,
                'feature_count': len(features)
            }
        })
        
    except Exception as e:
        logger.error(f"Error calculating features for enrollment {enrollment_id}: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to calculate features: {str(e)}'
        }), 500

@prediction_bp.route('/course/<int:offering_id>', methods=['GET'])
@jwt_required()
def get_course_predictions(offering_id):
    """Get predictions for all students in a course"""
    try:
        # Get all enrollments for this course offering
        enrollments = db.session.query(Enrollment)\
            .filter_by(offering_id=offering_id)\
            .filter_by(enrollment_status='enrolled')\
            .all()
        
        if not enrollments:
            return jsonify({
                'status': 'error',
                'message': 'No active enrollments found for this course'
            }), 404
        
        # Get latest predictions for each enrollment
        predictions = []
        for enrollment in enrollments:
            latest_prediction = db.session.query(Prediction)\
                .filter_by(enrollment_id=enrollment.enrollment_id)\
                .order_by(Prediction.prediction_date.desc())\
                .first()
            
            if latest_prediction:
                prediction_data = latest_prediction.to_dict()
                prediction_data['student_info'] = {
                    'student_id': enrollment.student_id,
                    'name': f"{enrollment.student.first_name} {enrollment.student.last_name}"
                }
                predictions.append(prediction_data)
        
        return jsonify({
            'status': 'success',
            'message': 'Course predictions retrieved successfully',
            'data': {
                'course_offering_id': offering_id,
                'total_students': len(enrollments),
                'predictions_available': len(predictions),
                'predictions': predictions
            }
        })
        
    except Exception as e:
        logger.error(f"Error retrieving course predictions for offering {offering_id}: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve course predictions'
        }), 500

@prediction_bp.route('/course/<int:offering_id>/generate', methods=['POST'])
@jwt_required()
def generate_course_predictions(offering_id):
    """Generate predictions for all students in a course"""
    try:
        # Get all active enrollments for this course
        enrollments = db.session.query(Enrollment)\
            .filter_by(offering_id=offering_id)\
            .filter_by(enrollment_status='enrolled')\
            .all()
        
        if not enrollments:
            return jsonify({
                'status': 'error',
                'message': 'No active enrollments found for this course'
            }), 404
        
        # Generate predictions for all students
        prediction_service = get_prediction_service()
        enrollment_ids = [e.enrollment_id for e in enrollments]
        prediction_results = prediction_service.predict_batch(enrollment_ids)
        
        # Count successful vs failed predictions
        successful = [p for p in prediction_results if 'error' not in p]
        failed = [p for p in prediction_results if 'error' in p]
        
        return jsonify({
            'status': 'success',
            'message': f'Generated {len(successful)} predictions successfully',
            'data': {
                'course_offering_id': offering_id,
                'total_students': len(enrollments),
                'successful_predictions': len(successful),
                'failed_predictions': len(failed),
                'predictions': prediction_results
            }
        })
        
    except Exception as e:
        logger.error(f"Error generating course predictions for offering {offering_id}: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to generate course predictions'
        }), 500

@prediction_bp.route('/at-risk', methods=['GET'])
@jwt_required()
def get_at_risk_students():
    """Get all students with high or medium risk predictions"""
    try:
        # Get latest high/medium risk predictions using raw SQL for compatibility
        at_risk_query = text("""
            SELECT p.prediction_id, p.enrollment_id, p.predicted_grade, 
                   p.confidence_score, p.risk_level, p.prediction_date,
                   e.student_id, s.first_name, s.last_name, 
                   c.course_code, c.course_name
            FROM predictions p
            JOIN enrollments e ON p.enrollment_id = e.enrollment_id
            JOIN students s ON e.student_id = s.student_id
            JOIN course_offerings co ON e.offering_id = co.offering_id
            JOIN courses c ON co.course_id = c.course_id
            WHERE p.risk_level IN ('high', 'medium')
            AND p.prediction_id IN (
                SELECT MAX(prediction_id) 
                FROM predictions 
                GROUP BY enrollment_id
            )
            ORDER BY 
                CASE p.risk_level 
                    WHEN 'high' THEN 1 
                    WHEN 'medium' THEN 2 
                    ELSE 3 
                END,
                p.confidence_score ASC
        """)
        
        result = db.engine.execute(at_risk_query)
        at_risk_students = []
        
        for row in result:
            at_risk_students.append({
                'prediction_id': row.prediction_id,
                'enrollment_id': row.enrollment_id,
                'student_id': row.student_id,
                'student_name': f"{row.first_name} {row.last_name}",
                'course_code': row.course_code,
                'course_name': row.course_name,
                'predicted_grade': row.predicted_grade,
                'confidence_score': float(row.confidence_score),
                'risk_level': row.risk_level,
                'prediction_date': row.prediction_date.isoformat()
            })
        
        return jsonify({
            'status': 'success',
            'message': 'At-risk students retrieved successfully',
            'data': {
                'total_at_risk': len(at_risk_students),
                'high_risk': len([s for s in at_risk_students if s['risk_level'] == 'high']),
                'medium_risk': len([s for s in at_risk_students if s['risk_level'] == 'medium']),
                'students': at_risk_students
            }
        })
        
    except Exception as e:
        logger.error(f"Error retrieving at-risk students: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve at-risk students'
        }), 500

# Add a simple test endpoint for checking enrollments
@prediction_bp.route('/test/enrollments', methods=['GET'])
@jwt_required()
def test_enrollments():
    """Test endpoint to see available enrollments"""
    try:
        enrollments = db.session.query(Enrollment)\
            .filter_by(enrollment_status='enrolled')\
            .limit(5)\
            .all()
        
        enrollment_data = []
        for e in enrollments:
            enrollment_data.append({
                'enrollment_id': e.enrollment_id,
                'student_id': e.student_id,
                'student_name': f"{e.student.first_name} {e.student.last_name}",
                'course': f"{e.offering.course.course_code}",
                'enrollment_date': e.enrollment_date.isoformat()
            })
        
        return jsonify({
            'status': 'success',
            'message': f'Found {len(enrollment_data)} enrollments',
            'data': enrollment_data
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500