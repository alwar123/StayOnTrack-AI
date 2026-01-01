from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

class Batch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True) # Check logic for user relation later if strict
    students = db.relationship('Student', backref='batch', cascade="all, delete-orphan", lazy=True)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.Integer, db.ForeignKey('batch.id'), nullable=True) # Nullable for compatibility
    name = db.Column(db.String(100), nullable=False)
    # Academic Data
    study_hours = db.Column(db.Float, nullable=False)
    assignment_score = db.Column(db.Float, nullable=False)
    attendance = db.Column(db.Float, nullable=False)
    test1 = db.Column(db.Float, nullable=False)
    test2 = db.Column(db.Float, nullable=False)
    final_exam = db.Column(db.Float, nullable=False)
    project_score = db.Column(db.Float, nullable=False)
    participation = db.Column(db.Float, nullable=True)
    sleep_hours = db.Column(db.Float, nullable=True)
    internet_usage_hours = db.Column(db.Float, nullable=True)
    stress_level = db.Column(db.Integer, nullable=True)
    
    # Relationship with reports
    report = db.relationship('Report', backref='student', uselist=False, cascade="all, delete-orphan")

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), unique=True, nullable=False)
    predicted_grade = db.Column(db.String(5), nullable=False)
    dropout_risk = db.Column(db.String(20), nullable=False)
    recommendation = db.Column(db.Text, nullable=False)
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)
