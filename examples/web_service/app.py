"""
Example 1: Enterprise Web Service Configuration Manager
"""

import os
import sys

try:
    from configwebui import ConfigEditor
except ImportError:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
    from configwebui import ConfigEditor

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCHEMA_FILE = os.path.join(BASE_DIR, "schema", "schema.json")
CONFIG_FILE = os.path.join(BASE_DIR, "config", "config.json")
PRESETS_DIR = os.path.join(BASE_DIR, "config", "presets")

PRESETS = {
    "Development": os.path.join(PRESETS_DIR, "development.json"),
    "Staging": os.path.join(PRESETS_DIR, "staging.json"),
    "Production (High Availability)": os.path.join(PRESETS_DIR, "production.json"),
    "Testing (CI)": os.path.join(PRESETS_DIR, "testing_ci.json"),
}

editor = ConfigEditor(
    app_name="Web Service Config",
    config_file=CONFIG_FILE,
    schema=SCHEMA_FILE,
    presets=PRESETS,
    default_preset="Development",
    admin_password="superadminsecret",
)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Loaded schema: {SCHEMA_FILE}")
    print(f"Target config: {CONFIG_FILE}")
    print(f"Presets: {list(PRESETS.keys())}")
    print(f"Starting web editor on http://127.0.0.1:{port} ...")
    editor.run(host="0.0.0.0", port=port)
