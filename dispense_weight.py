import os
import sys
import time
import board
import RPi.GPIO as GPIO
from cedargrove_nau7802 import NAU7802

# Ensure stepper_motor.py in the same folder can always be imported
#sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stepper_motor

# --- GPIO PIN CONFIGURATION ---
# NAU7802 uses hardware I2C pins (SDA = GPIO 2, SCL = GPIO 3)
PUMP_SUGAR_PIN = 12
PUMP_TEA_PIN = 16

# Standard active-low relay logic (swap LOW/HIGH if using an active-high board)
PUMP_ON = GPIO.LOW
PUMP_OFF = GPIO.HIGH

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(PUMP_SUGAR_PIN, GPIO.OUT, initial=PUMP_OFF)
GPIO.setup(PUMP_TEA_PIN, GPIO.OUT, initial=PUMP_OFF)

# --- RECIPES & CALIBRATION ---
# Raw ADC counts per gram (replace after calibrating with a known weight)
CALIBRATION_FACTOR = 420.0

SUGAR_GRAMS = {
    "0": 0,
    "50": 15,
    "100": 30,
}

DRINK_GRAMS = {
    "silly_seal": 200,
    "polar_prince": 220,
    "december_delight": 250,
}


def setup_scale():
    """Initializes the Adafruit NAU7802 over I2C and calibrates channel 1."""
    i2c = board.I2C()
    nau7802 = NAU7802(i2c, address=0x2A, active_channels=1)
    nau7802.enable(True)
    nau7802.channel = 1
    nau7802.calibrate("INTERNAL")
    nau7802.calibrate("OFFSET")

    # Flush initial startup readings
    for _ in range(5):
        while not nau7802.available():
            time.sleep(0.005)
        _ = nau7802.read()

    return nau7802


def read_grams(nau7802, samples=3):
    """Averages multiple NAU7802 readings and converts raw ADC counts to grams."""
    total = 0
    for _ in range(samples):
        while not nau7802.available():
            time.sleep(0.005)
        total += nau7802.read()
    avg_raw = total / samples
    return avg_raw / CALIBRATION_FACTOR


def dispense_to_weight(nau7802, pump_pin, target_grams, max_timeout=15):
    if target_grams <= 0:
        return

    # Take a fresh baseline reading after each table rotation
    initial_weight = read_grams(nau7802, samples=5)
    target_total = initial_weight + target_grams
    start_time = time.time()

    GPIO.output(pump_pin, PUMP_ON)
    try:
        while True:
            current_weight = read_grams(nau7802, samples=3)

            if current_weight >= target_total:
                added = current_weight - initial_weight
                print(f"Target reached: +{added:.1f}g (target: {target_grams}g)")
                break

            if time.time() - start_time > max_timeout:
                print("Safety timeout reached! Shutting off pump.")
                break

            time.sleep(0.02)
    finally:
        GPIO.output(pump_pin, PUMP_OFF)


def main(drink_key, sugar_level):
    target_sugar = SUGAR_GRAMS.get(sugar_level, 0)
    target_drink = DRINK_GRAMS.get(drink_key, 0)

    nau7802 = setup_scale()

    try:
        # 1. Rotate 90° to Station 1 (Sugar)
        stepper_motor.quarter_spin()
        if target_sugar > 0:
            print(f"Station 1: Dispensing {target_sugar}g sugar...")
            dispense_to_weight(nau7802, PUMP_SUGAR_PIN, target_sugar, max_timeout=10)

        # 2. Rotate 90° to Station 2 (Base Drink)
        stepper_motor.quarter_spin()
        if target_drink > 0:
            print(f"Station 2: Dispensing {target_drink}g of {drink_key}...")
            dispense_to_weight(nau7802, PUMP_TEA_PIN, target_drink, max_timeout=20)

        # 3. Rotate 90° past Station 3
        stepper_motor.quarter_spin()

        # 4. Rotate 90° back to Front Pickup (360° total)
        stepper_motor.quarter_spin()

        print("Drink complete and returned to front!")
    finally:
        GPIO.output(PUMP_SUGAR_PIN, PUMP_OFF)
        GPIO.output(PUMP_TEA_PIN, PUMP_OFF)
        stepper_motor.sleep_motor()


if __name__ == "__main__":
    if len(sys.argv) > 2:
        main(sys.argv[1], sys.argv[2])
    else:
        print("Usage: python3 dispense_weight.py <drink> <sugar>")