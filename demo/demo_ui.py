import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from demo import demo_main
try:
    from configwebui import ConfigEditor
except ImportError:
    from src.configwebui import ConfigEditor

CONFIG_FILE = "demo/config/main.json"
SCHEMA_FILE = "demo/schema/main.json"

PRESETS = {
    "Default": "demo/presets/default.json",
    "Christmas Special": "demo/presets/christmas.json",
    "VIP Applicant": "demo/presets/vip.json",
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
