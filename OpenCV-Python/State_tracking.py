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
threshold_dist = 15#cm
max_conf = 7
ser = serial.Serial("COM8", 9600, timeout=1)
distances = [0,0,0,0]

sensor_angles = {
    0: 0,
    1: 60,
    2: 120,
    3: 180
}

pygame.init()
font = pygame.font.SysFont("Arial", 18)
WIDTH, HEIGHT = 600, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Radar")
center = (WIDTH // 2, HEIGHT // 2)
max_radius = 250
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    #SERIAL INPUT
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

                #DISTANCE LOGIC
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

    #Rearming the System
    if not armed:
        if all(d is None or d > threshold_dist for d in distances):
            print("REARMED")
            armed = True

    #Radar Logic
    screen.fill((0, 0, 0))

    for r in range(50, max_radius + 1, 50):
        rect = pygame.Rect(center[0] - r, center[1] - r, 2*r, 2*r)
        pygame.draw.arc(screen, (0, 100, 0), rect, 0, math.pi, 1)

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

        table_y = HEIGHT - 180

        table_width = 3 * 150
        start_x = (WIDTH - table_width) // 2

        headers = ["Sensor", "Distance", "Confidence"]
        for i, text in enumerate(headers):
            label = font.render(text, True, (0, 255, 0))
            screen.blit(label, (start_x + i*150, table_y))

        for i in range(NUM_SENSORS):
            d = distances[i] if distances[i] is not None else "-"
            c = confidence[i]

            row = [str(i), str(round(d, 2)) if d != "-" else "-", str(c)]

            for j, val in enumerate(row):
                label = font.render(val, True, (255, 255, 255))
                screen.blit(label, (start_x + j*150, table_y + 30 + i*25))

    pygame.display.flip()
