from camera import *
import serial

confidence = 0
threshold = 5
ser = serial.Serial("COM7",9600)
safe_count = 0
armed = True

while True:
    line = ser.readline().decode().strip()
    
    if line == "SAFE" and confidence != 0:
        confidence -= 1
    elif line == "ALERT" and confidence < threshold+1: 
        confidence += 1
    
    print(f"Confidence: {confidence}")

    #Checking via Camera 
    if armed and confidence >= threshold: 
        check = verify()

    #Disarming the System if nothing found
        if (check == False):
            confidence = 0
            armed = False 

    #Rearming the System 
    elif not armed:
        if line == "SAFE":
            safe_count+=1
        if safe_count > 30:
            safe_count = 0
            armed = True
        
    



