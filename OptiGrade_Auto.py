import cv2
import numpy as np
import imutils
from imutils.perspective import four_point_transform
from imutils import contours
import os
import time
from datetime import datetime
from database_manager import OptiGradeDatabase

class OptiGradeAuto:
    """Enhanced OptiGrade application with automatic OMR detection and processing"""
    
    def __init__(self):
        self.db = OptiGradeDatabase()
        self.assignment_id = None
        self.answer_key = {}
        self.num_questions = 0
        self.is_scanning = False
        self.last_detection_time = 0
        self.detection_cooldown = 3.0  # Seconds between detections
        self.confidence_threshold = 0.7  # Minimum confidence for detection
        
    def setup_assignment(self):
        """Setup assignment configuration and save to database"""
        print("=" * 50)
        print("Welcome to OptiGrade Auto Scanner!")
        print("=" * 50)
        
        # Get assignment details
        assignment_name = input("Enter assignment name: ").strip()
        if not assignment_name:
            assignment_name = f"Assignment_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.num_questions = int(input("How many questions do you plan to grade? "))
        
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
        self.assignment_id = self.db.save_assignment(assignment_name, self.num_questions, self.answer_key)
        
        if self.assignment_id:
            print(f"\nAssignment '{assignment_name}' saved with ID: {self.assignment_id}")
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
    
    def process_omr_sheet(self, image, docCnt):
        """Process OMR sheet and detect answers"""
        try:
            # Transform perspective
            paper = four_point_transform(image, docCnt.reshape(4, 2))
            gray = cv2.cvtColor(paper, cv2.COLOR_BGR2GRAY)
            warped = four_point_transform(gray, docCnt.reshape(4, 2))
            
            # Threshold
            thresh = cv2.threshold(warped, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
            
            # Find bubbles
            cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cnts = imutils.grab_contours(cnts)
            questionCnts = []
            
            for c in cnts:
                (x, y, w, h) = cv2.boundingRect(c)
                ar = w / float(h)
                if w >= 20 and h >= 20 and 0.9 <= ar <= 1.1:
                    questionCnts.append(c)
            
            # Check if we have enough bubbles
            expected_bubbles = self.num_questions * 5
            if len(questionCnts) < expected_bubbles * 0.8:  # Allow 20% tolerance
                return None, None, None, f"Expected {expected_bubbles} bubbles, found {len(questionCnts)}"
            
            return paper, thresh, questionCnts, None
            
        except Exception as e:
            return None, None, None, f"Error processing OMR: {e}"
    
    def grade_answers(self, paper, thresh, questionCnts):
        """Grade the answers and return results"""
        try:
            questionCnts = contours.sort_contours(questionCnts, method="top-to-bottom")[0]
            correct = 0
            detailed_results = []
            
            for (q, i) in enumerate(np.arange(0, len(questionCnts), 5)):
                if i + 5 > len(questionCnts):
                    break
                    
                cnts = contours.sort_contours(questionCnts[i:i + 5])[0]
                bubbled = None
                
                for (j, c) in enumerate(cnts):
                    mask = np.zeros(thresh.shape, dtype="uint8")
                    cv2.drawContours(mask, [c], -1, 255, -1)
                    mask = cv2.bitwise_and(thresh, thresh, mask=mask)
                    total = cv2.countNonZero(mask)
                    if bubbled is None or total > bubbled[0]:
                        bubbled = (total, j)
                
                color = (0, 0, 255)
                k = self.answer_key.get(q, None)
                
                if k is not None and bubbled is not None:
                    correct_answer = 'ABCDE'[k]
                    student_answer = 'ABCDE'[bubbled[1]]
                    is_correct = k == bubbled[1]
                    
                    if is_correct:
                        color = (0, 255, 0)
                        correct += 1
                    
                    # Store detailed result
                    detailed_results.append({
                        'question_number': q + 1,
                        'correct_answer': correct_answer,
                        'student_answer': student_answer,
                        'is_correct': is_correct
                    })
                    
                    cv2.drawContours(paper, [cnts[k]], -1, color, 3)
            
            score = (correct / float(self.num_questions)) * 100
            return score, correct, detailed_results, paper
            
        except Exception as e:
            print(f"Error grading answers: {e}")
            return None, None, None, None
    
    def save_result_image(self, paper, score):
        """Save the result image with score overlay"""
        try:
            # Create images directory if it doesn't exist
            os.makedirs('images', exist_ok=True)
            
            # Add score text to image
            cv2.putText(paper, f"{score:.2f}%", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
            
            # Save image with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            image_path = f"images/omr_result_{timestamp}.jpg"
            cv2.imwrite(image_path, paper)
            
            return image_path
            
        except Exception as e:
            print(f"Error saving image: {e}")
            return None
    
    def get_student_info(self):
        """Get student information for database storage"""
        print("\n" + "=" * 30)
        print("STUDENT INFORMATION")
        print("=" * 30)
        
        student_name = input("Enter student name: ").strip()
        if not student_name:
            student_name = "Unknown"
        
        student_id = input("Enter student ID: ").strip()
        if not student_id:
            student_id = f"STU_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return student_name, student_id
    
    def auto_scan_loop(self, cap):
        """Main auto-scanning loop"""
        print("\n" + "=" * 50)
        print("AUTO SCANNING MODE")
        print("=" * 50)
        print("Place OMR sheets in front of the camera.")
        print("The system will automatically detect and process them.")
        print("Press 'q' to quit, 'p' to pause/resume scanning.")
        print("=" * 50)
        
        self.is_scanning = True
        detection_count = 0
        
        while self.is_scanning:
            ret, frame = cap.read()
            if not ret:
                print("[ERROR] Failed to grab frame.")
                break
            
            # Create display frame
            display_frame = frame.copy()
            
            # Check if enough time has passed since last detection
            current_time = time.time()
            if current_time - self.last_detection_time > self.detection_cooldown:
                # Try to detect OMR sheet
                detected, docCnt = self.detect_omr_sheet(frame)
                
                if detected:
                    print(f"\n[INFO] OMR sheet detected! Processing...")
                    
                    # Process the detected sheet
                    result = self.process_omr_sheet(frame, docCnt)
                    if result[0] is not None:
                        paper, thresh, questionCnts, error = result
                        
                        # Grade the answers
                        grade_result = self.grade_answers(paper, thresh, questionCnts)
                        if grade_result[0] is not None:
                            score, correct, detailed_results, graded_paper = grade_result
                            
                            # Get student information
                            student_name, student_id = self.get_student_info()
                            
                            # Save result image
                            image_path = self.save_result_image(graded_paper, score)
                            
                            # Display results
                            print(f"\n" + "=" * 30)
                            print("GRADING RESULTS")
                            print("=" * 30)
                            print(f"Student: {student_name} (ID: {student_id})")
                            print(f"Score: {score:.2f}%")
                            print(f"Correct Answers: {correct}/{self.num_questions}")
                            
                            # Show detailed results
                            print(f"\nDetailed Results:")
                            for result in detailed_results:
                                status = "✓" if result['is_correct'] else "✗"
                                print(f"Q{result['question_number']}: {result['student_answer']} (Correct: {result['correct_answer']}) {status}")
                            
                            # Save to database
                            if self.assignment_id:
                                session_id = self.db.save_grading_result(
                                    assignment_id=self.assignment_id,
                                    student_name=student_name,
                                    student_id=student_id,
                                    score=score,
                                    correct_answers=correct,
                                    total_questions=self.num_questions,
                                    image_path=image_path,
                                    detailed_results=detailed_results
                                )
                                
                                if session_id:
                                    print(f"\nResults saved to database with session ID: {session_id}")
                                else:
                                    print("\nError saving results to database.")
                            
                            detection_count += 1
                            print(f"\n[SUCCESS] Sheet {detection_count} processed successfully!")
                            print("Place next sheet or press 'q' to quit.")
                            
                            # Update last detection time
                            self.last_detection_time = current_time
                            
                        else:
                            print(f"[ERROR] Failed to grade answers.")
                    else:
                        print(f"[ERROR] Failed to process OMR sheet: {result[3]}")
                    
                    # Update last detection time even if processing failed
                    self.last_detection_time = current_time
            
            # Draw detection status on frame
            status_text = f"Scanning: {'ACTIVE' if self.is_scanning else 'PAUSED'}"
            cv2.putText(display_frame, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(display_frame, f"Detections: {detection_count}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(display_frame, "Press 'q' to quit, 'p' to pause", (10, display_frame.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Show the frame
            cv2.imshow("OptiGrade Auto Scanner", display_frame)
            
            # Handle key presses
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('p'):
                self.is_scanning = not self.is_scanning
                status = "RESUMED" if self.is_scanning else "PAUSED"
                print(f"\n[INFO] Scanning {status}")
        
        cap.release()
        cv2.destroyAllWindows()
        print(f"\n[INFO] Auto scanning completed. Total sheets processed: {detection_count}")
    
    def run_auto_grading_session(self):
        """Run a complete auto-grading session"""
        # Setup assignment
        self.setup_assignment()
        
        # Setup camera
        cap = self.setup_camera()
        if cap is None:
            return
        
        # Start auto scanning
        self.auto_scan_loop(cap)
    
    def show_statistics(self):
        """Show grading statistics"""
        if not self.assignment_id:
            print("No assignment selected. Please run a grading session first.")
            return
        
        stats = self.db.get_statistics(self.assignment_id)
        if stats:
            print("\n" + "=" * 40)
            print("ASSIGNMENT STATISTICS")
            print("=" * 40)
            print(f"Total Sessions: {stats['total_sessions']}")
            print(f"Average Score: {stats['average_score']:.2f}%")
            print(f"Highest Score: {stats['max_score']:.2f}%")
            print(f"Lowest Score: {stats['min_score']:.2f}%")
            print(f"\nGrade Distribution:")
            print(f"A (90-100%): {stats['a_grades']}")
            print(f"B (80-89%): {stats['b_grades']}")
            print(f"C (70-79%): {stats['c_grades']}")
            print(f"D (60-69%): {stats['d_grades']}")
            print(f"F (<60%): {stats['f_grades']}")
        else:
            print("No statistics available.")

def main():
    """Main application entry point"""
    app = OptiGradeAuto()
    
    while True:
        print("\n" + "=" * 50)
        print("OPTIGRADE AUTO SCANNER MENU")
        print("=" * 50)
        print("1. Start Auto Grading Session")
        print("2. View Assignment Statistics")
        print("3. Export Results to CSV")
        print("4. View Student Results")
        print("5. Exit")
        
        choice = input("\nSelect an option (1-5): ").strip()
        
        if choice == '1':
            app.run_auto_grading_session()
        elif choice == '2':
            app.show_statistics()
        elif choice == '3':
            if app.assignment_id:
                filename = app.db.export_results_csv(app.assignment_id)
                if filename:
                    print(f"Results exported to: {filename}")
            else:
                print("No assignment selected. Please run a grading session first.")
        elif choice == '4':
            student_id = input("Enter student ID to view results: ").strip()
            if student_id:
                results = app.db.get_student_results(student_id)
                if results:
                    print(f"\nResults for student {student_id}:")
                    for result in results:
                        print(f"Assignment: {result['assignment_name']}, Score: {result['score']:.2f}%")
                else:
                    print(f"No results found for student {student_id}")
        elif choice == '5':
            print("Thank you for using OptiGrade Auto Scanner!")
            break
        else:
            print("Invalid option. Please select 1-5.")

if __name__ == "__main__":
    main() 