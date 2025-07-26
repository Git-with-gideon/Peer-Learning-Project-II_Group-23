import cv2
import numpy as np
import imutils
from imutils.perspective import four_point_transform
from imutils import contours
import os
import time
from datetime import datetime
from database_manager import OptiGradeDatabase

class OptiGradeFullyAuto:
    """Fully automatic OptiGrade application with continuous scanning and processing"""
    
    def __init__(self):
        self.db = OptiGradeDatabase()
        self.assignment_id = None
        self.answer_key = {}
        self.num_questions = 0
        self.is_scanning = False
        self.last_detection_time = 0
        self.detection_cooldown = 2.0  # Seconds between detections
        self.student_counter = 1  # Auto-incrementing student counter
        self.session_name = ""
    
    def setup_assignment(self):
        """Setup assignment configuration and save to database"""
        print("=" * 50)
        print("Welcome to OptiGrade Fully Automatic Scanner!")
        print("=" * 50)
        
        # Get assignment details
        self.session_name = input("Enter assignment name: ").strip()
        if not self.session_name:
            self.session_name = f"Assignment_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        while True:
            try:
                num_input = input("How many questions do you plan to grade? ").strip()
                self.num_questions = int(num_input)
                if self.num_questions <= 0:
                    print("Please enter a positive number of questions.")
                    continue
                break
            except ValueError:
                print("Please enter a valid number (e.g., 5, 10, 20).")
        
        print(f"\nInput the correct answer for each question (A-E):")
        for i in range(self.num_questions):
            while True:
                ans = input(f"{i+1}. ").strip().upper()
                if ans in ['A', 'B', 'C', 'D', 'E']:
                    self.answer_key[i] = 'ABCDE'.index(ans)
                    break
                else:
                    print("Please enter a valid option (A, B, C, D, or E).")
          
        # Save assignment to database
        self.assignment_id = self.db.save_assignment(self.session_name, self.num_questions, self.answer_key)
        
        if self.assignment_id:
            print(f"\nAssignment '{self.session_name}' saved with ID: {self.assignment_id}")
        else:
            print("Error saving assignment to database. Continuing without database storage.")
    