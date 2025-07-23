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