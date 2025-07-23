"""
This is the main file
"""
import cv2
import numpy as np

def process_omr_sheet(frame, num_questions, num_options):
    """
    Process OMR sheet to detect marked answers
    Returns list of detected answers (A, B, C, D, E, etc.) or None if failed
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
        if 100 < area < 5000:  # Adjust these values based on your OMR sheet
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = w / float(h)
            if 0.8 < aspect_ratio < 1.2:  # Roughly circular
                bubbles.append((x, y, w, h, area))
    
    if len(bubbles) < num_questions * num_options:
        print(f"Warning: Found {len(bubbles)} bubbles, expected at least {num_questions * num_options}")
        return None
    # Sort bubbles by position (top to bottom, left to right)
    bubbles.sort(key=lambda b: (b[1], b[0]))
    
    # Group bubbles by questions
    detected_answers = []
    options = [chr(65 + i) for i in range(num_options)]  # A, B, C, D, E, etc.
    
    for q in range(num_questions):
        question_bubbles = bubbles[q*num_options:(q+1)*num_options]
        if len(question_bubbles) < num_options:
            detected_answers.append('X')  # No answer detected
        continue
    # Find the bubble with the most filled area (darkest)
    max_area = 0
    selected_option = 'X'
        
    for i, (x, y, w, h, area) in enumerate(question_bubbles):
        if i < len(options):
            # Calculate the average intensity in the bubble region
            roi = gray[y:y+h, x:x+w]
            if roi.size > 0:
                avg_intensity = np.mean(roi)
                    # Lower intensity means darker (more filled)
            if avg_intensity < 128 and area > max_area:
                        max_area = area
                        selected_option = options[i]
        
        detected_answers.append(selected_option)
    
    return detected_answers

def grade_answers(detected_answers, answer_key):
    """
    Grade the detected answers against the answer key
    Returns score as percentage
    """
    correct = 0
    total = len(answer_key)
    
    for detected, correct_ans in zip(detected_answers, answer_key):
        if detected == correct_ans:
            correct += 1
    
    return (correct / total) * 100
    
def display_results(detected_answers, answer_key, score, num_questions, num_options):
    """
    Display grading results
    """
    options_str = ", ".join([chr(65 + i) for i in range(num_options)])
    print("\n" + "="*50)
    print("GRADING RESULTS")
    print("="*50)
    print(f"Options available: {options_str}")
    print("-" * 50)
    
    print(f"{'Question':<10} {'Detected':<10} {'Correct':<10} {'Status':<10}")
    print("-" * 40)
    
    for i in range(num_questions):
        detected = detected_answers[i] if i < len(detected_answers) else 'X'
        correct = answer_key[i] if i < len(answer_key) else 'X'
        status = "✓" if detected == correct else "✗"
        
        print(f"{i+1:<10} {detected:<10} {correct:<10} {status:<10}")
    
    print("-" * 40)
    print(f"Score: {score:.1f}% ({int(score/100 * num_questions)}/{num_questions} correct)")
    print("="*50)
    
    # Display final answers clearly
    print("\nFINAL DETECTED ANSWERS:")
    print("-" * 30)
    for i, answer in enumerate(detected_answers, 1):
        print(f"Q{i}: {answer}")
    
    # Save results to file
    save_results_to_file(detected_answers, answer_key, score, num_questions)
    def save_results_to_file(detected_answers, answer_key, score, num_questions):
    """
    Save grading results to a text file
    """
    import datetime
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"grading_results_{timestamp}.txt"
    
    with open(filename, 'w') as f:
        f.write("OPTIGRADE GRADING RESULTS\n")
        f.write("=" * 30 + "\n")
        f.write(f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Score: {score:.1f}% ({int(score/100 * num_questions)}/{num_questions} correct)\n\n")   
        f.write("DETECTED ANSWERS:\n")
        f.write("-" * 20 + "\n")
        for i, answer in enumerate(detected_answers, 1):
            f.write(f"Q{i}: {answer}\n")
        
        f.write("\nANSWER KEY:\n")
        f.write("-" * 15 + "\n")
        for i, answer in enumerate(answer_key, 1):
            f.write(f"Q{i}: {answer}\n")
        
        f.write("\nCOMPARISON:\n")
        f.write("-" * 15 + "\n")
        for i in range(num_questions):
            detected = detected_answers[i] if i < len(detected_answers) else 'X'
            correct = answer_key[i] if i < len(answer_key) else 'X'
            status = "CORRECT" if detected == correct else "INCORRECT"
            f.write(f"Q{i+1}: Detected={detected}, Correct={correct}, Status={status}\n")
    
    print(f"\nResults saved to: {filename}")
    
# 1. CLI: Get answer key from teacher
print("Welcome to OptiGrade")
num_questions = int(input("How many questions do you plan to grade: "))
print(f"Input your answers from Question 1 to {num_questions} (e.g., A, B, C, D):")
answer_key = []
for i in range(num_questions):
    ans = input(f"{i+1}. ").strip().upper()
    answer_key.append(ans)

print("\nAnswer key saved:")
for idx, ans in enumerate(answer_key, 1):
    print(f"Q{idx}: {ans}")

input("\nPress Enter to begin scanning OMR sheets...")

# 2. Start webcam and capture frame
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Could not open webcam.")
    exit()

print("Press 's' to scan an OMR sheet, or 'q' to quit.")

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame.")
        break
    cv2.imshow('OptiGrade - Live Camera', frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('s'):
    
        # 3. Placeholder: OMR processing logic goes here
        # For now, just save the frame and print a message
        cv2.imwrite('scanned_omr.jpg', frame)
        print("OMR sheet captured and saved as 'scanned_omr.jpg'.")
        print("(OMR processing logic to be implemented here.)")

cap.release()
cv2.destroyAllWindows()

print("\nThank you for using OptiGrade!")
