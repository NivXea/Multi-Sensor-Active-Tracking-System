import serial
from track import *
import time
import pygame
import math

armed = True
cooldown = 2
last_trigger_time = 0
NUM_SENSORS = 4
last_valid = [None] * NUM_SENSORS
confidence = [0] * NUM_SENSORS
threshold_dist = 30#cm
max_conf = 7
ser = serial.Serial("COM8", 9600, timeout=1)

distances = [0,0,0,0]

sensor_angles = {
    0: 45,
    1: 90,
    2: 135,
    3: 180
}

pygame.init()
WIDTH, HEIGHT = 600, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Radar")
center = (WIDTH // 2, HEIGHT // 2)
max_radius = 250
running = True

while running:
    # -------- 1. EVENTS --------
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # -------- 2. SERIAL INPUT --------
    if ser.in_waiting:
        line = ser.readline().decode(errors='ignore').strip()

        try:
            parts = line.split(',')

            if parts[0] == 'D' and len(parts) == 3:
                _, idx, dist = parts

                idx = int(idx)
                dist = float(dist)

                if dist == -1:
                    dist = last_valid[idx]
                else:
                    last_valid[idx] = dist

                if dist is None:
                    continue

                distances[idx] = dist

                # -------- 3. LOGIC --------
                if dist < threshold_dist:
                    confidence[idx] += 1
                else:
                    confidence[idx] = max(0, confidence[idx] - 2)

                # trigger
                if armed and any(c >= max_conf for c in confidence):
                    if time.time() - last_trigger_time >= cooldown:

                        print("TRIGGERING TRACK MODE")
                        ser.write(b"START\n")

                        armed = False
                        last_trigger_time = time.time()

                        track(ser)

                        # RESET AFTER TRACK
                        confidence = [0] * NUM_SENSORS
                        last_valid = [None] * NUM_SENSORS
                        distances = [None] * NUM_SENSORS

            else:
                print("Arduino:", line)

        except:
            pass

    # -------- REARM --------
    if not armed:
        if all(d is None or d > threshold_dist for d in distances):
            print("REARMED")
            armed = True

    # -------- 4. DRAW RADAR --------
    screen.fill((0, 0, 0))

    for r in range(50, max_radius + 1, 50):
        pygame.draw.circle(screen, (0, 100, 0), center, r, 1)

    pygame.draw.circle(screen, (0, 255, 0), center, 5)

    for i, dist in enumerate(distances):
        if dist is None:
            continue

        angle = sensor_angles.get(i, 90)

        rad = math.radians(angle)
        scaled = min(dist * 2, max_radius)

        x = center[0] + scaled * math.cos(rad)
        y = center[1] - scaled * math.sin(rad)

        pygame.draw.line(screen, (0, 255, 0), center, (x, y), 1)
        pygame.draw.circle(screen, (255, 0, 0), (int(x), int(y)), 5)

    pygame.display.flip()
