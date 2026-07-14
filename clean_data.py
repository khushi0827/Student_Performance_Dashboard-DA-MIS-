import pandas as pd
import numpy as np

df = pd.read_csv(r"D:\DA_PROJECT\Student_Performance_Dashboard\messy_student_data.csv")
original_shape = df.shape

df.drop_duplicates(subset= 'StudentID', keep='first', inplace=True)

df['Name'] = df['Name'].fillna('Unknown')
df['Age'] = pd.to_numeric(df['Age'], errors='coerce')
df['Age'] = df['Age'].fillna(df['Age'].median())
df['Gender'] = df['Gender'].astype(str).str.strip().str.lower()
gender_map= {'m': 'M', 'male': 'M', 'f': 'F', 'female': 'F'}
df['Gender'] = df['Gender'].map(gender_map).fillna(df['Gender'].mode()[0] if not df['Gender'].mode().empty else 'M')
df['Remarks'] = df['Remarks'].fillna('')

numeric_cols = ['Attendance', 'AssignmentScore', 'QuizScore', 'MidtermScore', 'FinalExamScore']
for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors='coerce')
    df[col] = df[col].clip(0,100)
    df[col] = df[col].fillna(df[col].median())

df['Age'] = df['Age'].clip(15,20).fillna(17).astype(int)

df['TotalScore'] = (df['AssignmentScore']* 0.2 +
                    df['QuizScore'] * 0.2 +
                    df['MidtermScore'] * 0.3 +
                    df['FinalExamScore'] * 0.3)

def assign_grade(score):
    if score >= 90: return 'A'
    elif score >= 80: return 'B'
    elif score >= 70: return 'C'
    elif score >= 60: return 'D'
    else: return 'F'

df['Grade'] = df['TotalScore'].apply(assign_grade)
df.drop_duplicates(subset='StudentID', keep='first', inplace=True)
df.sort_values('StudentID', inplace=True)
df.reset_index(drop=True, inplace=True)

df.to_csv('cleaned_student_data.csv',index=False)
print(f"cleaned data:{len(df)} records. Saved to Cleaned student_data.csv")