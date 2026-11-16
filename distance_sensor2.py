import platform
import shutil
import subprocess
import threading
import time
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

# --- GLOBAL PRESENCE STATE & SENSOR CONFIG ---
USER_PRESENT = False
TRIG, ECHO = 17, 27  # BCM pins from distance_sensor.py
TIMEOUT = 0.040      # Timeout duration in seconds
MAX_ECHO = 0.0117    # Max echo window (2m max distance)
THRESHOLD_DIST = 0.5 # Target threshold (0.5m)


def run_distance_monitor():
    """Background daemon thread running the custom ultrasonic distance loop."""
    global USER_PRESENT

    # Automatically set to True on PC so simulation testing always works
    if platform.system() != "Linux":
        USER_PRESENT = True
        return

    try:
        import RPi.GPIO as GPIO

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(TRIG, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(ECHO, GPIO.IN)

        def echo_time():
            if GPIO.input(ECHO):
                return None
            GPIO.output(TRIG, GPIO.HIGH)
            time.sleep(10e-6)
            GPIO.output(TRIG, GPIO.LOW)

            t_trig = time.perf_counter()
            while GPIO.input(ECHO) == 0:
                if time.perf_counter() - t_trig > TIMEOUT:
                    return None

            start = time.perf_counter()
            while GPIO.input(ECHO) == 1:
                if time.perf_counter() - start > TIMEOUT:
                    return None

            end = time.perf_counter()
            width = end - start
            return width if 0 < width <= MAX_ECHO else None

        def distance_m(t_val):
            return (343 * t_val / 2) if t_val is not None else 0

        consecutive_count = 0

        while True:
            t = echo_time()
            dist = distance_m(t)

            if dist != 0 and dist < THRESHOLD_DIST:
                consecutive_count += 1
            elif dist == 0:
                pass
            else:
                consecutive_count = 0

            # Unlock screen after 3 consecutive valid readings within range
            if consecutive_count >= 3:
                USER_PRESENT = True
            elif consecutive_count == 0 and dist >= THRESHOLD_DIST:
                USER_PRESENT = False

            time.sleep(0.05)

    except Exception as e:
        print(f"Distance sensor error: {e}")
        # Fallback to True on error so the app remains usable
        USER_PRESENT = True


# Start distance monitor loop as a background daemon thread
threading.Thread(target=run_distance_monitor, daemon=True).start()


# --- DRINK MAP CONFIGURATION ---
DRINK_MAP = {
    "silly_seal": {
        "name": "Silly Seal Special",
        "0": ["python3", "/home/pi/scripts/dispense_weight.py", "silly_seal", "0"],
        "50": ["python3", "/home/pi/scripts/dispense_weight.py", "silly_seal", "50"],
        "100": ["python3", "/home/pi/scripts/dispense_weight.py", "silly_seal", "100"],
    },
    "polar_prince": {
        "name": "Polar Prince",
        "0": ["python3", "/home/pi/scripts/dispense_weight.py", "polar_prince", "0"],
        "50": ["python3", "/home/pi/scripts/dispense_weight.py", "polar_prince", "50"],
        "100": ["python3", "/home/pi/scripts/dispense_weight.py", "polar_prince", "100"],
    },
    "december_delight": {
        "name": "December Delight",
        "0": ["python3", "/home/pi/scripts/dispense_weight.py", "december_delight", "0"],
        "50": ["python3", "/home/pi/scripts/dispense_weight.py", "december_delight", "50"],
        "100": ["python3", "/home/pi/scripts/dispense_weight.py", "december_delight", "100"],
    },
}


def execute_pi_command(drink_key, sugar_level):
    drink_info = DRINK_MAP.get(drink_key)
    if not drink_info or sugar_level not in ["0", "50", "100"]:
        return {"status": "error", "output": "Invalid drink or sugar selection"}

    drink_name = drink_info["name"]
    cmd_list = drink_info.get(sugar_level)
    binary = cmd_list[0]

    if (
        platform.system() != "Linux"
        or shutil.which(binary) is None
        and binary != "sudo"
    ):
        return {
            "status": "success",
            "is_mock": True,
            "output": f"[PC Simulation] Dispensing {drink_name} ({sugar_level}% Sugar)",
        }

    try:
        result = subprocess.run(
            cmd_list, capture_output=True, text=True, timeout=30
        )
        output = (
            result.stdout.strip()
            if result.returncode == 0
            else result.stderr.strip()
        )
        return {
            "status": "success",
            "is_mock": False,
            "output": output or f"Dispensed {drink_name} ({sugar_level}% Sugar)",
        }
    except Exception as e:
        return {"status": "error", "output": str(e)}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/presence", methods=["GET"])
def get_presence():
    """Polled by frontend index.html every second to check lock status."""
    return jsonify({"active": USER_PRESENT})


@app.route("/api/execute", methods=["POST"])
def run_action():
    if not USER_PRESENT and platform.system() == "Linux":
        return jsonify({"status": "error", "output": "User not detected near machine."})

    data = request.get_json() or {}
    drink = data.get("drink")
    sugar = data.get("sugar")
    res = execute_pi_command(drink, sugar)
    return jsonify(res)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)