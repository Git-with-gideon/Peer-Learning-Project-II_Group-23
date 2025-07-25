import cv2
import numpy as np
import imutils
from imutils.perspective import four_point_transform
from imutils import contours

# 1. Welcome and Setup
print("Welcome to OptiGrade!")
num_questions = int(input("How many questions do you plan to grade? "))

print(f"Input the correct answer for each question (A-E):")
answer_key = {}
for i in range(num_questions):
    while True:
        ans = input(f"{i+1}. ").strip().upper()
        if ans in ['A', 'B', 'C', 'D', 'E']:
            answer_key[i] = 'ABCDE'.index(ans)
            break
        else:
            print("Please enter a valid option (A, B, C, D, or E).")

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
    exit(1)

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
        exit(0)

cap.release()
cv2.destroyAllWindows()

# 3. OMR Detection & Grading
# Preprocess
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
blurred = cv2.GaussianBlur(gray, (5, 5), 0)
edged = cv2.Canny(blurred, 75, 200)

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
    exit(1)

paper = four_point_transform(image, docCnt.reshape(4, 2))
warped = four_point_transform(gray, docCnt.reshape(4, 2))

thresh = cv2.threshold(warped, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]

# Debug: Optionally show the thresholded image
show_thresh = input("Show thresholded image for debugging? (y/n): ").strip().lower()
if show_thresh == 'y':
    cv2.imshow("Thresholded", thresh)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
cnts = imutils.grab_contours(cnts)
questionCnts = []

for c in cnts:
    (x, y, w, h) = cv2.boundingRect(c)
    ar = w / float(h)
    if w >= 20 and h >= 20 and 0.9 <= ar <= 1.1:
        questionCnts.append(c)

if len(questionCnts) < num_questions * 5:
    print(f"[WARNING] Detected {len(questionCnts)} bubbles, expected at least {num_questions * 5}.")
    if len(questionCnts) == 0:
        print("[ERROR] No bubbles detected. Please check the OMR sheet placement, lighting, and camera focus.")
        exit(1)

questionCnts = contours.sort_contours(questionCnts, method="top-to-bottom")[0]
correct = 0

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
    k = answer_key.get(q, None)
    if k is None:
        continue
    if bubbled is not None and k == bubbled[1]:
        color = (0, 255, 0)
        correct += 1
    cv2.drawContours(paper, [cnts[k]], -1, color, 3)

score = (correct / float(num_questions)) * 100
print(f"[INFO] Score: {score:.2f}%")
cv2.putText(paper, f"{score:.2f}%", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
cv2.imshow("OMR Result", paper)
cv2.waitKey(0)
cv2.destroyAllWindows()
