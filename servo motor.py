import time
import RPi.GPIO as GPIO


servo = 17 #sets which BCM pin we want to use for the single
GPIO.setmode(GPIO.BCM)
GPIO.setup(servo, GPIO.OUT)

pwm = GPIO.PWM(servo, 50) #sets the servo at 50 Hz
pwm.start(0)

#1.125 is 30 degrees probably maybe for the servo we are using 
#also max pwm for the servo is 10%

def angle_to_duty(angle): #15-63 are edited Gemini code 
    """
    find the angle to PWM ratio (for the servo we used it was 1.125:30 PWM:degrees)
    """
    return angle*1.125/30

def trigger_servo(target_angle, hold_duration, rest_angle=0):
    """
    Callable target for your UI button or event trigger.
    
    :param target_angle: Angle to move to (in degrees)
    :param hold_duration: How long to stay at target_angle (in seconds)
    :param rest_angle: Angle to return to when finished (in degrees)
    """
    try:
        # 1. Move to target angle
        target_duty = angle_to_duty(target_angle)
        pwm.ChangeDutyCycle(target_duty)
        time.sleep(0.4)  # Give motor time to physically turn
        
        # 2. Cut signal while holding to prevent servo jitter/buzzing
        pwm.ChangeDutyCycle(0)
        time.sleep(hold_duration)

        # 3. Return to starting angle
        rest_duty = angle_to_duty(rest_angle)
        pwm.ChangeDutyCycle(rest_duty)
        time.sleep(0.4)  # Give motor time to return
        
        # 4. Turn off signal again
        pwm.ChangeDutyCycle(0)

    except Exception as e:
        print(f"Servo execution error: {e}")

# Cleanup handler to call when closing your application
def cleanup():
    pwm.stop()
    GPIO.cleanup()

# Example Usage: Simulating UI Triggers
if __name__ == "__main__":
    try:
        print("Simulating UI button press...")
        # Move to 30 degrees, wait 3 seconds, return to 0 degrees
        trigger_servo(target_angle=30, hold_duration=3.0, rest_angle=0)
        
    finally:
        cleanup()