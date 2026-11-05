import time 
import RPi.GPIO as GPIO

# AIN1, AIN2, BIN1, BIN2

coil = [17, 27, 22, 23]

GPIO.setmode(GPIO.BCM) #sets which mode the pins are called from

GPIO.setup(24, GPIO.OUT) #sets up BCM 24, which is going to be used as the sleep 
GPIO.output(24, GPIO.HIGH)

for i in coil: #sets up our input BCMs through a loop
    GPIO.setup(i, GPIO.OUT, initial = 0)

def set_coils(a1, a2, b1, b2): #creates a function that lets us easily set the coils
    GPIO.output(coil[0], a1)
    GPIO.output(coil[1], a2)
    GPIO.output(coil[2], b1)
    GPIO.output(coil[3], b2)

steps = 200 #how many steps to complete a full rotation
turns = 1 #how many total rotations we want
rpm = 60 #rpm of the motor
direction = 1 #direction, 1 is clockwise, -1 is counter clockwise

delay = 60 / steps /rpm #delay between each step
total_steps = steps * turns #total number of steps for the full rotation

#defines specific states to be called upon later
state = 0 
absolute = 0 
state_blank = (0, 0, 0, 0)
statea1b1 = (1, 0, 1, 0)
statea2b1 = (0, 1, 1, 0)
statea2b2 = (0, 1, 0, 1)
statea1b2 = (1, 0, 0, 1)

set_coils(*statea1b1)
def quarter_spin():
    time.sleep (0.1)
    global state
    global absolute
    for i in range (50): #loops through all the steps, setting the coils to the right state sequentially
            state = (state + direction) #total_steps/4 should allow for each position to be hit
            absolute += 1
            if state % 4 == 0:
                set_coils(*statea1b1)
            if state % 4 == 1:
                set_coils(*statea2b1)
            if state % 4 == 2:
                set_coils(*statea2b2)
            if state % 4 == 3:
                set_coils(*statea1b2)
            time.sleep(delay)

def reset_stepper(): 
     time.sleep(0.1)
     global direction
     if abs % 200 == 0:
          return None
     elif (abs + 50) % 200 == 0:
          quarter_spin()
     elif (abs +100) % 200 == 0: 
          quarter_spin()
          quarter_spin()
     else:
          direction = -1
          quarter_spin()
          direction = 1

set_coils(*state_blank)
GPIO.output(24, GPIO.LOW)
GPIO.cleanup()