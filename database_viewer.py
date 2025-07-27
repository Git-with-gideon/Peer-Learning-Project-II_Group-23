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
    print(f"STUDENT PERFORMANCE - ID: {student_id}")
    print_separator()
    
    try:
        results = db.get_student_results(student_id)
        
        if not results:
            print(f"No results found for student {student_id}")
            return
        
        # Group by student name
        student_name = results[0]['student_name']
        print(f"Student Name: {student_name}")
        print(f"Student ID: {student_id}")
        print(f"Total Assignments: {len(results)}")
        
        total_score = sum(r['score'] for r in results)
        avg_score = total_score / len(results)
        print(f"Average Score: {avg_score:.2f}%")
        
        print(f"\nAssignment History:")
        for result in results:
            print(f"  {result['assignment_name']}: {result['score']:.2f}% ({result['processed_at']})")
        
    except Exception as e:
        print(f"Error viewing student performance: {e}")

def view_session_details(db, session_id):
    """View detailed results for a specific grading session"""
    print_separator()
    print(f"SESSION DETAILS - ID: {session_id}")
    print_separator()
    
    try:
        session = db.get_grading_session(session_id)
        if not session:
            print(f"Session with ID {session_id} not found.")
            return
        
        print(f"Student: {session['student_name']} (ID: {session['student_id']})")
        print(f"Assignment: {session['assignment_name']}")
        print(f"Score: {session['score']:.2f}%")
        print(f"Correct Answers: {session['correct_answers']}/{session['total_questions']}")
        print(f"Processed: {session['processed_at']}")
        
        if session['image_path']:
            print(f"Image: {session['image_path']}")
        
        # Get detailed question results
        detailed_results = db.get_detailed_results(session_id)
        if detailed_results:
            print(f"\nQuestion-by-Question Results:")
            for result in detailed_results:
                status = "✓" if result['is_correct'] else "✗"
                print(f"  Q{result['question_number']}: {result['student_answer']} "
                      f"(Correct: {result['correct_answer']}) {status}")
        
    except Exception as e:
        print(f"Error viewing session details: {e}")

def export_data_menu(db):
    """Menu for data export options"""
    print_separator()
    print("DATA EXPORT OPTIONS")
    print_separator()
    
    try:
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()
        
        # Get all assignments
        cursor.execute('SELECT id, assignment_name FROM assignments ORDER BY assignment_name')
        assignments = cursor.fetchall()
        
        if not assignments:
            print("No assignments available for export.")
            return
        
        print("Available assignments for export:")
        for assignment in assignments:
            print(f"  {assignment[0]}: {assignment[1]}")
        
        assignment_id = input("\nEnter assignment ID to export (or press Enter to cancel): ").strip()
        if not assignment_id:
            return
        
        try:
            assignment_id = int(assignment_id)
            filename = db.export_results_csv(assignment_id)
            if filename:
                print(f"Data exported successfully to: {filename}")
            else:
                print("Export failed.")
        except ValueError:
            print("Invalid assignment ID.")
        
        conn.close()
        
    except Exception as e:
        print(f"Error in export menu: {e}")

def main():
    """Main database viewer interface"""
    print("OptiGrade Database Viewer")
    print("=" * 60)
    
    # Initialize database
    db = OptiGradeDatabase()
    
    while True:
        print("\n" + "=" * 60)
        print("DATABASE VIEWER MENU")
        print("=" * 60)
        print("1. View All Assignments")
        print("2. View Assignment Details")
        print("3. View Recent Grading Sessions")
        print("4. View Student Performance")
        print("5. View Session Details")
        print("6. Export Data to CSV")
        print("7. View Database Statistics")
        print("8. Exit")
        
        choice = input("\nSelect an option (1-8): ").strip()
        
        if choice == '1':
            view_all_assignments(db)
        
        elif choice == '2':
            assignment_id = input("Enter assignment ID: ").strip()
            if assignment_id:
                try:
                    view_assignment_details(db, int(assignment_id))
                except ValueError:
                    print("Invalid assignment ID.")
        
        elif choice == '3':
            limit = input("Enter number of recent sessions to view (default 10): ").strip()
            try:
                limit = int(limit) if limit else 10
                view_recent_sessions(db, limit)
            except ValueError:
                print("Invalid number.")
        
        elif choice == '4':
            student_id = input("Enter student ID: ").strip()
            if student_id:
                view_student_performance(db, student_id)
        
        elif choice == '5':
            session_id = input("Enter session ID: ").strip()
            if session_id:
                try:
                    view_session_details(db, int(session_id))
                except ValueError:
                    print("Invalid session ID.")
        
        elif choice == '6':
            export_data_menu(db)
        
        elif choice == '7':
            print_separator()
            print("DATABASE STATISTICS")
            print_separator()
            
            stats = db.get_statistics()
            if stats and stats['total_sessions'] > 0:
                print(f"Total Grading Sessions: {stats['total_sessions']}")
                print(f"Overall Average Score: {stats['average_score']:.2f}%")
                print(f"Highest Score: {stats['max_score']:.2f}%")
                print(f"Lowest Score: {stats['min_score']:.2f}%")
                print(f"\nGrade Distribution:")
                print(f"  A (90-100%): {stats['a_grades']}")
                print(f"  B (80-89%): {stats['b_grades']}")
                print(f"  C (70-79%): {stats['c_grades']}")
                print(f"  D (60-69%): {stats['d_grades']}")
                print(f"  F (<60%): {stats['f_grades']}")
            else:
                print("No data available for statistics.")
        
        elif choice == '8':
            print("Thank you for using the OptiGrade Database Viewer!")
            break
        
        else:
            print("Invalid option. Please select 1-8.")

if __name__ == "__main__":
    main() 