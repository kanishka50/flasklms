from datetime import datetime
from backend.extensions import db

class AssessmentType(db.Model):
    """Assessment type model"""
    __tablename__ = 'assessment_types'
    
    type_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    type_name = db.Column(db.String(50), nullable=False)
    weight_percentage = db.Column(db.Numeric(5, 2), nullable=True)
    
    # Relationships
    assessments = db.relationship('Assessment', backref='assessment_type', lazy=True)
    
    def __init__(self, type_name, weight_percentage=None):
        self.type_name = type_name
        self.weight_percentage = weight_percentage
    
    def to_dict(self):
        """Convert assessment type to dictionary for API responses"""
        return {
            'type_id': self.type_id,
            'type_name': self.type_name,
            'weight_percentage': float(self.weight_percentage) if self.weight_percentage else None
        }
    
    def __repr__(self):
        return f"<AssessmentType {self.type_name}>"


class Assessment(db.Model):
    """Assessment model"""
    __tablename__ = 'assessments'
    
    assessment_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    offering_id = db.Column(db.Integer, db.ForeignKey('course_offerings.offering_id'), nullable=False)
    type_id = db.Column(db.Integer, db.ForeignKey('assessment_types.type_id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    max_score = db.Column(db.Numeric(6, 2), nullable=False)
    due_date = db.Column(db.DateTime, nullable=True)
    weight = db.Column(db.Numeric(5, 2), nullable=True)
    description = db.Column(db.Text, nullable=True)
    is_published = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    submissions = db.relationship('AssessmentSubmission', backref='assessment', lazy=True)
    
    def __init__(self, offering_id, type_id, title, max_score, **kwargs):
        self.offering_id = offering_id
        self.type_id = type_id
        self.title = title
        self.max_score = max_score
        
        # Optional fields
        self.due_date = kwargs.get('due_date')
        self.weight = kwargs.get('weight')
        self.description = kwargs.get('description')
        self.is_published = kwargs.get('is_published', False)
    
    def to_dict(self):
        """Convert assessment to dictionary for API responses"""
        return {
            'assessment_id': self.assessment_id,
            'offering_id': self.offering_id,
            'type_id': self.type_id,
            'title': self.title,
            'max_score': float(self.max_score) if self.max_score else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'weight': float(self.weight) if self.weight else None,
            'description': self.description,
            'is_published': self.is_published,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'assessment_type': self.assessment_type.to_dict() if self.assessment_type else None
        }
    
    def __repr__(self):
        return f"<Assessment {self.assessment_id}: {self.title}>"


class AssessmentSubmission(db.Model):
    """Assessment submission model"""
    __tablename__ = 'assessment_submissions'
    
    submission_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    enrollment_id = db.Column(db.Integer, db.ForeignKey('enrollments.enrollment_id'), nullable=False)
    assessment_id = db.Column(db.Integer, db.ForeignKey('assessments.assessment_id'), nullable=False)
    submission_date = db.Column(db.DateTime, nullable=False)
    score = db.Column(db.Numeric(6, 2), nullable=True)
    percentage = db.Column(db.Numeric(5, 2), nullable=True)
    is_late = db.Column(db.Boolean, default=False)
    late_penalty = db.Column(db.Numeric(5, 2), default=0)
    graded_date = db.Column(db.DateTime, nullable=True)
    graded_by = db.Column(db.String(20), nullable=True)
    feedback = db.Column(db.Text, nullable=True)
    attempt_number = db.Column(db.Integer, default=1)
    
    __table_args__ = (
        db.UniqueConstraint('enrollment_id', 'assessment_id', 'attempt_number', name='unique_submission'),
    )
    
    def __init__(self, enrollment_id, assessment_id, submission_date, **kwargs):
        self.enrollment_id = enrollment_id
        self.assessment_id = assessment_id
        self.submission_date = submission_date
        
        # Optional fields
        self.score = kwargs.get('score')
        self.percentage = kwargs.get('percentage')
        self.is_late = kwargs.get('is_late', False)
        self.late_penalty = kwargs.get('late_penalty', 0)
        self.graded_date = kwargs.get('graded_date')
        self.graded_by = kwargs.get('graded_by')
        self.feedback = kwargs.get('feedback')
        self.attempt_number = kwargs.get('attempt_number', 1)
    
    def grade(self, score, graded_by, feedback=None):
        """Grade the submission"""
        self.score = score
        self.graded_by = graded_by
        self.graded_date = datetime.utcnow()
        self.feedback = feedback
        
        # Calculate percentage
        assessment = Assessment.query.get(self.assessment_id)
        if assessment and assessment.max_score:
            self.percentage = (float(score) / float(assessment.max_score)) * 100
        
        db.session.commit()
    
    def to_dict(self):
        """Convert submission to dictionary for API responses"""
        return {
            'submission_id': self.submission_id,
            'enrollment_id': self.enrollment_id,
            'assessment_id': self.assessment_id,
            'submission_date': self.submission_date.isoformat() if self.submission_date else None,
            'score': float(self.score) if self.score else None,
            'percentage': float(self.percentage) if self.percentage else None,
            'is_late': self.is_late,
            'late_penalty': float(self.late_penalty) if self.late_penalty else 0,
            'graded_date': self.graded_date.isoformat() if self.graded_date else None,
            'graded_by': self.graded_by,
            'feedback': self.feedback,
            'attempt_number': self.attempt_number,
            'assessment': self.assessment.to_dict() if self.assessment else None
        }
    
    def __repr__(self):
        return f"<Submission {self.submission_id} for Assessment {self.assessment_id}>"