# pyConfigWebUI

[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/lucienshawls/py-config-web-ui)
[![Build Status](https://github.com/lucienshawls/py-config-web-ui/actions/workflows/release.yml/badge.svg)](https://github.com/lucienshawls/py-config-web-ui/actions/workflows/release.yml)
[![License](https://img.shields.io/github/license/lucienshawls/py-config-web-ui)](LICENSE)
[![Latest Release Tag](https://img.shields.io/github/v/release/lucienshawls/py-config-web-ui)](https://github.com/lucienshawls/py-config-web-ui/releases/latest)
[![Latest PyPI Version](https://img.shields.io/pypi/v/configwebui-lucien.svg)](https://pypi.org/project/configwebui-lucien/)

A modern, simple, web-based configuration editor for Python applications.

This package provides an interactive web UI for editing a single global configuration file (JSON/YAML/Dict) with preset configuration switching, JSON schema validation, offline capabilities, admin mode for unlocking read-only variables, and real-time program execution logs.

---

## Key Features

- **Single Global Configuration File**: Directly edit and persist a specified configuration file with real-time UI synchronization.
- **100% Offline Capable**: All CSS, JavaScript, icons, and web fonts are bundled locally. **Zero internet connection or external CDN required.**
- **Configuration Presets**: Easily define and switch between preset configurations (e.g. *Default*, *Production*, *Testing*) to overwrite the editor state in one click.
- **Admin Login & Read-Only Variable Override**:
  - Secure sensitive or system parameters with `"readOnly": true` in the schema.
  - Guest users see read-only fields disabled.
  - Log in via the **Admin Login** button to unlock and freely modify all read-only fields.
- **Real-Time Schema Validation**: Automatic form generation and validation directly against your standard [JSON Schema](https://json-schema.org/), plus support for custom backend validation.
- **Live JSON Preview**: Synchronized interactive JSON code view with expand/collapse options and automatic masking for password fields.
- **Interactive Terminal Output**: Launch your main Python entry point in a background thread and view real-time captured stdout/stderr directly in the browser.
- **Graceful Lifecycle Management**: Terminate the local web server cleanly directly from the UI or via keyboard interrupt.

---

## Quick Start

### 1. Installation

Install via pip from PyPI:
```shell
pip install configwebui-lucien
```

Or install from source:
```shell
git clone https://github.com/lucienshawls/py-config-web-ui
cd py-config-web-ui
pip install -r requirements.txt
```

### 2. Try the Demo

Run the included demo:
```shell
python demo/demo_ui.py
```
Open your browser at `http://localhost:5000/` (or the URL printed in the terminal).

---

## Usage Example

```python
from configwebui import ConfigEditor, ResultStatus


# 1. Define JSON Schema (with readOnly fields if needed)
schema = {
    "title": "Application Configuration",
    "type": "object",
    "properties": {
        "server_port": {
            "title": "Server Port",
            "type": "integer",
            "default": 8080,
        },
        "debug_mode": {"title": "Debug Mode", "type": "boolean", "default": False},
        "api_endpoint": {
            "title": "API Endpoint (Read-Only)",
            "type": "string",
            "readOnly": True,
            "default": "https://api.internal.production",
        },
    },
    "required": ["server_port"],
}

# 2. Define optional main entry point
def my_main_program():
    print("Main program starting...")
    # Your application logic reading from config/main.json
    print("Application executed successfully.")
    return ResultStatus(True)

# 3. Instantiate ConfigEditor
editor = ConfigEditor(
    app_name="My App Config",
    config_file="config/main.json",
    schema=schema,
    presets={
        "Default": "presets/default.json",
        "Production": {"server_port": 443, "debug_mode": False},
    },
    admin_password="secretadminpassword",
    main_entry=my_main_program,
)

# 4. Start the Web UI
if __name__ == "__main__":
    editor.run(host="127.0.0.1", port=5000)
```

---

## Architecture & How It Works

```
JSON Schema / File ──► ConfigEditor (Presets + Admin Mode) ──► Local Offline Web UI
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
             Global Config File   Main Entry (Runner)
```

1. **`ConfigEditor`**: The core orchestrator that binds your configuration file, schema, presets, admin password, and main application runner into a local Flask web application.
2. **Presets**: Stored in memory or loaded from JSON files. Selecting a preset overwrites the active editor config.
3. **Admin Mode**:
   - Guests receive the standard schema with `readOnly: true` applied.
   - Admin authentication sets an encrypted session. In Admin mode, `readOnly` flags are dynamically stripped from the schema, enabling editing of all locked properties.
4. **ProgramRunner**: Hijacks stdout and stderr for the main entry execution thread, providing real-time log polling and terminal output in the browser.

---

## API Reference: `ConfigEditor`

```python
ConfigEditor(
    app_name: str = "Config Editor",
    config_file: str | None = None,
    schema: dict | str | None = None,
    config: dict | None = None,
    presets: dict[str, dict | str] | None = None,
    default_preset: str | None = None,
    admin_password: str = "admin",
    extra_validation_func: Callable | None = None,
    save_func: Callable | None = None,
    load_func: Callable | None = None,
    main_entry: Callable | None = None,
)
```

### Parameters

- `app_name` (*str*): Display name in the web interface title and navigation bar.
- `config_file` (*str | None*): Path to the global configuration file to edit and save.
- `schema` (*dict | str | None*): JSON schema dictionary or path to a JSON schema file.
- `config` (*dict | None*): Initial configuration dictionary (defaults to reading `config_file` or generating defaults from `schema`).
- `presets` (*dict[str, dict | str] | None*): Mapping of preset names to configuration dictionaries or preset JSON file paths.
- `default_preset` (*str | None*): Name of the preset to load initially if no config file exists.
- `admin_password` (*str*): Password for logging into Admin Mode (default: `"admin"`).
- `extra_validation_func` (*Callable | None*): Custom validation callable `func(config) -> ResultStatus | bool`.
- `save_func` (*Callable | None*): Custom save function `func(config) -> ResultStatus | bool`.
- `load_func` (*Callable | None*): Custom load function `func() -> dict`.
- `main_entry` (*Callable | None*): Main entry point to execute when "Launch main program" is clicked.

---

## License

This project is licensed under the [MIT License](LICENSE).
