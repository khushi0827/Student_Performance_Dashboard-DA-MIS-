import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# ===== CONFIGURATION =====
MYSQL_PASSWORD = "123456789"   # <-- CHANGE THIS
DB_NAME = "student_performance_db"
DB_HOST = "localhost"
DB_USER = "root"

# ===== PAGE SETUP =====
st.set_page_config(page_title="Student Performance Dashboard", layout="wide", page_icon="📊")
st.title("📊 Student Performance Dashboard")
st.markdown("### Interactive Analytics & Management")

# ===== DATABASE FUNCTIONS =====
@st.cache_resource
def init_engine():
    """Create SQLAlchemy engine once"""
    return create_engine(f"mysql+mysqlconnector://{DB_USER}:{MYSQL_PASSWORD}@{DB_HOST}/{DB_NAME}")

def load_data():
    """Load data from MySQL with error handling"""
    try:
        engine = init_engine()
        query = "SELECT * FROM students ORDER BY StudentID"
        df = pd.read_sql(query, engine)
        return df
    except SQLAlchemyError as e:
        st.error(f"❌ Database error: {e}")
        st.info("Please check your MySQL password in the script and ensure the database exists.\n\nRun `python store_to_mysql.py` first.")
        return pd.DataFrame()  # empty DataFrame

def run_sql(query, params=None):
    """Execute SQL command (INSERT, UPDATE, DELETE)"""
    try:
        engine = init_engine()
        with engine.connect() as conn:
            if params:
                conn.execute(text(query), params)
            else:
                conn.execute(text(query))
            conn.commit()
        return True
    except SQLAlchemyError as e:
        st.error(f"SQL Error: {e}")
        return False

# ===== LOAD DATA & VALIDATE =====
df = load_data()
if df.empty:
    st.stop()   # Stop execution if no data

# ===== KPI METRICS =====
total_students = len(df)
avg_total = df['TotalScore'].mean()
pass_rate = (df['Grade'] != 'F').mean() * 100
grade_counts = df['Grade'].value_counts()
top_grade = grade_counts.index[0] if not grade_counts.empty else "N/A"

col1, col2, col3, col4 = st.columns(4)
col1.metric("👩‍🎓 Total Students", total_students)
col2.metric("📈 Average Total Score", f"{avg_total:.1f}" if not pd.isna(avg_total) else "N/A")
col3.metric("✅ Pass Rate", f"{pass_rate:.1f}%" if not pd.isna(pass_rate) else "N/A")
col4.metric("🏆 Top Grade", top_grade)

st.markdown("---")

# ===== SIDEBAR FILTERS =====
st.sidebar.title("🎓 Filter Panel")
gender_filter = st.sidebar.multiselect("Gender", options=df['Gender'].unique(), default=df['Gender'].unique())
grade_filter = st.sidebar.multiselect("Grade", options=sorted(df['Grade'].unique()), default=sorted(df['Grade'].unique()))
age_range = st.sidebar.slider("Age Range", int(df['Age'].min()), int(df['Age'].max()), (15, 20))

filtered_df = df[(df['Gender'].isin(gender_filter)) & 
                 (df['Grade'].isin(grade_filter)) & 
                 (df['Age'].between(age_range[0], age_range[1]))]

# ===== TABS =====
tab1, tab2, tab3, tab4 = st.tabs(["📈 Analytics", "📋 Data View", "➕ Insert", "✏️ Modify/Delete"])

# ----- TAB 1: Analytics -----
with tab1:
    colA, colB = st.columns(2)
    with colA:
        st.subheader("Grade Distribution")
        grade_counts_f = filtered_df['Grade'].value_counts().sort_index()
        if not grade_counts_f.empty:
            fig, ax = plt.subplots()
            ax.bar(grade_counts_f.index, grade_counts_f.values, color=['green', 'blue', 'orange', 'red', 'gray'])
            ax.set_xlabel("Grade")
            ax.set_ylabel("Count")
            st.pyplot(fig)
        else:
            st.info("No data for selected filters")

        st.subheader("Score Distribution")
        if not filtered_df.empty:
            fig2, ax2 = plt.subplots()
            filtered_df[['AssignmentScore', 'QuizScore', 'MidtermScore', 'FinalExamScore']].plot(kind='box', ax=ax2)
            ax2.set_ylabel("Scores")
            st.pyplot(fig2)

    with colB:
        st.subheader("Total Score Histogram")
        if not filtered_df.empty:
            fig3, ax3 = plt.subplots()
            ax3.hist(filtered_df['TotalScore'], bins=20, edgecolor='black', alpha=0.7)
            ax3.set_xlabel("Total Score")
            ax3.set_ylabel("Frequency")
            st.pyplot(fig3)

        st.subheader("Attendance vs Total Score")
        if not filtered_df.empty:
            fig4, ax4 = plt.subplots()
            ax4.scatter(filtered_df['Attendance'], filtered_df['TotalScore'], alpha=0.6)
            ax4.set_xlabel("Attendance (%)")
            ax4.set_ylabel("Total Score")
            st.pyplot(fig4)

    st.subheader("Performance by Gender")
    if not filtered_df.empty:
        gender_perf = filtered_df.groupby('Gender')['TotalScore'].mean().sort_values()
        st.bar_chart(gender_perf)

# ----- TAB 2: Data View -----
with tab2:
    st.subheader("Student Records")
    if not filtered_df.empty:
        st.dataframe(filtered_df, use_container_width=True, height=400)
        st.download_button("Download Filtered Data (CSV)", filtered_df.to_csv(index=False), "student_data.csv", "text/csv")
    else:
        st.warning("No records match the current filters.")

# ----- TAB 3: Insert New Student -----
with tab3:
    st.subheader("➕ Add New Student")
    with st.form("insert_form"):
        new_id = st.number_input("Student ID (unique)", min_value=1, step=1, value=int(df['StudentID'].max())+1)
        new_name = st.text_input("Name")
        new_age = st.slider("Age", 15, 20, 17)
        new_gender = st.selectbox("Gender", ['M', 'F'])
        new_attendance = st.slider("Attendance (%)", 0.0, 100.0, 85.0)
        new_assign = st.slider("Assignment Score", 0.0, 100.0, 70.0)
        new_quiz = st.slider("Quiz Score", 0.0, 100.0, 70.0)
        new_mid = st.slider("Midterm Score", 0.0, 100.0, 70.0)
        new_final = st.slider("Final Exam Score", 0.0, 100.0, 70.0)
        new_remarks = st.text_area("Remarks")
        
        if st.form_submit_button("Insert Student"):
            total = new_assign*0.2 + new_quiz*0.2 + new_mid*0.3 + new_final*0.3
            grade = 'A' if total >= 90 else 'B' if total >= 80 else 'C' if total >= 70 else 'D' if total >= 60 else 'F'
            query = """
                INSERT INTO students 
                (StudentID, Name, Age, Gender, Attendance, AssignmentScore, QuizScore, 
                 MidtermScore, FinalExamScore, TotalScore, Grade, Remarks)
                VALUES (:id, :name, :age, :gender, :att, :assign, :quiz, :mid, :final, :total, :grade, :remarks)
            """
            params = {
                'id': new_id, 'name': new_name, 'age': new_age, 'gender': new_gender,
                'att': new_attendance, 'assign': new_assign, 'quiz': new_quiz,
                'mid': new_mid, 'final': new_final, 'total': total, 'grade': grade, 'remarks': new_remarks
            }
            if run_sql(query, params):
                st.success("Student added successfully!")
                st.rerun()

# ----- TAB 4: Modify / Delete -----
with tab4:
    st.subheader("✏️ Modify or Delete Student")
    student_ids = df['StudentID'].tolist()
    if student_ids:
        selected_id = st.selectbox("Select Student ID to modify", student_ids)
        current = df[df['StudentID'] == selected_id].iloc[0]
        
        with st.form("update_form"):
            new_name = st.text_input("Name", current['Name'])
            new_age = st.number_input("Age", min_value=15, max_value=20, value=int(current['Age']))
            new_gender = st.selectbox("Gender", ['M', 'F'], index=0 if current['Gender'] == 'M' else 1)
            new_attendance = st.slider("Attendance (%)", 0.0, 100.0, float(current['Attendance']))
            new_assign = st.slider("Assignment Score", 0.0, 100.0, float(current['AssignmentScore']))
            new_quiz = st.slider("Quiz Score", 0.0, 100.0, float(current['QuizScore']))
            new_mid = st.slider("Midterm Score", 0.0, 100.0, float(current['MidtermScore']))
            new_final = st.slider("Final Exam Score", 0.0, 100.0, float(current['FinalExamScore']))
            new_remarks = st.text_area("Remarks", current['Remarks'])
            
            col1, col2 = st.columns(2)
            with col1:
                update_btn = st.form_submit_button("Update Record")
            with col2:
                delete_btn = st.form_submit_button("Delete Record", type="primary")
            
            if update_btn:
                total = new_assign*0.2 + new_quiz*0.2 + new_mid*0.3 + new_final*0.3
                grade = 'A' if total >= 90 else 'B' if total >= 80 else 'C' if total >= 70 else 'D' if total >= 60 else 'F'
                query = """
                    UPDATE students SET 
                    Name=:name, Age=:age, Gender=:gender, Attendance=:att, AssignmentScore=:assign,
                    QuizScore=:quiz, MidtermScore=:mid, FinalExamScore=:final, TotalScore=:total,
                    Grade=:grade, Remarks=:remarks
                    WHERE StudentID=:id
                """
                params = {
                    'id': selected_id, 'name': new_name, 'age': new_age, 'gender': new_gender,
                    'att': new_attendance, 'assign': new_assign, 'quiz': new_quiz,
                    'mid': new_mid, 'final': new_final, 'total': total, 'grade': grade, 'remarks': new_remarks
                }
                if run_sql(query, params):
                    st.success("Record updated!")
                    st.rerun()
            
            if delete_btn:
                confirm = st.checkbox("Confirm deletion (cannot undo)")
                if confirm:
                    if run_sql("DELETE FROM students WHERE StudentID = :id", {'id': selected_id}):
                        st.warning("Record deleted!")
                        st.rerun()
    else:
        st.info("No students found in database.")

st.sidebar.markdown("---")
st.sidebar.info("Use tabs to analyze, view, insert, or modify student data.")