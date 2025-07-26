import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple

class OptiGradeDatabase:
    """Database manager for OptiGrade application"""
    
    def __init__(self, db_path: str = 'data/optigrade.db'):
        self.db_path = db_path
        self._ensure_database_exists()
    
    def _ensure_database_exists(self):
        """Ensure database and tables exist"""
        if not os.path.exists(self.db_path):
            from database_setup import create_database
            create_database()
               
    def _get_connection(self):
        """Get database connection with proper configuration"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        return conn
    
    def save_assignment(self, assignment_name: str, num_questions: int, answer_key: Dict[int, int]) -> int:
        """Save a new assignment configuration"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Convert answer key to JSON string
            answer_key_json = json.dumps(answer_key)
            
            cursor.execute('''
                INSERT INTO assignments (assignment_name, num_questions, answer_key)
                VALUES (?, ?, ?)
            ''', (assignment_name, num_questions, answer_key_json))
            
            assignment_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            print(f"Assignment '{assignment_name}' saved with ID: {assignment_id}")
            return assignment_id
            
        except Exception as e:
            print(f"Error saving assignment: {e}")
            return None
    
    def save_grading_result(self, assignment_id: int, student_name: str, student_id: str,
                          score: float, correct_answers: int, total_questions: int,
                          image_path: str = None, detailed_results: List[Dict] = None) -> int:
        """Save a grading session result"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
                       
            # Save main grading session
            cursor.execute('''
                INSERT INTO grading_sessions 
                (assignment_id, student_name, student_id, score, correct_answers, total_questions, image_path)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (assignment_id, student_name, student_id, score, correct_answers, total_questions, image_path))
            
            session_id = cursor.lastrowid
            
            # Save detailed results if provided
            if detailed_results:
                for result in detailed_results:
                    cursor.execute('''
                        INSERT INTO detailed_results 
                        (session_id, question_number, correct_answer, student_answer, is_correct)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (session_id, result['question_number'], result['correct_answer'], 
                         result['student_answer'], result['is_correct']))
            
            conn.commit()
            conn.close()
            
            print(f"Grading result saved for student {student_name} (ID: {student_id})")
            return session_id
            
        except Exception as e:
            print(f"Error saving grading result: {e}")
            return None
    
    def get_assignment(self, assignment_id: int) -> Optional[Dict]:
        """Retrieve assignment by ID"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM assignments WHERE id = ?', (assignment_id,))
            row = cursor.fetchone()
            
            conn.close()
            
            if row:
                assignment = dict(row)
                assignment['answer_key'] = json.loads(assignment['answer_key'])
                return assignment
            return None
            
        except Exception as e:
            print(f"Error retrieving assignment: {e}")
            return None
