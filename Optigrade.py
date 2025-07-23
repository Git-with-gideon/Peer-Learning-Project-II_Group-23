"""
This is the main file
"""
import cv2
import numpy as np

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