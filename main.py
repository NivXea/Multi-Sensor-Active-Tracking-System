import cv2
import numpy as np

colors = {
    "green": [ ((40, 70, 70), (80, 255, 255)) ]
    ,
    "magenta": [ ((140, 80, 80), (170, 255, 255)) ]
}



cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        continue

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    for color_name, ranges in colors.items():

        color_mask = None

        for (lower, upper) in ranges:
            lower = np.array(lower)
            upper = np.array(upper)

            partial = cv2.inRange(hsv, lower, upper)
            color_mask = partial
    
        contours, _ = cv2.findContours(color_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        largest = None
        max_area = 0

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < 2000:
                continue
            if area > max_area:
                max_area = area
                largest = cnt

        if largest is not None:
            x, y, w, h = cv2.boundingRect(largest)
            rect_area = w * h
            contour_area = cv2.contourArea(largest)
            solidity = contour_area / rect_area
            if solidity > 0.6:
                cv2.drawContours(frame, [largest], -1, (0,255,0), 2)

        cv2.imshow("Live", frame)

    if cv2.waitKey(1) == 27:
        break

cap.release()
cv2.destroyAllWindows()
