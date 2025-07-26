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
                
    def get_grading_session(self, session_id: int) -> Optional[Dict]:
        """Retrieve grading session by ID"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT gs.*, a.assignment_name 
                FROM grading_sessions gs
                JOIN assignments a ON gs.assignment_id = a.id
                WHERE gs.id = ?
            ''', (session_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return dict(row)
            return None
            
        except Exception as e:
            print(f"Error retrieving grading session: {e}")
            return None
    
    def get_student_results(self, student_id: str) -> List[Dict]:
        """Get all results for a specific student"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT gs.*, a.assignment_name 
                FROM grading_sessions gs
                JOIN assignments a ON gs.assignment_id = a.id
                WHERE gs.student_id = ?
                ORDER BY gs.processed_at DESC
            ''', (student_id,))
            
            results = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            return results
            
        except Exception as e:
            print(f"Error retrieving student results: {e}")
            return []
    
    def get_assignment_results(self, assignment_id: int) -> List[Dict]:
        """Get all results for a specific assignment"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT gs.*, a.assignment_name 
                FROM grading_sessions gs
                JOIN assignments a ON gs.assignment_id = a.id
                WHERE gs.assignment_id = ?
                ORDER BY gs.processed_at DESC
            ''', (assignment_id,))
            
            results = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            return results
            
        except Exception as e:
            print(f"Error retrieving assignment results: {e}")
            return []
    
    def get_detailed_results(self, session_id: int) -> List[Dict]:
        """Get detailed question-by-question results for a session"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM detailed_results 
                WHERE session_id = ?
                ORDER BY question_number
            ''', (session_id,))
            
            results = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            return results
                        
        except Exception as e:
            print(f"Error retrieving detailed results: {e}")
            return []
    
    def get_statistics(self, assignment_id: int = None) -> Dict:
        """Get grading statistics"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            if assignment_id:
                # Statistics for specific assignment
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total_sessions,
                        AVG(score) as average_score,
                        MIN(score) as min_score,
                        MAX(score) as max_score,
                        COUNT(CASE WHEN score >= 90 THEN 1 END) as a_grades,
                        COUNT(CASE WHEN score >= 80 AND score < 90 THEN 1 END) as b_grades,
                        COUNT(CASE WHEN score >= 70 AND score < 80 THEN 1 END) as c_grades,
                        COUNT(CASE WHEN score >= 60 AND score < 70 THEN 1 END) as d_grades,
                        COUNT(CASE WHEN score < 60 THEN 1 END) as f_grades
                    FROM grading_sessions 
                    WHERE assignment_id = ?
                ''', (assignment_id,))
            else:
                # Overall statistics
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total_sessions,
                        AVG(score) as average_score,
                        MIN(score) as min_score,
                        MAX(score) as max_score,
                        COUNT(CASE WHEN score >= 90 THEN 1 END) as a_grades,
                        COUNT(CASE WHEN score >= 80 AND score < 90 THEN 1 END) as b_grades,
                        COUNT(CASE WHEN score >= 70 AND score < 80 THEN 1 END) as c_grades,
                        COUNT(CASE WHEN score >= 60 AND score < 70 THEN 1 END) as d_grades,
                        COUNT(CASE WHEN score < 60 THEN 1 END) as f_grades
                    FROM grading_sessions
                ''')
            
            stats = dict(cursor.fetchone())
            conn.close()
            
            return stats
                     
        except Exception as e:
            print(f"Error retrieving statistics: {e}")
            return {}
    
    def export_results_csv(self, assignment_id: int, filename: str = None) -> str:
        """Export assignment results to CSV"""
        try:
            import csv
            
            if not filename:
                filename = f"assignment_{assignment_id}_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            results = self.get_assignment_results(assignment_id)
            
            with open(filename, 'w', newline='') as csvfile:
                fieldnames = ['student_id', 'student_name', 'score', 'correct_answers', 
                             'total_questions', 'processed_at', 'assignment_name']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for result in results:
                    writer.writerow(result)
            
            print(f"Results exported to {filename}")
            return filename
            
        except Exception as e:
            print(f"Error exporting results: {e}")
            return None 
            
