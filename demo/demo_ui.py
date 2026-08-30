import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from demo import demo_main
try:
    from configwebui import ConfigEditor
except ImportError:
    from src.configwebui import ConfigEditor

DEMO_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(DEMO_DIR, "config", "config.json")
SCHEMA_FILE = os.path.join(DEMO_DIR, "schema", "schema.json")
PRESETS_DIR = os.path.join(DEMO_DIR, "config", "presets")

PRESETS = {
    "Default": os.path.join(PRESETS_DIR, "default.json"),
    "Christmas Special": os.path.join(PRESETS_DIR, "christmas.json"),
    "VIP Applicant": os.path.join(PRESETS_DIR, "vip.json"),
}

CONFIG_EDITOR = ConfigEditor(
    app_name="Demo UI",
    config_file=CONFIG_FILE,
    schema=SCHEMA_FILE,
    presets=PRESETS,
    admin_password="admin",
    main_entry=demo_main.main,
)


def ui():
    port = int(os.environ.get("PORT", 5000))
    CONFIG_EDITOR.run(host="0.0.0.0", port=port)


if __name__ == "__main__":
    ui()
