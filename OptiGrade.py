import cv2
import numpy as np
import os
import time
from datetime import datetime
# Assuming database_manager.py exists and handles database operations
# You would need to ensure this file is present and correctly configured.
from database_manager import OptiGradeDatabase 

class OptiGradeFullyAuto:
    """
    Fully automatic OptiGrade application with continuous scanning and processing,
    using simplified OMR detection and grading logic.
    """

    def __init__(self):
        self.db = OptiGradeDatabase()
        self.assignment_id = None
        self.answer_key = {}
        self.num_questions = 0
        self.num_options = 5  # Default to A, B, C, D, E
        self.last_detection_time = 0
        self.detection_cooldown = 2.0  # Seconds between processing attempts
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
        
        while True:
            try:
                num_options_input = input("How many options per question (e.g., 4 for A,B,C,D or 5 for A,B,C,D,E): ").strip()
                self.num_options = int(num_options_input)
                if self.num_options <= 0 or self.num_options > 5: # Limiting to 5 options (A-E)
                    print("Please enter a valid number of options (1-5).")
                    continue
                break
            except ValueError:
                print("Please enter a valid number (e.g., 4, 5).")

        print(f"\nInput the correct answer for each question (A-{chr(65 + self.num_options - 1)}):")
        valid_options_chars = [chr(65 + i) for i in range(self.num_options)]
        for i in range(self.num_questions):
            while True:
                ans = input(f"{i+1}. ").strip().upper()
                if ans in valid_options_chars:
                    # Store as character for simpler grading logic consistency with OptiGrade.py
                    self.answer_key[i] = ans 
                    break
                else:
                    print(f"Please enter a valid option ({', '.join(valid_options_chars)}).")

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

    def process_omr_sheet_simplified(self, frame):
        """
        Process OMR sheet to detect marked answers using simplified logic from OptiGrade.py.
        Returns list of detected answers (A, B, C, D, E, etc.) or None if failed.
        """
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # Apply threshold to get binary image
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Filter contours to find potential bubbles
        bubbles = []
        for contour in contours:
            area = cv2.contourArea(contour)
            # Adjust these values based on your OMR sheet and camera setup
            if 100 < area < 5000: 
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = w / float(h)
                if 0.8 < aspect_ratio < 1.2:  # Roughly circular
                    bubbles.append((x, y, w, h, area))

        # Check if we found enough bubbles. Allow some tolerance.
        expected_min_bubbles = int(self.num_questions * self.num_options * 0.8) # 80% of expected
        if len(bubbles) < expected_min_bubbles:
            # print(f"Warning: Found {len(bubbles)} bubbles, expected at least {expected_min_bubbles}")
            return None

        # Sort bubbles by position (top to bottom, then left to right)
        # This is crucial for grouping bubbles into questions
        bubbles.sort(key=lambda b: (b[1] // 50, b[0])) # Group by approximate row (y // 50) then x

        # Group bubbles by questions
        detected_answers = []
        options_chars = [chr(65 + i) for i in range(self.num_options)]

        for q_idx in range(self.num_questions):
            # Attempt to get bubbles for the current question
            # This is a simplified approach and might need refinement for complex layouts
            question_bubbles_candidates = []
            
            # Heuristic: Find bubbles that are roughly on the same 'row' as the first bubble of the question
            # This part is a simplification and might need to be more robust
            if q_idx * self.num_options < len(bubbles):
                first_bubble_y = bubbles[q_idx * self.num_options][1]
                # Collect bubbles that are within a certain vertical range (e.g., 30 pixels)
                question_bubbles_candidates = [
                    b for b in bubbles if abs(b[1] - first_bubble_y) < 30
                ]
                # Sort these candidates by x-coordinate to get options in order (A, B, C, D, E)
                question_bubbles_candidates.sort(key=lambda b: b[0])
            
            # Take only the first 'num_options' bubbles for this question
            question_bubbles = question_bubbles_candidates[:self.num_options]

            if len(question_bubbles) < self.num_options:
                detected_answers.append('X')  # Not enough options detected for this question
                continue

            # Find the bubble with the most filled area (darkest) for the current question
            max_filled_intensity = 256 # Initialize with a value higher than max pixel intensity (255)
            selected_option_char = 'X'

            for i, (x, y, w, h, area) in enumerate(question_bubbles):
                if i < len(options_chars):
                    roi = gray[y:y+h, x:x+w]
                    if roi.size > 0:
                        # Calculate the average intensity in the bubble region
                        # Lower intensity means darker (more filled)
                        avg_intensity = np.mean(roi)
                        if avg_intensity < max_filled_intensity:
                            max_filled_intensity = avg_intensity
                            selected_option_char = options_chars[i]
            
            # A simple threshold to decide if a bubble is truly marked (e.g., avg intensity below 100)
            if max_filled_intensity < 100: # This threshold might need tuning
                detected_answers.append(selected_option_char)
            else:
                detected_answers.append('X') # Considered unmarked

        return detected_answers

    def grade_answers_simplified(self, detected_answers, answer_key):
        """
        Grade the detected answers against the answer key using simplified logic from OptiGrade.py.
        Returns score as percentage and number of correct answers.
        """
        correct_count = 0
        total_questions = len(answer_key) # Use the length of the answer key as total questions
        
        # Ensure detected_answers has enough elements to compare
        min_len = min(len(detected_answers), total_questions)

        for i in range(min_len):
            # Access answer key by index, as it's a list of characters
            if detected_answers[i] == answer_key[i]:
                correct_count += 1
        
        if total_questions == 0:
            score = 0.0
        else:
            score = (correct_count / float(total_questions)) * 100
        
        return score, correct_count

    def save_result_image(self, frame, score, student_id):
        """Save the result image with score overlay"""
        try:
            # Create images directory if it doesn't exist
            os.makedirs('images', exist_ok=True)

            # Create a copy to draw on
            display_image = frame.copy()
            
            # Add score text to image
            cv2.putText(display_image, f"Score: {score:.2f}%", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
            cv2.putText(display_image, f"Student ID: {student_id}", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            # Save image with timestamp and student ID
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            image_path = f"images/omr_result_{student_id}_{timestamp}.jpg"
            cv2.imwrite(image_path, display_image)

            return image_path

        except Exception as e:
            print(f"Error saving image: {e}")
            return None

    def auto_scan_loop(self, cap):
        """Main auto-scanning loop - fully automatic"""
        print("\n" + "=" * 50)
        print("FULLY AUTOMATIC SCANNING MODE")
        print("=" * 50)
        print("Place OMR sheets in front of the camera.")
        print("The system will automatically detect, process, and grade them.")
        print("Press 'q' to quit.")
        print("=" * 50)

        detection_count = 0

        while True: # Continuous scanning without pause/resume
            ret, frame = cap.read()
            if not ret:
                print("[ERROR] Failed to grab frame.")
                break

            # Create display frame
            display_frame = frame.copy()

            # Check if enough time has passed since last processing
            current_time = time.time()
            if current_time - self.last_detection_time > self.detection_cooldown:
                
                # Use the simplified processing function
                detected_answers = self.process_omr_sheet_simplified(frame)

                if detected_answers:
                    # Check if we have valid answers (not all 'X')
                    # This threshold can be adjusted
                    valid_answers_count = sum(1 for ans in detected_answers if ans != 'X')
                    if valid_answers_count >= self.num_questions * 0.5: # At least 50% of questions answered
                        detection_count += 1
                        self.last_detection_time = current_time

                        print(f"\n🎯 OMR Sheet #{detection_count} detected and processed!")
                        
                        # Grade the answers using the simplified grading function
                        # self.answer_key is a dictionary, convert to list of values for simplified grading
                        answer_key_list = [self.answer_key[i] for i in sorted(self.answer_key.keys())]
                        score, correct = self.grade_answers_simplified(detected_answers, answer_key_list)

                        # Auto-generate student information
                        student_name = f"Student_{self.student_counter:03d}"
                        student_id = f"STU_{datetime.now().strftime('%Y%m%d')}_{self.student_counter:03d}"

                        # Save result image (using the original frame for simplicity)
                        image_path = self.save_result_image(frame, score, student_id)

                        # Display results (simplified version)
                        print(f"\n" + "=" * 30)
                        print("AUTOMATIC GRADING RESULTS")
                        print("=" * 30)
                        print(f"Student: {student_name} (ID: {student_id})")
                        print(f"Score: {score:.2f}%")
                        print(f"Correct Answers: {correct}/{self.num_questions}")
                        
                        # Display simplified detected answers
                        print("\nFINAL DETECTED ANSWERS:")
                        print("-" * 30)
                        for i, answer in enumerate(detected_answers, 1):
                            print(f"Q{i}: {answer}")
                        print("-" * 30)

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
                                # Detailed results are not generated by simplified grading, pass empty list
                                detailed_results=[] 
                            )

                            if session_id:
                                print(f"\nResults saved to database with session ID: {session_id}")
                            else:
                                print("\nError saving results to database.")

                        self.student_counter += 1
                        print(f"\n[SUCCESS] Sheet {detection_count} processed automatically!")
                        print("Place next sheet or press 'q' to quit.")

                        # Show the frame with results for a short duration
                        for _ in range(90):  # 3 seconds at ~30 fps
                            cv2.imshow('OptiGrade Fully Automatic Scanner', display_frame)
                            if cv2.waitKey(33) & 0xFF == ord('q'):
                                break
                    else:
                        # Draw "No valid OMR detected" on frame if not enough valid answers
                        cv2.putText(display_frame, "No valid OMR detected", (10, 30),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                        print("[INFO] No valid OMR detected. Waiting for next frame...")
                else:
                    # Draw "Looking for OMR..." on frame
                    cv2.putText(display_frame, "Looking for OMR sheet...", (10, 30),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
                    print("[INFO] Looking for OMR sheet...")
            
            # Show the live frame
            cv2.imshow("OptiGrade Fully Automatic Scanner", display_frame)

            # Handle key presses
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()
        print(f"\n[INFO] Fully automatic scanning completed. Total sheets processed: {detection_count}")

    def run_fully_auto_session(self):
        """Run a complete fully automatic grading session"""
        # Setup assignment
        self.setup_assignment()

        # Setup camera
        cap = self.setup_camera()
        if cap is None:
            return

        # Start fully automatic scanning
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
    app = OptiGradeFullyAuto()

    while True:
        print("\n" + "=" * 50)
        print("OPTIGRADE FULLY AUTOMATIC SCANNER")
        print("=" * 50)
        print("1. Start Fully Automatic Grading Session")
        print("2. View Assignment Statistics")
        print("3. Export Results to CSV")
        print("4. View Student Results")
        print("5. Exit")

        choice = input("\nSelect an option (1-5): ").strip()

        if choice == '1':
            app.run_fully_auto_session()
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
            print("Thank you for using OptiGrade Fully Automatic Scanner!")
            break
        else:
            print("Invalid option. Please select 1-5.")

if __name__ == "__main__":
    main()
