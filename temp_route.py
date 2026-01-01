
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
            s_data["Analysis Date"] = student.report.generated_at.strftime('%Y-%m-%d %H:%M:%S')
        else:
            s_data["Predicted Grade"] = "N/A"
            s_data["Dropout Risk"] = "Pending"
            s_data["Recommendation"] = ""
            s_data["Analysis Date"] = ""
            
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
