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
