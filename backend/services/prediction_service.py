# backend/services/prediction_service.py
import pickle
import numpy as np
import pandas as pd
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from ..extensions import db
from ..models import Prediction, Enrollment
from .feature_calculator_service import WebAppFeatureCalculator

logger = logging.getLogger(__name__)

class MLPredictionService:
    """
    Service for making predictions using your trained XGBoost model
    """
    
    def __init__(self):
        self.model = None
        self.scaler = None
        self.feature_calculator = WebAppFeatureCalculator()
        self.model_metadata = None
        self._load_model()
    
    def _load_model(self):
        """Load the trained model and scaler"""
        try:
            # Load model
            with open('ml_models/grade_predictor.pkl', 'rb') as f:
                self.model = pickle.load(f)
            
            # Load scaler
            with open('ml_models/scaler.pkl', 'rb') as f:
                self.scaler = pickle.load(f)
            
            # Load metadata
            with open('ml_models/model_metadata.json', 'r') as f:
                self.model_metadata = json.load(f)
            
            logger.info(f"Successfully loaded model: {self.model_metadata.get('model_name', 'Unknown')}")
            logger.info(f"Model expects {self.model_metadata.get('feature_count', 0)} features")
            
        except Exception as e:
            logger.error(f"Failed to load model: {str(e)}")
            raise
    
    def predict_student_grade(
        self, 
        enrollment_id: int, 
        calculation_date: Optional[datetime] = None
    ) -> Dict[str, any]:
        """
        Predict grade for a single student
        """
        try:
            logger.info(f"Starting prediction for enrollment {enrollment_id}")
            
            # Calculate features
            features = self.feature_calculator.calculate_features_for_student(
                enrollment_id, 
                calculation_date
            )
            
            if not features:
                raise ValueError("Failed to calculate features")
            
            logger.info(f"Features calculated: {len(features)} features")
            
            # Convert to numpy array in correct order
            feature_vector = np.array([
                features[feature] for feature in self.model_metadata['feature_order']
            ]).reshape(1, -1)
            
            logger.info(f"Feature vector shape: {feature_vector.shape}")
            
            # Scale features
            scaled_features = self.scaler.transform(feature_vector)
            logger.info("Features scaled successfully")
            
            # Make prediction
            prediction_proba = self.model.predict_proba(scaled_features)[0]
            predicted_class = self.model.predict(scaled_features)[0]
            
            logger.info(f"Raw prediction: class={predicted_class}, probabilities={prediction_proba}")
            
            # Map prediction to grade
            grade_mapping = {0: 'Fail', 1: 'Pass', 2: 'Distinction', 3: 'Withdrawn'}
            predicted_grade = grade_mapping.get(predicted_class, 'Unknown')
            
            # Calculate confidence (max probability)
            confidence = float(np.max(prediction_proba))
            
            # Determine risk level
            risk_level = self._calculate_risk_level(predicted_grade, confidence)
            
            # Store prediction in database
            prediction_record = self._save_prediction(
                enrollment_id=enrollment_id,
                predicted_grade=predicted_grade,
                confidence=confidence,
                risk_level=risk_level,
                features=features
            )
            
            result = {
                'prediction_id': prediction_record.prediction_id,
                'enrollment_id': enrollment_id,
                'predicted_grade': predicted_grade,
                'confidence_score': confidence,
                'risk_level': risk_level,
                'prediction_date': prediction_record.prediction_date.isoformat(),
                'model_version': self.model_metadata.get('model_name', 'v1.0'),
                'features_used': features,
                'class_probabilities': {
                    'Fail': float(prediction_proba[0]) if len(prediction_proba) > 0 else 0,
                    'Pass': float(prediction_proba[1]) if len(prediction_proba) > 1 else 0,
                    'Distinction': float(prediction_proba[2]) if len(prediction_proba) > 2 else 0,
                    'Withdrawn': float(prediction_proba[3]) if len(prediction_proba) > 3 else 0
                }
            }
            
            logger.info(f"Prediction completed: {predicted_grade} (confidence: {confidence:.2f})")
            return result
            
        except Exception as e:
            logger.error(f"Error predicting for enrollment {enrollment_id}: {str(e)}")
            raise
    
    def predict_batch(
        self, 
        enrollment_ids: List[int], 
        calculation_date: Optional[datetime] = None
    ) -> List[Dict[str, any]]:
        """
        Predict grades for multiple students
        """
        results = []
        
        for enrollment_id in enrollment_ids:
            try:
                prediction = self.predict_student_grade(enrollment_id, calculation_date)
                results.append(prediction)
            except Exception as e:
                logger.error(f"Failed to predict for enrollment {enrollment_id}: {str(e)}")
                # Add error record
                results.append({
                    'enrollment_id': enrollment_id,
                    'error': str(e),
                    'predicted_grade': None,
                    'confidence_score': 0.0,
                    'risk_level': 'unknown'
                })
        
        return results
    
    def _calculate_risk_level(self, predicted_grade: str, confidence: float) -> str:
        """
        Calculate risk level based on prediction and confidence
        """
        if predicted_grade in ['Fail', 'Withdrawn']:
            return 'high'
        elif predicted_grade == 'Pass' and confidence < 0.7:
            return 'medium'
        elif predicted_grade == 'Pass' and confidence >= 0.7:
            return 'low'
        elif predicted_grade == 'Distinction':
            return 'low'
        else:
            return 'medium'
    
    def _save_prediction(
        self,
        enrollment_id: int,
        predicted_grade: str,
        confidence: float,
        risk_level: str,
        features: Dict[str, float]
    ) -> Prediction:
        """
        Save prediction to database
        """
        try:
            # Create prediction record
            prediction = Prediction(
                enrollment_id=enrollment_id,
                prediction_date=datetime.now(),
                predicted_grade=predicted_grade,
                confidence_score=confidence,
                risk_level=risk_level,
                model_version=self.model_metadata.get('model_name', 'v1.0'),
                feature_snapshot=features
            )
            
            db.session.add(prediction)
            db.session.commit()
            
            logger.info(f"Prediction saved with ID: {prediction.prediction_id}")
            return prediction
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to save prediction: {str(e)}")
            raise
    
    def get_model_info(self) -> Dict[str, any]:
        """
        Get information about the loaded model
        """
        return {
            'model_name': self.model_metadata.get('model_name', 'Unknown'),
            'model_type': self.model_metadata.get('model_type', 'Unknown'),
            'feature_count': self.model_metadata.get('feature_count', 0),
            'export_date': self.model_metadata.get('export_date', 'Unknown'),
            'training_complete': self.model_metadata.get('training_complete', False),
            'features': self.model_metadata.get('feature_order', [])
        }
    
    def validate_features(self, features: Dict[str, float]) -> Dict[str, any]:
        """
        Validate that features are complete and in correct format
        """
        expected_features = set(self.model_metadata['feature_order'])
        provided_features = set(features.keys())
        
        missing_features = expected_features - provided_features
        extra_features = provided_features - expected_features
        
        return {
            'is_valid': len(missing_features) == 0,
            'expected_count': len(expected_features),
            'provided_count': len(provided_features),
            'missing_features': list(missing_features),
            'extra_features': list(extra_features)
        }