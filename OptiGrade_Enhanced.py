import cv2
import numpy as np
import imutils
from imutils.perspective import four_point_transform
from imutils import contours
import os
from datetime import datetime
from database_manager import OptiGradeDatabase

class OptiGradeEnhanced:
    """Enhanced OptiGrade application with database integration"""
    
    def __init__(self):
        self.db = OptiGradeDatabase()
        self.assignment_id = None
        self.answer_key = {}
        self.num_questions = 0
        
    def setup_assignment(self):
        """Setup assignment configuration and save to database"""
        print("=" * 50)
        print("Welcome to OptiGrade Enhanced!")
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
    
    def capture_omr_sheet(self, cap):
        """Capture OMR sheet from camera"""
        print("\nAlright, begin scanning! Press 's' to scan when the OMR sheet is in view, or 'q' to quit.")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                print("[ERROR] Failed to grab frame.")
                break
            cv2.imshow("Live Camera - Place OMR Sheet", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('s'):
                image = frame.copy()
                break
            elif key == ord('q'):
                cap.release()
                cv2.destroyAllWindows()
                return None
        
        cap.release()
        cv2.destroyAllWindows()
        return image
    
    def process_omr_sheet(self, image):
        """Process OMR sheet and detect answers"""
        # Preprocess
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edged = cv2.Canny(blurred, 75, 200)
        
        # Find document contour
        cnts = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)
        docCnt = None
        
        if len(cnts) > 0:
            cnts = sorted(cnts, key=cv2.contourArea, reverse=True)
            for c in cnts:
                peri = cv2.arcLength(c, True)
                approx = cv2.approxPolyDP(c, 0.02 * peri, True)
                if len(approx) == 4:
                    docCnt = approx
                    break
        
        if docCnt is None:
            print("[ERROR] Could not find OMR sheet in the image.")
            return None, None, None
        
        # Transform perspective
        paper = four_point_transform(image, docCnt.reshape(4, 2))
        warped = four_point_transform(gray, docCnt.reshape(4, 2))
        
        # Threshold
        thresh = cv2.threshold(warped, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
        
        # Debug option
        show_thresh = input("Show thresholded image for debugging? (y/n): ").strip().lower()
        if show_thresh == 'y':
            cv2.imshow("Thresholded", thresh)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
        
        # Find bubbles
        cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)
        questionCnts = []
        
        for c in cnts:
            (x, y, w, h) = cv2.boundingRect(c)
            ar = w / float(h)
            if w >= 20 and h >= 20 and 0.9 <= ar <= 1.1:
                questionCnts.append(c)
        
        if len(questionCnts) < self.num_questions * 5:
            print(f"[WARNING] Detected {len(questionCnts)} bubbles, expected at least {self.num_questions * 5}.")
            if len(questionCnts) == 0:
                print("[ERROR] No bubbles detected. Please check the OMR sheet placement, lighting, and camera focus.")
                return None, None, None
        
        return paper, thresh, questionCnts
    
    def grade_answers(self, paper, thresh, questionCnts):
        """Grade the answers and return results"""
        questionCnts = contours.sort_contours(questionCnts, method="top-to-bottom")[0]
        correct = 0
        detailed_results = []
        
        for (q, i) in enumerate(np.arange(0, len(questionCnts), 5)):
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
            
            if k is not None:
                correct_answer = 'ABCDE'[k]
                student_answer = 'ABCDE'[bubbled[1]] if bubbled else None
                is_correct = bubbled is not None and k == bubbled[1]
                
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
    
    def save_result_image(self, paper, score):
        """Save the result image with score overlay"""
        # Create images directory if it doesn't exist
        os.makedirs('images', exist_ok=True)
        
        # Add score text to image
        cv2.putText(paper, f"{score:.2f}%", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
        
        # Save image with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        image_path = f"images/omr_result_{timestamp}.jpg"
        cv2.imwrite(image_path, paper)
        
        return image_path
    
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
    
    def run_grading_session(self):
        """Run a complete grading session"""
        # Setup assignment
        self.setup_assignment()
        
        # Setup camera
        cap = self.setup_camera()
        if cap is None:
            return
        
        # Capture OMR sheet
        image = self.capture_omr_sheet(cap)
        if image is None:
            return
        
        # Process OMR sheet
        result = self.process_omr_sheet(image)
        if result[0] is None:
            return
        
        paper, thresh, questionCnts = result
        
        # Grade answers
        result = self.grade_answers(paper, thresh, questionCnts)
        if result[0] is None:
            return
        
        score, correct, detailed_results, paper = result
        
        # Get student information
        student_name, student_id = self.get_student_info()
        
        # Save result image
        image_path = self.save_result_image(paper, score)
        
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
        
        # Show result image
        cv2.imshow("OMR Result", paper)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        
        print(f"\nResult image saved to: {image_path}")
    
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
    app = OptiGradeEnhanced()
    
    while True:
        print("\n" + "=" * 50)
        print("OPTIGRADE ENHANCED MENU")
        print("=" * 50)
        print("1. Start New Grading Session")
        print("2. View Assignment Statistics")
        print("3. Export Results to CSV")
        print("4. View Student Results")
        print("5. Exit")
        
        choice = input("\nSelect an option (1-5): ").strip()
        
        if choice == '1':
            app.run_grading_session()
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
            print("Thank you for using OptiGrade Enhanced!")
            break
        else:
            print("Invalid option. Please select 1-5.")

if __name__ == "__main__":
    main() 