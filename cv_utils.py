# cv_utils.py
import cv2
import numpy as np

def analyze_image(image_path):
    """
    Detects crowds or large objects using simple contour detection.
    Returns a cv_score (0 to 1) and list of objects detected.
    """
    img = cv2.imread(image_path)
    if img is None:
        return {"cv_score": 0, "objects_detected": []}

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    objects_detected = []
    cv_score = 0

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > 500:  # threshold for "large object"
            objects_detected.append("large_object")
            cv_score += 0.1

    cv_score = min(cv_score, 1.0)
    return {"cv_score": cv_score, "objects_detected": objects_detected}
