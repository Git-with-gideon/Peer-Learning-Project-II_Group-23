import sqlite3
import os
from datetime import datetime

def create_database():
    """Create the OptiGrade database with necessary tables"""
    
    # Create database directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    conn = sqlite3.connect('data/optigrade.db')
    cursor = conn.cursor()
    
    # Create assignments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            assignment_name TEXT NOT NULL,
            num_questions INTEGER NOT NULL,
            answer_key TEXT NOT NULL,  -- JSON string of answer key
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create grading_sessions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS grading_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            assignment_id INTEGER,
            student_name TEXT,
            student_id TEXT,
            score REAL NOT NULL,
            correct_answers INTEGER NOT NULL,
            total_questions INTEGER NOT NULL,
            image_path TEXT,  -- Path to saved OMR image
            processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (assignment_id) REFERENCES assignments (id)
        )
    ''')
    
    # Create detailed_results table for individual question results
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS detailed_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            question_number INTEGER NOT NULL,
            correct_answer TEXT NOT NULL,
            student_answer TEXT,
            is_correct BOOLEAN NOT NULL,
            FOREIGN KEY (session_id) REFERENCES grading_sessions (id)
        )
    ''')
    
    # Create indexes for better performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_assignment ON grading_sessions(assignment_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_student ON grading_sessions(student_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_detailed_session ON detailed_results(session_id)')
    
    conn.commit()
    conn.close()
    
    print("Database created successfully!")
    print("Tables created:")
    print("- assignments: Store assignment configurations")
    print("- grading_sessions: Store grading session results")
    print("- detailed_results: Store individual question results")

if __name__ == "__main__":
    create_database() 