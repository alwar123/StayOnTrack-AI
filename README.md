# AI Student Grade & Drop-out Risk Prediction System

A teacher-only web application that uses Machine Learning to predict student grades and dropout risks, providing actionable AI-generated recommendations.

## Features
- **Teacher Authentication**: Secure login for authorized personnel.
- **AI Prediction Engine**: Predicts final grades and dropout risk levels (Low, Medium, High).
- **Automated Recommendations**: Generates personalized insights based on academic data.
- **Bulk Import**: Upload CSV files to process multiple students at once.
- **Persistent Reports**: Saves the latest analysis for every student.
- **Dynamic Dashboard**: Visual overview of class performance.

## Setup & Running
1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```
2. **Run the Application**
   ```bash
   python app.py
   ```
3. **Access the Dashboard**
   - Open Browser: `http://127.0.0.1:5000`
   - Default Credentials:
     - Username: `teacher`
     - Password: `password123`

## Usage
- **Upload Data**: Use the "Upload CSV" button. (Sample data in `data/sample_student_data.csv`)
- **View Reports**: Click "View Report" on any student to see detailed AI insights.
- **Regenerate**: Manually re-run the prediction for a specific student if needed.
