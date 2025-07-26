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
        
