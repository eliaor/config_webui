"""
Example: Basic Configuration Editor with Presets & Admin Security

This script loads:
- One unified schema: schema.json
- One active config file: config.json
- Multiple full presets from the presets/ folder:
  * Development
  * Staging
  * Production
  * Testing (CI)
"""

import os
import sys

# Support running directly from source checkout or installed package
try:
    from configwebui import ConfigEditor
except ImportError:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
    from configwebui import ConfigEditor

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCHEMA_FILE = os.path.join(BASE_DIR, "schema.json")
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
PRESETS_DIR = os.path.join(BASE_DIR, "presets")

# Register multiple complete presets
PRESETS = {
    "Development": os.path.join(PRESETS_DIR, "development.json"),
    "Staging": os.path.join(PRESETS_DIR, "staging.json"),
    "Production (High Availability)": os.path.join(PRESETS_DIR, "production.json"),
    "Testing (CI)": os.path.join(PRESETS_DIR, "testing_ci.json"),
}

# Instantiate the ConfigEditor
editor = ConfigEditor(
    app_name="Enterprise Application Config",
    config_file=CONFIG_FILE,
    schema=SCHEMA_FILE,
    presets=PRESETS,
    default_preset="Development",
    admin_password="superadminsecret",
)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Loading unified schema from: {SCHEMA_FILE}")
    print(f"Target config file: {CONFIG_FILE}")
    print(f"Registered {len(PRESETS)} presets: {list(PRESETS.keys())}")
    print(f"Starting offline web editor on http://127.0.0.1:{port} ...")
    editor.run(host="0.0.0.0", port=port)
