import platform
import shutil
import subprocess
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

# --- DRINK & COMMAND CONFIGURATION ---
DRINK_MAP = {
    "silly_seal": {
        "name": "Silly Seal Special",
        "0": ["python3", "/home/pi/scripts/seal_0.py"],
        "50": ["python3", "/home/pi/scripts/seal_50.py"],
        "100": ["python3", "/home/pi/scripts/seal_100.py"],
    },
    "polar_prince": {
        "name": "Polar Prince",
        "0": ["python3", "/home/pi/scripts/polar_0.py"],
        "50": ["python3", "/home/pi/scripts/polar_50.py"],
        "100": ["python3", "/home/pi/scripts/polar_100.py"],
    },
    "december_delight": {
        "name": "December Delight",
        "0": ["python3", "/home/pi/scripts/dec_0.py"],
        "50": ["python3", "/home/pi/scripts/dec_50.py"],
        "100": ["python3", "/home/pi/scripts/dec_100.py"],
    },
}


def execute_pi_command(drink_key, sugar_level):
    drink_info = DRINK_MAP.get(drink_key)
    if not drink_info or sugar_level not in ["0", "50", "100"]:
        return {"status": "error", "output": "Invalid drink or sugar selection"}

    drink_name = drink_info["name"]
    cmd_list = drink_info.get(sugar_level, ["echo", "dispensing"])
    binary = cmd_list[0]

    # PC Simulation check
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

    # Raspberry Pi Execution
    try:
        result = subprocess.run(
            cmd_list, capture_output=True, text=True, timeout=10
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


@app.route("/api/execute", methods=["POST"])
def run_action():
    data = request.get_json() or {}
    drink = data.get("drink")
    sugar = data.get("sugar")
    res = execute_pi_command(drink, sugar)
    return jsonify(res)


if __name__ == "__main__":
    # threaded=True improves mobile load times
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)