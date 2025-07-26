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

    def setup_camera(self):
        """Setup camera source"""
        print("\nSelect camera source:")
        print("1. Local webcam (default)")
        print("2. IP camera (use your mobile device)")
        source_choice = input("Enter 1 or 2: ").strip()
        
        if source_choice == '2':
            print("\nTo use your mobile device, install an IP camera app (e.g., IP Webcam for Android, EpocCam for iOS).\n" 
                  "Connect your phone and computer to the same Wi-Fi network. Start the camera server on your phone and enter the video stream URL below (e.g., http://192.168.1.100:8080/video):")
            ip_camera_url = input("Enter the IP camera stream URL: ").strip()
            cap = cv2.VideoCapture(ip_camera_url)
        else:
            cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("[ERROR] Could not open the selected camera source.")
            return None
        
        return cap
    
     def detect_omr_sheet(self, frame):
        """Detect if an OMR sheet is present in the frame"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            edged = cv2.Canny(blurred, 75, 200)
            
            # Find contours
            cnts = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cnts = imutils.grab_contours(cnts)
            
            if len(cnts) > 0:
                # Sort contours by area
                cnts = sorted(cnts, key=cv2.contourArea, reverse=True)
                
                for c in cnts:
                    peri = cv2.arcLength(c, True)
                    approx = cv2.approxPolyDP(c, 0.02 * peri, True)
                    
                    # Check if it's a quadrilateral (potential OMR sheet)
                    if len(approx) == 4:
                        # Calculate area ratio to ensure it's large enough
                        area = cv2.contourArea(c)
                        frame_area = frame.shape[0] * frame.shape[1]
                        area_ratio = area / frame_area
                        
                        # Check if the detected area is reasonable (not too small, not too large)
                        if 0.1 < area_ratio < 0.9:
                            return True, approx
            
            return False, None
            
        except Exception as e:
            print(f"Error in OMR detection: {e}")
            return False, None