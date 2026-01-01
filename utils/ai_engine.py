import pandas as pd
import numpy as np

def generate_recommendation(student_data, predicted_grade, dropout_risk):
    """
    Generates a deterministic actionable recommendation based on student data and predictions.
    """
    recommendations = []
    
    # Analyze components
    attendance = student_data.get('Attendance', 0)
    study_hours = student_data.get('StudyHours', 0)
    scores = [student_data.get(k, 0) for k in ['Test1', 'Test2', 'AssignmentScore']]
    avg_score = sum(scores) / len(scores) if scores else 0
    
    # 1. Risk-Based Recommendations
    if dropout_risk == 'High Risk':
        recommendations.append("URGENT: This student is at high risk of dropping out.")
        if attendance < 70:
            recommendations.append("Attendance is critical ({}%). Immediate parent-teacher meeting recommended.".format(attendance))
        if avg_score < 50:
            recommendations.append("Academic performance is severely low. Remedial classes are suggested.")
            
    elif dropout_risk == 'Medium Risk':
        recommendations.append("Warning: Student shows signs of struggle.")
        if study_hours < 5:
            recommendations.append("Self-study hours are low ({} hrs/week). Encourage a structured study plan.".format(study_hours))
        
        # Check Stress if available
        stress = student_data.get('StressLevel')
        if stress is not None and stress > 7:
            recommendations.append("Student reports high stress. Counseling or workload management advised.")

    # 2. Grade-Based specific advice
    if predicted_grade in ['D', 'F']:
        recommendations.append("Focus on core concepts. Review recent test mistakes.")
    elif predicted_grade == 'C':
        recommendations.append("Consistent effort needed to reach B grade. Focus on assignment quality.")
    elif predicted_grade in ['A', 'B+']:
        recommendations.append("Excellent performance. Encourage peer mentoring to reinforce knowledge.")

    # 3. Default fallback
    if not recommendations:
        recommendations.append("Student is performing well. Maintain current habits.")

    return " ".join(recommendations)

def predict_single_student(model, student_data):
    """
    Runs prediction for a single student dictionary/row.
    """
    # Create DataFrame for model input
    df_single = pd.DataFrame([student_data])
    
    # Impute missing values with Safe Defaults for Prediction Only
    # These defaults are 'neutral' and minimize impact on the prediction
    defaults = {
        'Participation': 80.0,
        'SleepHours': 7.0,
        'InternetUsageHours': 2.0,
        'StressLevel': 5
    }
    for col, val in defaults.items():
        if col not in df_single.columns or pd.isna(df_single[col].iloc[0]):
            df_single[col] = val

    # Ensure all features exist
    trained_cols = model.feature_names_in_
    X_encoded = pd.get_dummies(df_single, drop_first=True)
    
    for col in trained_cols:
        if col not in X_encoded.columns:
            X_encoded[col] = 0
    X_encoded = X_encoded[trained_cols]
    
    predicted_grade = model.predict(X_encoded)[0]
    
    # Determine Risk
    risk = "Low Risk"
    if predicted_grade in ["D", "F"]:
        risk = "High Risk"
    elif predicted_grade == "C":
        risk = "Medium Risk"
        
    return predicted_grade, risk
