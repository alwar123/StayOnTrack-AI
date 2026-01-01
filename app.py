from flask import Flask, render_template, request, redirect, url_for, flash, send_file, Response
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from database import db, User, Student, Report, Batch
from utils.ai_engine import predict_single_student, generate_recommendation
import joblib
import pandas as pd
import os
import json
from datetime import datetime
import io
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'supersecretkey') 

# Database Configuration for Render (PostgreSQL) vs Local (SQLite)
database_url = os.environ.get('DATABASE_URL', 'sqlite:///students.db')
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Ensure tables exist (Production safe-guard)
with app.app_context():
    db.create_all()

# Load Model
model_path = "models/student_grade_model.joblib"
if os.path.exists(model_path):
    model = joblib.load(model_path)
else:
    model = None # Handle gracefully if model missing

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Routes ---

@app.route("/", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()
        
        # Check if exists
        try:
             # Basic check to avoid duplicates if needed, but for now we trust unique constraints or lack thereof
             pass
        except:
             pass
             
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            # Persistence restored: We do NOT clear data here anymore.
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid username or password", "danger")
            
    return render_template("login.html")

@app.route("/student/<int:student_id>/update_name", methods=["POST"])
@login_required
def update_student_name(student_id):
    student = Student.query.get_or_404(student_id)
    new_name = request.form.get("new_name")
    
    if new_name and new_name.strip():
        student.name = new_name.strip()
        db.session.commit()
        flash("Student name updated successfully.", "success")
    else:
        flash("Invalid name provided.", "warning")
        
    return redirect(url_for('student_detail', student_id=student.id))

@app.route("/student/<int:student_id>/delete", methods=["POST"])
@login_required
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)
    try:
        # Delete associated report first if cascade isn't set up (though typical sqlalchemy usually handles it, manual is safer)
        if student.report:
            db.session.delete(student.report)
        db.session.delete(student)
        db.session.commit()
        flash("Student record deleted successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash("Error deleting record.", "danger")
        print(e)
        
    return redirect(url_for('dashboard'))
            
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        # Check if exists
        if User.query.filter_by(username=username).first():
            flash("Username already exists. Please choose another.", "danger")
            return redirect(url_for('register'))
            
        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, password=hashed_pw)
        db.session.add(user)
        db.session.commit()
        
        flash("Account created! You can now login.", "success")
        return redirect(url_for('login'))
        
    return render_template("register.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route("/dashboard")
@login_required
def dashboard():
    # Show list of Batches (Reports)
    batches = Batch.query.filter_by(user_id=current_user.id).order_by(Batch.created_at.desc()).all()
    
    # Calculate global stats
    total_students = 0
    high_risk_count = 0
    risk_counts = {'Low Risk': 0, 'Medium Risk': 0, 'High Risk': 0}
    
    for batch in batches:
        for student in batch.students:
            total_students += 1
            if student.report:
                r = student.report.dropout_risk
                risk_counts[r] = risk_counts.get(r, 0) + 1
                if r == "High Risk":
                    high_risk_count += 1
                
    return render_template("dashboard.html", 
                         batches=batches, 
                         total_students=total_students,
                         risk_counts=risk_counts)

@app.route("/batch/<int:batch_id>")
@login_required
def batch_detail(batch_id):
    batch = Batch.query.get_or_404(batch_id)
    # verify ownership
    if batch.user_id != current_user.id:
         flash("Unauthorized access.", "danger")
         return redirect(url_for('dashboard'))
    
    # Calculate stats for this batch
    risk_counts = {'Low Risk': 0, 'Medium Risk': 0, 'High Risk': 0}
    for student in batch.students:
        if student.report:
             r = student.report.dropout_risk
             risk_counts[r] = risk_counts.get(r, 0) + 1

    return render_template("batch_detail.html", batch=batch, risk_counts=risk_counts)

@app.route("/batch/<int:batch_id>/download_csv")
@login_required
def download_batch_csv(batch_id):
    batch = Batch.query.get_or_404(batch_id)
    if batch.user_id != current_user.id:
        flash("Unauthorized access.", "danger")
        return redirect(url_for('dashboard'))
    
    data_list = []
    
    for student in batch.students:
        s_data = {
            "Student Name": student.name,
            "Study Hours": student.study_hours,
            "Attendance (%)": student.attendance,
            "Assignment Score": student.assignment_score,
            "Test 1": student.test1,
            "Test 2": student.test2,
            "Final Exam": student.final_exam,
            "Project Score": student.project_score,
            "Participation": student.participation,
            "Sleep Hours": student.sleep_hours,
            "Internet Usage": student.internet_usage_hours,
            "Stress Level": student.stress_level,
        }
        
        if student.report:
            s_data["Predicted Grade"] = student.report.predicted_grade
            s_data["Dropout Risk"] = student.report.dropout_risk
            s_data["Recommendation"] = student.report.recommendation
            s_data["Analysis Date"] = student.report.generated_at.strftime('%d-%b-%Y')
            s_data["Analysis Time"] = student.report.generated_at.strftime('%I:%M %p')
        else:
            s_data["Predicted Grade"] = "N/A"
            s_data["Dropout Risk"] = "Pending"
            s_data["Recommendation"] = ""
            s_data["Analysis Date"] = ""
            s_data["Analysis Time"] = ""
            
        data_list.append(s_data)
        
    df = pd.DataFrame(data_list)
    
    # Create CSV in memory
    output = io.StringIO()
    df.to_csv(output, index=False)
    
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename=Report_{batch.name}_{datetime.now().strftime('%Y%m%d')}.csv"}
    )

@app.route("/student/<int:student_id>")
@login_required
def student_detail(student_id):
    student = Student.query.get_or_404(student_id)
    return render_template("student_detail.html", student=student)

@app.route("/student/regenerate/<int:student_id>", methods=["POST"])
@login_required
def regenerate_prediction(student_id):
    student = Student.query.get_or_404(student_id)
    
    if not model:
        flash("Model not loaded!", "danger")
        return redirect(url_for('student_detail', student_id=student.id))

    # Prepare data dictionary
    data = {
        "StudyHours": student.study_hours,
        "AssignmentScore": student.assignment_score,
        "Attendance": student.attendance,
        "Test1": student.test1,
        "Test2": student.test2,
        "FinalExam": student.final_exam,
        "ProjectScore": student.project_score,
        "Participation": student.participation,
        "SleepHours": student.sleep_hours,
        "InternetUsageHours": student.internet_usage_hours,
        "StressLevel": student.stress_level
    }
    
    grade, risk = predict_single_student(model, data)
    rec = generate_recommendation(data, grade, risk)
    
    if student.report:
        student.report.predicted_grade = grade
        student.report.dropout_risk = risk
        student.report.recommendation = rec
        student.report.generated_at = pd.Timestamp.now()
    else:
        new_report = Report(student_id=student.id, predicted_grade=grade, dropout_risk=risk, recommendation=rec)
        db.session.add(new_report)
        
    db.session.commit()
    flash("Prediction regenerated!", "success")
    return redirect(url_for('student_detail', student_id=student.id))

@app.route("/upload", methods=["POST"])
@login_required
def upload_csv():
    if 'file' not in request.files:
        flash("No file part", "danger")
        return redirect(url_for('dashboard'))
        
    file = request.files['file']
    report_name = request.form.get("report_name", f"Report - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    if file.filename == '':
        flash("No selected file", "danger")
        return redirect(url_for('dashboard'))

    if file and file.filename.endswith('.csv'):
        try:
            # Create Batch
            new_batch = Batch(name=report_name, user_id=current_user.id)
            db.session.add(new_batch)
            db.session.flush() # get ID
            
            df = pd.read_csv(file)
            count = 0
            
            for index, row in df.iterrows():
                # Flexible extraction
                name = row.get('Name') or row.get('StudentName') or f"Student {index+1}"
                
                # Smart Data Inference to prevent "Same Grade" issue for sparse CSVs
                # 1. Get a base academic performance indicator
                base_score = float(row.get('TestScores', row.get('Test1', row.get('Grade', 70.0))))
                
                # 2. Extract or infer fields
                study_hours = float(row.get('StudyHours', 5.0))
                attendance = float(row.get('Attendance', 85.0))
                
                # If specific columns are missing, use the base_score to maintain consistency
                # e.g. If TestScores is 40, assume Test2/Final are also around 40, not 70.
                test1 = float(row.get('Test1', base_score))
                test2 = float(row.get('Test2', base_score))
                final_exam = float(row.get('FinalExam', base_score))
                assignment_score = float(row.get('AssignmentScore', base_score + 5)) # Assignments usually slightly higher
                project_score = float(row.get('ProjectScore', base_score))
                
                # Limit values to 0-100
                test1 = max(0, min(100, test1))
                test2 = max(0, min(100, test2))
                final_exam = max(0, min(100, final_exam))
                
                # Create Student
                student = Student(
                    batch_id=new_batch.id,
                    name=str(name),
                    study_hours=study_hours,
                    assignment_score=assignment_score,
                    attendance=attendance,
                    test1=test1,
                    test2=test2,
                    final_exam=final_exam,
                    project_score=project_score,
                    participation=float(row.get('Participation')) if row.get('Participation') and str(row.get('Participation')).strip() else None,
                    sleep_hours=float(row.get('SleepHours')) if row.get('SleepHours') and str(row.get('SleepHours')).strip() else None,
                    internet_usage_hours=float(row.get('InternetUsageHours')) if row.get('InternetUsageHours') and str(row.get('InternetUsageHours')).strip() else None,
                    stress_level=int(row.get('StressLevel')) if row.get('StressLevel') and str(row.get('StressLevel')).strip() else None
                )
                db.session.add(student)
                db.session.flush() 
                
                # Prepare data for AI
                student_data_dict = {
                    'StudyHours': student.study_hours,
                    'Attendance': student.attendance,
                    'AssignmentScore': student.assignment_score,
                    'Test1': student.test1,
                    'Test2': student.test2,
                    'FinalExam': student.final_exam,
                    'ProjectScore': student.project_score,
                    'Participation': student.participation,
                    'SleepHours': student.sleep_hours,
                    'InternetUsageHours': student.internet_usage_hours,
                    'StressLevel': student.stress_level
                }
                
                # Predict
                if model:
                    try:
                        predicted_grade, risk_level = predict_single_student(model, student_data_dict)
                    except Exception as e:
                        print(f"Prediction error for {name}: {e}")
                        predicted_grade = "N/A"
                        risk_level = "Unknown"

                    # Recs
                    recs = generate_recommendation(student_data_dict, predicted_grade, risk_level)
                    
                    # Report
                    report = Report(
                        student_id=student.id,
                        predicted_grade=predicted_grade,
                        dropout_risk=risk_level,
                        recommendation=recs,
                        generated_at=datetime.now()
                    )
                    db.session.add(report)
                count += 1
                
            db.session.commit()
            flash(f"Successfully created report '{report_name}' with {count} students.", "success")
            return redirect(url_for('batch_detail', batch_id=new_batch.id))
            
        except Exception as e:
            print("Upload Error:", e)
            db.session.rollback()
            flash(f"Error processing file: {str(e)}", "danger")
            
    return redirect(url_for('dashboard'))

@app.route("/batch/<int:batch_id>/delete", methods=["POST"])
@login_required
def delete_batch(batch_id):
    batch = Batch.query.get_or_404(batch_id)
    if batch.user_id != current_user.id:
        flash("Unauthorized", "danger")
        return redirect(url_for('dashboard'))
        
    try:
        db.session.delete(batch)
        db.session.commit()
        flash("Report batch deleted.", "success")
    except:
        db.session.rollback()
        flash("Error deleting report batch.", "danger")
        
    return redirect(url_for('dashboard'))

@app.route("/init_db")
def init_db():
    db.create_all()
    # Create test user
    if not User.query.filter_by(username="teacher").first():
        hashed_pw = bcrypt.generate_password_hash("password123").decode('utf-8')
        user = User(username="teacher", password=hashed_pw)
        db.session.add(user)
        db.session.commit()
        return "Database initialized. User 'teacher' created."
    return "Database already initialized."

if __name__ == "__main__":
    with app.app_context():
        if not os.path.exists('reports'):
            os.makedirs('reports')
        # We'll run db creation on start for convenience in this env
        db.create_all()
        if not User.query.filter_by(username="teacher").first():
            hashed_pw = bcrypt.generate_password_hash("password123").decode('utf-8')
            user = User(username="teacher", password=hashed_pw)
            db.session.add(user)
            db.session.commit()
            print("Admin user 'teacher' created.")
            
    app.run(debug=True, port=5000)
