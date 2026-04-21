import cv2
import numpy as np
import time


def track(ser):
    cap = cv2.VideoCapture(1)
    inac_time = time.time()  #Target Timeout
    last_sent = 0  #Serial Timeout

   

    #Sending Mean Position Angles beforehand
    servo_x = 99
    servo_y = 88
    ser.write(b"T,99,88\n") 
    prev_x , prev_y = 99,88

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
    "red_low": [((0, 90, 90), (12, 255, 255))],
    "red_high": [((165, 90, 90), (180, 255, 255))],
}

        largest = None
        max_area = 0

        full_mask = None

        for ranges in colors.values():
            for (lower, upper) in ranges:
                lower = np.array(lower)
                upper = np.array(upper)

                partial = cv2.inRange(hsv, lower, upper)

                if full_mask is None:
                    full_mask = partial
                else:
                    full_mask = cv2.bitwise_or(full_mask, partial)

            contours, _ = cv2.findContours(full_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area < 1500:
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
                    if time.time() - last_sent > 0.02:
                        norm_x = (cx - frame_w // 2) / (frame_w // 2)
                        norm_y = (cy - frame_h // 2) / (frame_h // 2)

                        servo_x = int(100 - norm_x * 20)
                        servo_y = int(90 + norm_y * 15)

                        # clamp safety
                        servo_x = max(80, min(120, servo_x))
                        servo_y = max(75, min(105, servo_y))

                        # optional smoothing (only if needed)
                        # servo_x = int(0.7 * prev_x + 0.3 * servo_x)
                        # servo_y = int(0.7 * prev_y + 0.3 * servo_y)

                        prev_x, prev_y = servo_x, servo_y

                        ser.write(f"T,{servo_x},{servo_y}\n".encode())
                        print(f"X: {servo_x} , Y: {servo_y}")

                        last_sent = time.time()

        else:
            if time.time() - inac_time > 3:
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
