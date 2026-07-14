import mysql.connector
import pandas as pd
from mysql.connector import Error

try:
    from sqlalchemy import create_engine
except ImportError:
    create_engine = None

# =========================
# CONFIGURATION
# =========================

MYSQL_PASSWORD = "123456789"  # Change if needed

DB_NAME = "student_performance_db"

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": MYSQL_PASSWORD,
    "database": DB_NAME
}


# =========================
# CREATE DATABASE
# =========================

def create_database():
    try:
        conn = mysql.connector.connect(
            host=DB_CONFIG["host"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"]
        )

        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")

        print(f"Database '{DB_NAME}' ready.")

        cursor.close()
        conn.close()

    except Error as e:
        print(f"Database creation error: {e}")
        exit(1)


# =========================
# CREATE TABLE
# =========================

def create_table():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            StudentID INT PRIMARY KEY,
            Name VARCHAR(100),
            Age INT,
            Gender VARCHAR(20),
            Attendance FLOAT,
            AssignmentScore FLOAT,
            QuizScore FLOAT,
            MidtermScore FLOAT,
            FinalExamScore FLOAT,
            TotalScore FLOAT,
            Grade VARCHAR(5),
            Remarks TEXT
        )
        """)

        conn.commit()

        print("Table 'students' ready.")

        cursor.close()
        conn.close()

    except Error as e:
        print(f"Table creation error: {e}")
        exit(1)


# =========================
# INSERT DATA
# =========================

def insert_data():
    try:

        if create_engine is None:
            raise ImportError(
                "SQLAlchemy not installed.\n"
                "Run: pip install sqlalchemy mysql-connector-python"
            )

        # Load CSV
        df = pd.read_csv("cleaned_student_data.csv")

        print("\nOriginal Columns:")
        print(df.columns.tolist())

        # Remove extra spaces
        df.columns = df.columns.str.strip()

        # Fix gender/Gender conflict
        if 'gender' in df.columns and 'Gender' in df.columns:
            df['Gender'] = df['Gender'].fillna(df['gender'])
            df.drop(columns=['gender'], inplace=True)

        elif 'gender' in df.columns:
            df.rename(columns={'gender': 'Gender'}, inplace=True)

        # Remove duplicate columns
        df = df.loc[:, ~df.columns.duplicated()]

        # Required columns
        required_columns = [
            'StudentID',
            'Name',
            'Age',
            'Gender',
            'Attendance',
            'AssignmentScore',
            'QuizScore',
            'MidtermScore',
            'FinalExamScore',
            'TotalScore',
            'Grade',
            'Remarks'
        ]

        # Keep only valid columns
        available_columns = [
            col for col in required_columns
            if col in df.columns
        ]

        df = df[available_columns]

        # Remove duplicate Student IDs
        if 'StudentID' in df.columns:
            df.drop_duplicates(
                subset=['StudentID'],
                keep='first',
                inplace=True
            )

        print("\nColumns To Insert:")
        print(df.columns.tolist())

        print(f"\nRecords Found: {len(df)}")

        # Clear table before insert
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        cursor.execute("TRUNCATE TABLE students")

        conn.commit()
        cursor.close()
        conn.close()

        print("Old data removed from table.")

        # SQLAlchemy Engine
        engine = create_engine(
            f"mysql+mysqlconnector://"
            f"{DB_CONFIG['user']}:"
            f"{DB_CONFIG['password']}@"
            f"{DB_CONFIG['host']}/"
            f"{DB_NAME}"
        )

        # Insert Data
        df.to_sql(
            name="students",
            con=engine,
            if_exists="append",
            index=False
        )

        print(
            f"\nSuccessfully inserted {len(df)} records into students table."
        )

        engine.dispose()

    except Exception as e:
        print(f"\nInsert error: {e}")
        exit(1)


# =========================
# MAIN
# =========================

if __name__ == "__main__":
    create_database()
    create_table()
    insert_data()