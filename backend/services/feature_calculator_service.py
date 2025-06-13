# backend/services/feature_calculator_service.py
import pandas as pd
import numpy as np
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy import text
from ..extensions import db

logger = logging.getLogger(__name__)

class WebAppFeatureCalculator:
    """
    Calculate all 26 features required by the ML model
    """
    
    def __init__(self):
        # Load feature order from your trained model
        try:
            with open('ml_models/feature_list.json', 'r') as f:
                self.feature_order = json.load(f)
            logger.info(f"Loaded {len(self.feature_order)} features from model")
        except FileNotFoundError:
            logger.error("feature_list.json not found")
            self.feature_order = []
    
    def calculate_features_for_student(
        self, 
        enrollment_id: int, 
        calculation_date: Optional[datetime] = None
    ) -> Dict[str, float]:
        """
        Calculate all 26 features for a single student enrollment
        """
        if calculation_date is None:
            calculation_date = datetime.now()
        
        logger.info(f"Calculating features for enrollment {enrollment_id}")
        
        try:
            # Check if enrollment exists
            enrollment_check = db.engine.execute(
                text("SELECT student_id FROM enrollments WHERE enrollment_id = :id"),
                id=enrollment_id
            ).fetchone()
            
            if not enrollment_check:
                raise ValueError(f"Enrollment {enrollment_id} not found")
            
            # Calculate each feature group
            features = {}
            
            # Activity features (from attendance and LMS data)
            activity_features = self._calculate_activity_features(enrollment_id, calculation_date)
            features.update(activity_features)
            
            # Assessment features
            assessment_features = self._calculate_assessment_features(enrollment_id, calculation_date)
            features.update(assessment_features)
            
            # Temporal features
            temporal_features = self._calculate_temporal_features(enrollment_id, calculation_date)
            features.update(temporal_features)
            
            # Demographic features
            student_id = enrollment_check[0]
            demographic_features = self._calculate_demographic_features(student_id)
            features.update(demographic_features)
            
            # Ensure all 26 features are present
            ordered_features = {}
            for feature in self.feature_order:
                ordered_features[feature] = features.get(feature, 0.0)
            
            logger.info(f"Successfully calculated {len(ordered_features)} features")
            return ordered_features
            
        except Exception as e:
            logger.error(f"Error calculating features for enrollment {enrollment_id}: {str(e)}")
            return self._get_default_features()
    
    def _calculate_activity_features(self, enrollment_id: int, calc_date: datetime) -> Dict[str, float]:
        """Calculate activity-based features from attendance and LMS data"""
        
        # Get attendance data
        attendance_query = text("""
            SELECT attendance_date, status 
            FROM attendance 
            WHERE enrollment_id = :enrollment_id 
            AND attendance_date <= :calc_date
            ORDER BY attendance_date
        """)
        
        try:
            attendance_result = db.engine.execute(
                attendance_query, 
                enrollment_id=enrollment_id, 
                calc_date=calc_date.date()
            )
            attendance_data = [dict(row) for row in attendance_result]
        except:
            attendance_data = []
        
        # Get LMS activity data
        lms_query = text("""
            SELECT 
                DATE(activity_timestamp) as activity_date,
                activity_type,
                resource_id,
                COUNT(*) as click_count
            FROM lms_activities 
            WHERE enrollment_id = :enrollment_id 
            AND activity_timestamp <= :calc_date
            GROUP BY DATE(activity_timestamp), activity_type, resource_id
            ORDER BY activity_date
        """)
        
        try:
            lms_result = db.engine.execute(
                lms_query, 
                enrollment_id=enrollment_id, 
                calc_date=calc_date
            )
            lms_data = [dict(row) for row in lms_result]
        except:
            lms_data = []
        
        # Calculate features
        features = {}
        
        # Days active (from both attendance and LMS)
        active_dates = set()
        
        # Add attendance dates where student was present/late
        for record in attendance_data:
            if record['status'] in ['present', 'late']:
                active_dates.add(record['attendance_date'])
        
        # Add LMS activity dates
        for record in lms_data:
            active_dates.add(record['activity_date'])
        
        features['days_active'] = len(active_dates)
        
        # Total clicks (weighted by attendance and LMS activity)
        total_clicks = 0
        
        # Add attendance clicks (using mapping rules)
        present_count = sum(1 for r in attendance_data if r['status'] == 'present')
        late_count = sum(1 for r in attendance_data if r['status'] == 'late')
        total_clicks += (present_count * 30) + (late_count * 15)
        
        # Add LMS clicks (weighted by activity type)
        click_weights = {
            'resource_view': 1, 'forum_post': 5, 'forum_reply': 3,
            'assignment_view': 2, 'quiz_attempt': 10, 'video_watch': 1,
            'file_download': 2, 'page_view': 1
        }
        
        for record in lms_data:
            weight = click_weights.get(record['activity_type'], 1)
            total_clicks += record['click_count'] * weight
        
        features['total_clicks'] = total_clicks
        
        # Unique materials (unique resources + attendance sessions)
        unique_materials = set()
        
        # Add LMS resources
        for record in lms_data:
            if record['resource_id']:
                unique_materials.add(record['resource_id'])
        
        # Add attendance as unique "materials"
        for record in attendance_data:
            if record['status'] in ['present', 'late']:
                unique_materials.add(f"attendance_{record['attendance_date']}")
        
        features['unique_materials'] = len(unique_materials)
        
        # Activity rate (percentage of course days active)
        course_length = 112  # 16-week semester = 112 days
        features['activity_rate'] = (features['days_active'] / course_length) * 100 if course_length > 0 else 0
        
        # Average clicks per active day
        features['avg_clicks_per_active_day'] = (
            total_clicks / features['days_active'] if features['days_active'] > 0 else 0
        )
        
        # First and last activity days (relative to course start)
        if active_dates:
            # Get enrollment date
            enrollment_query = text("SELECT enrollment_date FROM enrollments WHERE enrollment_id = :id")
            enrollment_result = db.engine.execute(enrollment_query, id=enrollment_id).fetchone()
            
            if enrollment_result:
                course_start = enrollment_result[0]
                min_date = min(active_dates)
                max_date = max(active_dates)
                
                features['first_activity_day'] = (min_date - course_start).days
                features['last_activity_day'] = (max_date - course_start).days
            else:
                features['first_activity_day'] = 0
                features['last_activity_day'] = 0
        else:
            features['first_activity_day'] = 0
            features['last_activity_day'] = 0
        
        return features
    
    def _calculate_assessment_features(self, enrollment_id: int, calc_date: datetime) -> Dict[str, float]:
        """Calculate assessment-based features"""
        
        # Get assessment submissions
        submission_query = text("""
            SELECT 
                asub.score,
                asub.submission_date,
                asub.is_late,
                COALESCE(a.assessment_type_mapped, 'Assignment') as assessment_type,
                a.due_date
            FROM assessment_submissions asub
            JOIN assessments a ON asub.assessment_id = a.assessment_id
            WHERE asub.enrollment_id = :enrollment_id 
            AND asub.submission_date <= :calc_date
        """)
        
        try:
            submission_result = db.engine.execute(
                submission_query, 
                enrollment_id=enrollment_id, 
                calc_date=calc_date
            )
            submissions = [dict(row) for row in submission_result]
        except:
            submissions = []
        
        features = {}
        
        if not submissions:
            # Return zero values for all assessment features
            return {
                'submitted_assessments': 0, 'submission_rate': 0, 'avg_score': 0,
                'avg_score_cma': 0, 'avg_score_tma': 0, 'avg_score_exam': 0,
                'on_time_submissions': 0, 'avg_days_early': 0, 'late_submission_count': 0
            }
        
        # Basic submission metrics
        features['submitted_assessments'] = len(submissions)
        
        # Get total assessments for this enrollment
        total_assessments_query = text("""
            SELECT COUNT(*) as total
            FROM assessments a
            JOIN course_offerings co ON a.offering_id = co.offering_id
            JOIN enrollments e ON e.offering_id = co.offering_id
            WHERE e.enrollment_id = :enrollment_id
            AND a.due_date <= :calc_date
        """)
        
        try:
            result = db.engine.execute(
                total_assessments_query, 
                enrollment_id=enrollment_id, 
                calc_date=calc_date
            ).fetchone()
            total_assessments = result[0] if result else 1
        except:
            total_assessments = 1
        
        features['submission_rate'] = (features['submitted_assessments'] / total_assessments) * 100
        
        # Average scores
        scores = [s['score'] for s in submissions if s['score'] is not None]
        features['avg_score'] = sum(scores) / len(scores) if scores else 0
        
        # Scores by assessment type
        for assess_type in ['CMA', 'TMA', 'Exam']:
            type_scores = [s['score'] for s in submissions 
                          if s['assessment_type'] == assess_type and s['score'] is not None]
            features[f'avg_score_{assess_type.lower()}'] = (
                sum(type_scores) / len(type_scores) if type_scores else 0
            )
        
        # Submission timing
        on_time = sum(1 for s in submissions if not s['is_late'])
        late = sum(1 for s in submissions if s['is_late'])
        
        features['on_time_submissions'] = on_time
        features['late_submission_count'] = late
        
        # Calculate average days early (simplified)
        features['avg_days_early'] = 0  # Would need more complex date calculation
        
        return features
    
    def _calculate_temporal_features(self, enrollment_id: int, calc_date: datetime) -> Dict[str, float]:
        """Calculate temporal pattern features"""
        
        # Get all activity dates (attendance + LMS)
        activity_query = text("""
            SELECT DISTINCT DATE(activity_timestamp) as activity_date
            FROM lms_activities 
            WHERE enrollment_id = :enrollment_id 
            AND activity_timestamp <= :calc_date
            
            UNION
            
            SELECT DISTINCT attendance_date as activity_date
            FROM attendance 
            WHERE enrollment_id = :enrollment_id 
            AND status IN ('present', 'late')
            AND attendance_date <= :calc_date
            
            ORDER BY activity_date
        """)
        
        try:
            activity_result = db.engine.execute(
                activity_query, 
                enrollment_id=enrollment_id, 
                calc_date=calc_date
            )
            activity_dates = [row[0] for row in activity_result]
        except:
            activity_dates = []
        
        features = {}
        
        if not activity_dates:
            return {
                'weekly_activity_std': 0, 'activity_regularity': 0,
                'longest_inactivity_gap': 0, 'weekend_activity_ratio': 0,
                'activity_trend': 0
            }
        
        # Convert to pandas for easier calculation
        df = pd.DataFrame({'activity_date': pd.to_datetime(activity_dates)})
        df['week'] = df['activity_date'].dt.isocalendar().week
        
        # Weekly activity count
        weekly_counts = df.groupby('week').size()
        features['weekly_activity_std'] = weekly_counts.std() if len(weekly_counts) > 1 else 0
        
        # Activity regularity
        if weekly_counts.mean() > 0 and len(weekly_counts) > 1:
            cv = weekly_counts.std() / weekly_counts.mean()
            features['activity_regularity'] = 1 / (1 + cv)
        else:
            features['activity_regularity'] = 0
        
        # Longest inactivity gap
        if len(activity_dates) > 1:
            gaps = []
            for i in range(1, len(activity_dates)):
                gap = (activity_dates[i] - activity_dates[i-1]).days
                gaps.append(gap)
            features['longest_inactivity_gap'] = max(gaps) if gaps else 0
        else:
            features['longest_inactivity_gap'] = 0
        
        # Weekend activity ratio
        df['day_of_week'] = df['activity_date'].dt.dayofweek
        weekend_count = len(df[df['day_of_week'].isin([5, 6])])  # Sat, Sun
        features['weekend_activity_ratio'] = weekend_count / len(df) if len(df) > 0 else 0
        
        # Activity trend (simplified)
        features['activity_trend'] = 0  # Would need scipy for linear regression
        
        return features
    
    def _calculate_demographic_features(self, student_id: str) -> Dict[str, float]:
        """Calculate demographic features from student record"""
        
        # Get student demographic data
        student_query = text("""
            SELECT age_band, highest_education, num_of_prev_attempts, 
                   studied_credits, has_disability
            FROM students 
            WHERE student_id = :student_id
        """)
        
        try:
            student_result = db.engine.execute(student_query, student_id=student_id).fetchone()
        except:
            student_result = None
        
        if not student_result:
            return self._get_default_demographic_features()
        
        features = {}
        
        # Age band encoding
        age_band_map = {'0-35': 0, '35-55': 1, '55+': 2}
        features['age_band_encoded'] = age_band_map.get(student_result[0] or '0-35', 0)
        
        # Education level encoding
        education_map = {
            'No Formal quals': 0, 'Lower Than A Level': 1,
            'A Level or Equivalent': 2, 'HE Qualification': 3,
            'Post Graduate Qualification': 4
        }
        features['highest_education_encoded'] = education_map.get(
            student_result[1] or 'A Level or Equivalent', 2
        )
        
        # Direct features
        features['num_of_prev_attempts'] = student_result[2] or 0
        features['studied_credits'] = student_result[3] or 60
        features['has_disability'] = 1 if student_result[4] else 0
        
        return features
    
    def _get_default_demographic_features(self) -> Dict[str, float]:
        """Default demographic features when student data is missing"""
        return {
            'age_band_encoded': 0,
            'highest_education_encoded': 2,
            'num_of_prev_attempts': 0,
            'studied_credits': 60,
            'has_disability': 0
        }
    
    def _get_default_features(self) -> Dict[str, float]:
        """Return default feature values when calculation fails"""
        return {feature: 0.0 for feature in self.feature_order}