import time 
import RPi.GPIO as GPIO
import pandas as pd

TRIG, ECHO = 17, 27 #BCM
TIMEOUT = 0.040 #s
MAX_ECHO = 0.0117 #s max echo, 2m 
THRESHOLD_DIST = 0.5 #m 

GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG, GPIO.OUT, initial = GPIO.LOW)
GPIO.setup(ECHO, GPIO.IN)

def echo_time():
    if GPIO.input(ECHO): #returns none if echo is 0 
        return None
    GPIO.output(TRIG, GPIO.HIGH)
    time.sleep(10e-6)
    GPIO.output(TRIG, GPIO.LOW)
    now = time.perf_counter()
    t_trig = time.perf_counter()
    while GPIO.input(ECHO) == 0: #if we receive no ECHO input, ie if input is low 
        if now - t_trig > TIMEOUT:
            return None
    start = time.perf_counter()
    while GPIO.input(ECHO) == 1:
        if now - start > TIMEOUT:
            return None
    end = time.perf_counter()
    width = end - start
    if not 0 < width <= MAX_ECHO:
        return None
    return width



def distance_m(T):#formula for distance from T 
    if T == None:
        return 0
    return 343*T/2


try: #43-69 Gemini AI
    while 1:
        t = echo_time()
        dist = distance_m(t)

        if dist is not 0 and dist < THRESHOLD_DIST:
            consecutive_count += 1
            #print(f"Reading {consecutive_count}/3 below threshold: {dist:.2f} m")
        elif dist == 0:
            pass #does nothing 
        else:
            # Reset count if reading fails or exceeds the distance limit
            consecutive_count = 0

        if consecutive_count >= 3:
            #print("Action triggered: 3 consecutive readings were under threshold!")
            # Insert custom action/code here
            
            # Optional: reset counter if you want it to wait for 3 new readings before triggering again
            # consecutive_count = 0 

        time.sleep(0.05)  # Short delay between measurements

except KeyboardInterrupt:
    print("Program stopped.")
finally:
    GPIO.cleanup()
