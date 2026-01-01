import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingClassifier
import joblib, os, numpy as np

df = pd.read_csv("data/sample_student_data.csv")

if "Grade" not in df.columns:
    print("⚠️ 'Grade' column not found — auto-generating based on performance metrics.")
    performance = df[["StudyHours","AssignmentScore","ProjectScore","Test1","Test2","FinalExam"]].mean(axis=1)
    df["Grade"] = pd.cut(
        performance,
        bins=[0, 50, 65, 75, 85, 100],
        labels=["D", "C", "B", "B+", "A"],
        include_lowest=True
    )

X = df.drop(columns=["Name", "Grade"], errors="ignore")
y = df["Grade"]

X_encoded = pd.get_dummies(X, drop_first=True)

X_train, X_test, y_train, y_test = train_test_split(X_encoded, y, test_size=0.2, random_state=42)


model = GradientBoostingClassifier(
    n_estimators=400,
    learning_rate=0.05,
    max_depth=6,
    subsample=0.9,
    random_state=42
)
model.fit(X_train, y_train)


os.makedirs("models", exist_ok=True)
joblib.dump(model, "models/student_grade_model.joblib")


importance = pd.DataFrame({
    "Feature": X_encoded.columns,
    "Importance": model.feature_importances_
}).sort_values(by="Importance", ascending=False)

importance.to_csv("data/feature_importance.csv", index=False)

print("✅ Model trained successfully and saved to 'models/student_grade_model.joblib'")
print("\nTop Features Influencing Performance:")
print(importance.head(10))
