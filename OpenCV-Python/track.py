import cv2
import numpy as np
import time


def track(ser):
    cap = cv2.VideoCapture(0)
    inac_time = time.time()  #Target Timeout
    last_sent = 0  #Serial Timeout

   

    #Sending Mean Position Angles beforehand
    servo_x = 90
    servo_y = 90
    ser.write(b"T,90,90\n") 

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        frame_h, frame_w = frame.shape[:2]
        #Adding Lines for Cleaner Debugging Later 
        #cv2.line(frame, (frame_w//2, 0), (frame_w//2, frame_h), (255,255,255), 1) 
        #cv2.line(frame, (0, frame_h//2), (frame_w, frame_h//2), (255,255,255), 1)

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        colors = {
            "green": [((40, 70, 70), (80, 255, 255))],
            "magenta": [((140, 80, 80), (170, 255, 255))]
        }

        largest = None
        max_area = 0

        for ranges in colors.values():

            color_mask = None

            for (lower, upper) in ranges:
                lower = np.array(lower)
                upper = np.array(upper)

                partial = cv2.inRange(hsv, lower, upper)
                if color_mask is None:
                    color_mask = partial
                else:
                    color_mask = cv2.bitwise_or(color_mask, partial)

            contours, _ = cv2.findContours(color_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area < 2000:
                    continue
                if area > max_area:
                    max_area = area
                    largest = cnt

        #Tracking The Target
        if largest is not None:
            inac_time = time.time()

            x, y, w, h = cv2.boundingRect(largest)
            rect_area = w * h
            contour_area = cv2.contourArea(largest)

            if rect_area > 0:
                solidity = contour_area / rect_area
            else:
                solidity = 0

            if solidity > 0.6:
                cv2.drawContours(frame, [largest], -1, (0, 255, 0), 2)

                #Computing Cx , Cy
                M = cv2.moments(largest)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])

                    cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)

                    #Sending Serial Input for Servo
                    if time.time() - last_sent > 0.05:
                        error_x = cx - frame_w // 2
                        error_y = cy - frame_h // 2

                        # simple proportional control
                        kp = 0.05

                        #Adding A Deadzone to reduce Jitter
                        dead_zone = 20
                        if abs(error_x) > dead_zone:
                            servo_x -= int(kp * error_x)

                        if abs(error_y) > dead_zone:
                            servo_y += int(kp * error_y)

                        # clamp angles
                        servo_x = int((cx / frame_w) * 180)
                        servo_y = int((cy / frame_h) * 180)

                        prev_x, prev_y = servo_x, servo_y

                        #Smoothing
                        alpha = 0.2
                        servo_x = int((1 - alpha) * prev_x + alpha * servo_x)
                        servo_y = int((1 - alpha) * prev_y + alpha * servo_y)

                        ser.write(f"T,{servo_x},{servo_y}\n".encode())
                        last_sent = time.time()

        else:
            if time.time() - inac_time > 5:
                cv2.putText(
                    frame,
                    "TARGET LOST",
                    (50, 50),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 0, 255),
                    2
                )

                cv2.imshow("Live", frame)
                cv2.waitKey(500)  # show message briefly

                print("TARGET LOST")

                ser.write(b"STOP\n")
                break

        cv2.imshow("Live", frame)
        if cv2.waitKey(1) == 27:
            ser.write(b"STOP\n")
            break

    cap.release()
    cv2.destroyAllWindows()
