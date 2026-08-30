"""
Example 1: Basic Usage of pyConfigWebUI

This script demonstrates the simplest setup:
1. Define a JSON Schema for application settings.
2. Instantiate ConfigEditor with a target JSON file path.
3. Launch the web UI (completely offline).
"""

import os
try:
    from configwebui import ConfigEditor
except ImportError:
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
    from configwebui import ConfigEditor

# Define standard JSON Schema
SCHEMA = {
    "title": "Server Configuration",
    "type": "object",
    "properties": {
        "host": {
            "title": "Host Address",
            "type": "string",
            "default": "127.0.0.1",
            "description": "IP or hostname to bind server",
        },
        "port": {
            "title": "Port Number",
            "type": "integer",
            "default": 8080,
            "minimum": 1,
            "maximum": 65535,
        },
        "debug": {
            "title": "Debug Mode",
            "type": "boolean",
            "default": False,
            "description": "Enable verbose logging and debug features",
        },
        "max_workers": {
            "title": "Worker Threads",
            "type": "integer",
            "default": 4,
            "minimum": 1,
            "maximum": 32,
        },
    },
    "required": ["host", "port"],
}

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "output_basic_config.json")

# Create editor instance
editor = ConfigEditor(
    app_name="Basic Server Config",
    config_file=CONFIG_FILE,
    schema=SCHEMA,
)

if __name__ == "__main__":
    print(f"Starting config editor on http://127.0.0.1:5000 ...")
    print(f"Config will be saved to: {CONFIG_FILE}")
    editor.run(host="127.0.0.1", port=5000)
