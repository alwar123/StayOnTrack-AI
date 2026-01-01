import pandas as pd
import joblib
import os
from reportlab.pdfgen import canvas
from datetime import datetime

def load_model():
    return joblib.load("student_grade_model.joblib")

def predict_grades(model, df):
    features = df.drop(columns=["Name"], errors="ignore")
    return model.predict(features)

def risk_analysis(grade):
    if grade in ["A+", "A"]:
        return "Low Risk"
    elif grade in ["B+", "B"]:
        return "Moderate Risk"
    else:
        return "High Risk"

def recommendation(grade):
    if grade in ["A+", "A"]:
        return "Keep it up! Explore advanced topics."
    elif grade in ["B+", "B"]:
        return "Focus on weak areas and revise regularly."
    else:
        return "High attention needed — seek mentor guidance."

def generate_pdf(df):
    folder = "reports/generated_reports"
    os.makedirs(folder, exist_ok=True)

    filename = f"{folder}/Student_Report_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
    c = canvas.Canvas(filename)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, 800, "AI Student Performance Report")
    y = 770

    for _, row in df.iterrows():
        text = f"{row['Name']} | Grade: {row['Predicted_Grade']} | Risk: {row['Risk']} | {row['Recommendation']}"
        c.setFont("Helvetica", 11)
        c.drawString(50, y, text)
        y -= 20
        if y < 50:
            c.showPage()
            y = 800

    c.save()
    return filename
