#!/usr/bin/env python3
"""
Database Viewer for OptiGrade
A utility to explore and query the OptiGrade database
"""

import sqlite3
import json
from datetime import datetime
from database_manager import OptiGradeDatabase

def print_separator():
    """Print a separator line"""
    print("=" * 60)

def view_all_assignments(db):
    """View all assignments in the database"""
    print_separator()
    print("ALL ASSIGNMENTS")
    print_separator()
    
    try:
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, assignment_name, num_questions, created_at, 
                   (SELECT COUNT(*) FROM grading_sessions WHERE assignment_id = assignments.id) as session_count
            FROM assignments 
            ORDER BY created_at DESC
        ''')
        
        assignments = cursor.fetchall()
        
        if not assignments:
            print("No assignments found in database.")
            return
        
        for assignment in assignments:
            print(f"ID: {assignment[0]}")
            print(f"Name: {assignment[1]}")
            print(f"Questions: {assignment[2]}")
            print(f"Created: {assignment[3]}")
            print(f"Sessions: {assignment[4]}")
            print("-" * 40)
        
        conn.close()
        
    except Exception as e:
        print(f"Error viewing assignments: {e}")

def view_assignment_details(db, assignment_id):
    """View detailed information about a specific assignment"""
    print_separator()
    print(f"ASSIGNMENT DETAILS - ID: {assignment_id}")
    print_separator()
    
    try:
        assignment = db.get_assignment(assignment_id)
        if not assignment:
            print(f"Assignment with ID {assignment_id} not found.")
            return
        
        print(f"Name: {assignment['assignment_name']}")
        print(f"Questions: {assignment['num_questions']}")
        print(f"Created: {assignment['created_at']}")
        print(f"Updated: {assignment['updated_at']}")
        
        print(f"\nAnswer Key:")
        for q_num, ans_idx in assignment['answer_key'].items():
            print(f"  Q{q_num + 1}: {chr(65 + ans_idx)}")  # Convert 0-4 to A-E
        
        # Get statistics
        stats = db.get_statistics(assignment_id)
        if stats and stats['total_sessions'] > 0:
            print(f"\nStatistics:")
            print(f"  Total Sessions: {stats['total_sessions']}")
            print(f"  Average Score: {stats['average_score']:.2f}%")
            print(f"  Highest Score: {stats['max_score']:.2f}%")
            print(f"  Lowest Score: {stats['min_score']:.2f}%")
        
    except Exception as e:
        print(f"Error viewing assignment details: {e}")

def view_recent_sessions(db, limit=10):
    """View recent grading sessions"""
    print_separator()
    print(f"RECENT GRADING SESSIONS (Last {limit})")
    print_separator()
    
    try:
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT gs.id, gs.student_name, gs.student_id, gs.score, 
                   gs.correct_answers, gs.total_questions, gs.processed_at,
                   a.assignment_name
            FROM grading_sessions gs
            JOIN assignments a ON gs.assignment_id = a.id
            ORDER BY gs.processed_at DESC
            LIMIT ?
        ''', (limit,))
        
        sessions = cursor.fetchall()
        
        if not sessions:
            print("No grading sessions found.")
            return
        
        for session in sessions:
            print(f"Session ID: {session[0]}")
            print(f"Student: {session[1]} (ID: {session[2]})")
            print(f"Assignment: {session[7]}")
            print(f"Score: {session[3]:.2f}% ({session[4]}/{session[5]} correct)")
            print(f"Processed: {session[6]}")
            print("-" * 40)
        
        conn.close()
        
    except Exception as e:
        print(f"Error viewing recent sessions: {e}")

def view_student_performance(db, student_id):
    """View performance history for a specific student"""
    print_separator()
