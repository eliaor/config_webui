"""
Reservation Booking System — Demo UI launcher.
Run:  python demo/reservation/demo_ui.py
"""
import os
import sys

# Allow running from repo root or from inside this directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

try:
    from configwebui import ConfigEditor
except ImportError:
    sys.path.insert(0, os.path.join(BASE_DIR, "..", "..", "..", "src"))
    from configwebui import ConfigEditor

# Import the backend worker from the same directory
sys.path.insert(0, BASE_DIR)
from demo_main import main as reservation_main

CONFIG_FILE = os.path.join(BASE_DIR, "config", "config.json")
SCHEMA_FILE = os.path.join(BASE_DIR, "schema", "schema.json")
PRESETS_DIR = os.path.join(BASE_DIR, "config", "presets")

PRESETS = {
    "Default": os.path.join(PRESETS_DIR, "default.json"),
    "Christmas Special": os.path.join(PRESETS_DIR, "christmas.json"),
    "VIP Applicant": os.path.join(PRESETS_DIR, "vip.json"),
}

editor = ConfigEditor(
    app_name="Reservation Demo",
    config_file=CONFIG_FILE,
    schema=SCHEMA_FILE,
    presets=PRESETS,
    admin_password="admin",
    main_entry=reservation_main,
)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Loaded schema: {SCHEMA_FILE}")
    print(f"Target config: {CONFIG_FILE}")
    print(f"Starting Reservation Demo on http://127.0.0.1:{port} ...")
    editor.run(host="0.0.0.0", port=port)
