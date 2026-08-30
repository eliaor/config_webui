# pyConfigWebUI

[![License](https://img.shields.io/github/license/lucienshawls/py-config-web-ui)](LICENSE)
[![Latest Release](https://img.shields.io/github/v/release/lucienshawls/py-config-web-ui)](https://github.com/lucienshawls/py-config-web-ui/releases/latest)
[![PyPI Version](https://img.shields.io/pypi/v/configwebui-lucien.svg)](https://pypi.org/project/configwebui-lucien/)
[![Python Versions](https://img.shields.io/pypi/pyversions/configwebui-lucien.svg)](https://pypi.org/project/configwebui-lucien/)

**pyConfigWebUI** turns your JSON Schema and config files into a fully interactive web-based editor — with preset switching, live validation, password-protected read-only fields, and optional task execution with streamed terminal output.

Zero internet required. Everything works offline and in air-gapped environments.

---

## Table of Contents

- [Key Features](#-key-features)
- [Installation](#-installation)
- [Quick Start (30 seconds)](#-quick-start-30-seconds)
- [Screenshots](#-screenshots)
- [Feature Guide](#-feature-guide)
  - [1. Configuration Presets](#1-configuration-presets)
  - [2. Admin Mode & Read-Only Fields](#2-admin-mode--read-only-fields)
  - [3. Collapsed Sections by Default](#3-collapsed-sections-by-default)
  - [4. Custom Business Validation](#4-custom-business-validation)
  - [5. Custom Storage (YAML, SQLite, etc.)](#5-custom-storage-yaml-sqlite-etc)
  - [6. Running a Task & Streaming Logs](#6-running-a-task--streaming-logs)
- [Example Projects](#-example-projects)
  - [web_service — Presets & Admin Mode](#demoweb_service--presets--admin-mode)
  - [data_pipeline — Custom Validation](#demodata_pipeline--custom-validation)
  - [model_training — Task Runner & Live Logs](#demomodel_training--task-runner--live-logs)
  - [reservation — Reservation Booking System](#demoreservation--reservation-booking-system)
- [API Reference](#-api-reference)
  - [ConfigEditor](#configeditor)
  - [ResultStatus](#resultstatus)
- [Offline Assurance](#-offline-assurance)
- [Building the Package](#-building-the-package)
- [License](#-license)

---

## 🌟 Key Features

| Feature | Description |
|---|---|
| 🔒 **100% Offline** | All CSS, JS, fonts, and icons are bundled in the package. No CDN, no internet needed. |
| 🎛️ **Configuration Presets** | Register named presets (dicts or JSON files). Switch with one click — even without admin rights. |
| 🛡️ **Admin Mode & Read-Only Locking** | Mark fields `"readOnly": true` in your schema. Guests see them locked; admin unlocks all. |
| 📂 **Collapsed Sections** | Mark sections `"options": {"collapsed": true}` in your schema to start them folded. |
| 📝 **Side-by-Side JSON Preview** | Live-updating formatted JSON preview next to the form editor. |
| 🔍 **Multi-Level Validation** | Real-time client-side schema validation + server-side jsonschema + custom `extra_validation_func`. |
| 🔌 **Flexible Storage** | Default JSON file persistence, or plug in `save_func`/`load_func` for YAML, SQLite, Redis, etc. |
| 🚀 **Task Runner** | Hook a `main_entry` callable to run background tasks with live terminal output streamed to the browser. |
| 🛑 **Graceful Lifecycle** | Terminate the editor from the UI navbar or with `Ctrl+C`. |

---

## 📦 Installation

### From PyPI

```bash
pip install configwebui-lucien
```

### From Source (development / offline)

```bash
git clone https://github.com/lucienshawls/py-config-web-ui.git
cd py-config-web-ui
pip install -r requirements.txt
```

---

## 🚀 Quick Start (30 seconds)

Create `app.py`:

```python
from configwebui import ConfigEditor

schema = {
    "title": "My App Config",
    "type": "object",
    "properties": {
        "server_host": {
            "title": "Host",
            "type": "string",
            "default": "127.0.0.1"
        },
        "server_port": {
            "title": "Port",
            "type": "integer",
            "default": 8080,
            "minimum": 1,
            "maximum": 65535
        },
        "debug_mode": {
            "title": "Debug Mode",
            "type": "boolean",
            "default": True
        },
    },
    "required": ["server_host", "server_port"],
}

editor = ConfigEditor(
    app_name="App Config Editor",
    config_file="config.json",   # Created automatically if missing
    schema=schema,
)

if __name__ == "__main__":
    editor.run(host="127.0.0.1", port=5000)
```

Run it:

```bash
python app.py
```

Open `http://127.0.0.1:5000` — the editor opens automatically in your browser. Changes are saved to `config.json` when you click **Save**.

---

## 📸 Screenshots

### Guest View (Read-Only Fields Protected)
Guests can edit regular fields; read-only (admin-locked) fields are greyed out and non-interactive.

![Guest View](docs/guest_view.png)

### Admin View (All Fields Unlocked)
After logging in with the admin password, all read-only fields become fully editable.

![Admin View](docs/admin_view.png)

---

## 📚 Feature Guide

### 1. Configuration Presets

Presets let users instantly switch between fully pre-defined parameter profiles — e.g. *Development*, *Staging*, *Production* — without having to change values manually. **Any user (even without admin rights) can apply and save presets.** Presets are trusted configurations: applying one overwrites read-only fields too (they come from a trusted source defined in code).

**In code** — pass a dict or a file path per preset:

```python
from configwebui import ConfigEditor

PRESETS = {
    "Development": {
        "server_host": "127.0.0.1",
        "server_port": 8000,
        "debug_mode": True,
    },
    "Staging": "presets/staging.json",     # Path to a JSON file
    "Production": "presets/production.json",
}

editor = ConfigEditor(
    app_name="Server Manager",
    config_file="config/active.json",
    schema=schema,
    presets=PRESETS,
    default_preset="Development",   # Load this if config file doesn't exist yet
)
```

**Recommended project structure:**

```
myproject/
├── app.py
├── schema/
│   └── schema.json        # One unified JSON Schema
└── config/
    ├── config.json        # Active config file (auto-saved)
    └── presets/
        ├── development.json
        ├── staging.json
        └── production.json
```

---

### 2. Admin Mode & Read-Only Fields

Protect sensitive or infrastructure-level variables by marking them `"readOnly": true` in your schema. Guest users see these fields greyed out and cannot change them. The admin password unlocks all read-only fields.

```python
schema = {
    "type": "object",
    "properties": {
        "app_title": {
            "title": "Application Title",
            "type": "string",
            "default": "My App"
        },
        "system_uuid": {
            "title": "System UUID (Protected)",
            "type": "string",
            "readOnly": True,      # <-- guests cannot change this
            "default": "SYS-9812-PROD"
        },
        "rate_limit": {
            "title": "Global Rate Limit (Protected)",
            "type": "integer",
            "readOnly": True,      # <-- locked for guests, editable by admin
            "default": 10000,
            "minimum": 100
        },
    }
}

editor = ConfigEditor(
    app_name="Secured App",
    schema=schema,
    config_file="config.json",
    admin_password="my-strong-password",   # Default: "admin"
)
```

> **Behaviour:** A guest can still apply presets (which may override read-only values) because presets come from trusted code. What guests **cannot** do is manually type new values into read-only fields.

---

### 3. Collapsed Sections by Default

For schemas with many sections, you can have some sections load **already collapsed** in the UI, so users only expand what they need. Use JSONEditor's `"options": {"collapsed": true}` on any object property in the schema:

```json
{
  "title": "App Config",
  "type": "object",
  "properties": {
    "server": {
      "title": "Server Settings",
      "type": "object",
      "properties": { ... }
    },
    "advanced": {
      "title": "Advanced Settings",
      "type": "object",
      "options": {
        "collapsed": true
      },
      "properties": { ... }
    },
    "system_protected": {
      "title": "System Controls (Read-Only)",
      "type": "object",
      "options": {
        "collapsed": true
      },
      "properties": { ... }
    }
  }
}
```

In Python, you can pass the schema directly as a dict:

```python
schema = {
    "type": "object",
    "properties": {
        "server": {
            "title": "Server Settings",
            "type": "object",
            "properties": {
                "host": {"title": "Host", "type": "string", "default": "localhost"},
                "port": {"title": "Port", "type": "integer", "default": 8080},
            }
        },
        "advanced": {
            "title": "Advanced Settings",
            "type": "object",
            "options": {"collapsed": True},   # <-- starts collapsed
            "properties": {
                "debug": {"title": "Debug Mode", "type": "boolean", "default": False},
                "log_level": {
                    "title": "Log Level",
                    "type": "string",
                    "enum": ["DEBUG", "INFO", "WARNING", "ERROR"],
                    "default": "INFO"
                },
            }
        }
    }
}
```

> This is also demonstrated in [`examples/web_service/schema/schema.json`](examples/web_service/schema/schema.json) where the *Caching*, *Feature Flags*, and *System Controls* sections start collapsed.

---

### 4. Custom Business Validation

Use `extra_validation_func` to enforce rules that go beyond what JSON Schema can express — like cross-field dependencies, conditional requirements, or domain-specific constraints. Return a `ResultStatus` with clear messages that are shown in the UI.

```python
from configwebui import ConfigEditor, ResultStatus

def validate_pipeline(config: dict) -> ResultStatus:
    """
    Custom rules:
    1. buffer_size must be at least 2x batch_size to prevent backpressure.
    2. If encryption is enabled, a KMS key is required.
    """
    proc = config.get("processing", {})
    batch = proc.get("batch_size", 0)
    buf   = proc.get("buffer_size", 0)

    if buf < batch * 2:
        return ResultStatus(
            False,
            f"Buffer size ({buf}) must be at least 2x batch size ({batch * 2})."
        )

    sec = config.get("security", {})
    if sec.get("enable_encryption") and not sec.get("kms_key_id", "").strip():
        return ResultStatus(False, "KMS Key ID is required when encryption is enabled.")

    return ResultStatus(True)   # All checks passed

editor = ConfigEditor(
    app_name="Pipeline Config",
    schema=schema,
    config_file="config/active.json",
    extra_validation_func=validate_pipeline,
)
```

The `ResultStatus` can carry one or multiple messages:

```python
def my_validator(config: dict) -> ResultStatus:
    result = ResultStatus(True)
    if config.get("port", 0) < 1024:
        result.set_status(False)
        result.add_message("Port must be >= 1024 for non-root users.")
    if not config.get("secret_key"):
        result.set_status(False)
        result.add_message("secret_key cannot be empty.")
    return result
```

---

### 5. Custom Storage (YAML, SQLite, etc.)

Override the default JSON file persistence by supplying `save_func` and `load_func`. This lets you store config in YAML, SQLite, Redis, a database, or anywhere else.

```python
import yaml
from configwebui import ConfigEditor, ResultStatus

CONFIG_PATH = "config/app.yaml"

def load_config() -> dict:
    """Load config from a YAML file."""
    try:
        with open(CONFIG_PATH, "r") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        return {}

def save_config(config: dict) -> ResultStatus:
    """Save config to a YAML file."""
    with open(CONFIG_PATH, "w") as f:
        yaml.safe_dump(config, f, sort_keys=False)
    return ResultStatus(True, "Saved to YAML successfully.")

editor = ConfigEditor(
    app_name="YAML Config Editor",
    schema=schema,
    load_func=load_config,
    save_func=save_config,
)
```

---

### 6. Running a Task & Streaming Logs

Hook a `main_entry` callable to your `ConfigEditor`. When the user clicks **Run Program** in the UI, the function executes in a background thread. All `print()` output (stdout + stderr) is captured and streamed live to the browser's terminal panel.

```python
import time
from configwebui import ConfigEditor, ResultStatus

def run_backup():
    """
    This function runs in a background thread when the user clicks Run.
    Access the live config from a file or pass it in yourself.
    """
    print("Starting database backup...")
    for partition in range(1, 4):
        time.sleep(1)
        print(f"  Backing up partition {partition}/3...")
    print("Backup complete!")
    return ResultStatus(True, "Backup succeeded.")

editor = ConfigEditor(
    app_name="Backup Manager",
    config_file="config/backup.json",
    schema=schema,
    main_entry=run_backup,
)
```

> **Tip:** Your `main_entry` function should read the active config from the config file (or wherever you store it) — the function runs independently as a background task.

---

## 📂 Example Projects

Each demo is a fully self-contained project folder. Everything lives in the `demo/` directory:

```
demo/
├── web_service/            # Presets + Admin Mode + Collapsed Sections
├── data_pipeline/          # Custom Cross-Field Validation
├── model_training/         # Background Task Runner + Live Log Streaming
└── reservation/            # End-to-end Reservation Booking System
```

All follow the same layout:

```
demo/<project>/
├── app.py                  # Run this to launch the editor
├── schema/
│   └── schema.json         # One unified JSON Schema for the whole project
└── config/
    ├── config.json         # Active configuration (auto-saved on Save)
    └── presets/
        └── *.json          # Complete preset configurations
```

---

### `demo/web_service/` — Presets & Admin Mode

**Run:**
```bash
python demo/web_service/app.py
```

**What it demonstrates:**
- 4 complete preset environments: *Development*, *Staging*, *Production (High Availability)*, *Testing (CI)*
- `"readOnly": true` fields for cluster UUID, environment tier, rate limits, and license key → locked for guests, unlocked for admin
- **Collapsed sections** — *Caching*, *Feature Flags*, and *System Controls* all start collapsed by default using `"options": {"collapsed": true}` in the schema
- Admin password: `superadminsecret`

**Schema sections:**
| Section | Collapsed? | Admin-only? |
|---|---|---|
| Server & Network Settings | No (expanded) | No |
| Database Settings | No (expanded) | No |
| Caching & Sessions | **Yes** | No |
| Logging & Diagnostics | No (expanded) | No |
| Feature Flags | **Yes** | No |
| System & Admin Controls | **Yes** | **Read-only** |

---

### `demo/data_pipeline/` — Custom Validation

**Run:**
```bash
python demo/data_pipeline/app.py
```

**What it demonstrates:**
- Custom `extra_validation_func` enforcing two business rules:
  1. `buffer_size` must be ≥ 2× `batch_size` to prevent backpressure drops
  2. `kms_key_id` is required whenever `enable_encryption` is `true`
- 3 presets: *Batch ETL (S3)*, *Realtime Streaming (Kafka)*, *Memory-Optimized Edge*
- Read-only fields for `max_throughput_mb_s` and `pipeline_cluster_id`
- Admin password: `etladminsecret`

**Validation logic:**
```python
def validate_pipeline_logic(config: dict) -> ResultStatus:
    proc  = config.get("processing", {})
    batch = proc.get("batch_size", 0)
    buf   = proc.get("buffer_size", 0)
    if buf < batch * 2:
        return ResultStatus(False, f"Buffer ({buf}) must be ≥ 2× batch ({batch*2}).")
    sec = config.get("security", {})
    if sec.get("enable_encryption") and not sec.get("kms_key_id", "").strip():
        return ResultStatus(False, "KMS Key ID required when encryption is on.")
    return ResultStatus(True)
```

---

### `demo/model_training/` — Task Runner & Live Logs

**Run:**
```bash
python demo/model_training/app.py
```

**What it demonstrates:**
- `main_entry=train_model` — click **Run Program** in the UI to start a simulated training loop
- `trainer.py` prints live loss/accuracy metrics that stream to the browser terminal in real time
- 3 presets: *Quick Experiment (3 Epochs)*, *Standard Training (ResNet-50)*, *High Accuracy GPU Cluster*
- Read-only fields: `gpu_quota_limit`, `cluster_id`
- Admin password: `gpuadminsecret`

**How the task runner is hooked up:**
```python
from trainer import train_model

editor = ConfigEditor(
    app_name="ML Training Manager",
    config_file=CONFIG_FILE,
    schema=SCHEMA_FILE,
    presets=PRESETS,
    main_entry=train_model,   # Called when user clicks "Run Program"
)
```

---

### `demo/reservation/` — Reservation Booking System

An end-to-end interactive demo of a reservation/appointment booking system.

**Run:**
```bash
python demo/reservation/demo_ui.py
```

**Structure:**
```
demo/reservation/
├── demo_ui.py          # Web UI launcher
├── demo_main.py        # Backend worker (simulates booking logic)
├── schema/
│   └── schema.json     # Unified schema for the reservation app
└── config/
    ├── config.json     # Active configuration
    └── presets/
        ├── default.json
        ├── christmas.json   # Seasonal capacity/pricing override
        └── vip.json         # VIP-priority booking config
```

**How to explore:**
1. Open `http://localhost:5000/` in your browser
2. Try switching presets (*Christmas Special*, *VIP Applicant*) — applies and saves immediately
3. Notice the `system_settings` section is locked for guests (admin password: `admin`)
4. Log in as admin to edit the locked fields
5. Click **Run Program** to simulate a reservation booking — watch the output stream live

---

## 🛠️ API Reference

### `ConfigEditor`

```python
from configwebui import ConfigEditor

editor = ConfigEditor(
    app_name="My Config Editor",    # str: Title shown in navbar and browser tab
    config_file="config.json",      # str | None: path to config JSON file
    schema=schema,                  # dict | str | None: JSON Schema dict or path to .json file
    config=None,                    # dict | None: initial config (overrides file)
    presets={                       # dict[str, dict|str] | None: named preset configs
        "Default": {...},
        "Production": "presets/prod.json",
    },
    default_preset="Default",       # str | None: preset to load if config file is missing
    admin_password="admin",         # str: password for Admin Login
    extra_validation_func=None,     # Callable | None: func(config) -> ResultStatus | bool
    save_func=None,                 # Callable | None: func(config) -> ResultStatus | bool
    load_func=None,                 # Callable | None: func() -> dict
    main_entry=None,                # Callable | None: function to run when user clicks "Run"
)

editor.run(host="127.0.0.1", port=5000)
```

#### Constructor Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `app_name` | `str` | `"Config Editor"` | Display name in the navbar and browser title. |
| `config_file` | `str \| None` | `None` | Path to the active config JSON file. Created automatically if it doesn't exist. |
| `schema` | `dict \| str \| None` | `None` | JSON Schema as a Python dict, or a file path to a `.json` schema file. |
| `config` | `dict \| None` | `None` | Override config loaded from file with this dict. |
| `presets` | `dict[str, dict \| str] \| None` | `None` | Named configuration presets. Values can be dicts or file paths. |
| `default_preset` | `str \| None` | `None` | Preset to apply on first launch (when no config file exists yet). |
| `admin_password` | `str` | `"admin"` | Password for Admin Login. Change from the default in production. |
| `extra_validation_func` | `Callable \| None` | `None` | Custom validation: `func(config: dict) -> ResultStatus \| bool`. Called on every Save. |
| `save_func` | `Callable \| None` | `None` | Custom save handler: `func(config: dict) -> ResultStatus \| bool`. Replaces the default JSON file write. |
| `load_func` | `Callable \| None` | `None` | Custom load handler: `func() -> dict`. Replaces reading from `config_file`. |
| `main_entry` | `Callable \| None` | `None` | Task function executed when user clicks **Run Program** in the UI. Runs in a background thread. |

#### Methods

| Method | Returns | Description |
|---|---|---|
| `run(host, port)` | — | Starts the web server and opens a browser. |
| `get_config()` | `dict` | Returns a deep copy of the current config. |
| `set_config(config, ...)` | `ResultStatus` | Validates and updates the active config. |
| `get_schema(is_admin)` | `dict` | Returns schema; if `is_admin=True`, `readOnly` flags are stripped. |
| `set_schema(schema)` | — | Replaces the active JSON schema. |
| `add_preset(name, preset)` | — | Registers a new preset. |
| `get_presets()` | `dict[str, dict]` | Returns all registered presets. |
| `get_preset_names()` | `list[str]` | Returns the list of preset names. |
| `apply_preset(name, save_file)` | `ResultStatus` | Applies a preset to the active config. |
| `check(config, ...)` | `ResultStatus` | Validates a config dict without saving. |
| `save(config)` | `ResultStatus` | Persists the config to `config_file` or `save_func`. |
| `load()` | `dict` | Reloads config from file or `load_func`. |
| `verify_admin_password(password)` | `bool` | Checks if the password matches. |
| `set_admin_password(password)` | — | Updates the admin password at runtime. |
| `stop_server()` | — | Stops the Flask server. |
| `clean_up()` | — | Shuts down server threads and restores stdout/stderr. |

---

### `ResultStatus`

Returned by all validation and save operations. Carry success/failure state and human-readable messages that are shown in the browser UI.

```python
from configwebui import ResultStatus

# Simple success
result = ResultStatus(True)

# Success with a message
result = ResultStatus(True, "Configuration saved successfully.")

# Failure with a reason
result = ResultStatus(False, "Port must be between 1 and 65535.")

# Multiple messages (build up errors)
result = ResultStatus(True)
result.set_status(False)
result.add_message("Port is out of range.")
result.add_message("Database host cannot be empty.")

# Read the result
result.get_status()     # -> bool
result.get_messages()   # -> list[str]
```

---

## 🛡️ Offline Assurance

**pyConfigWebUI** does not load anything from external CDNs or the internet. All frontend assets are bundled inside the package at `configwebui/static/`:

| Asset | Version |
|---|---|
| Bootstrap | 5.3.3 CSS + JS |
| JSONEditor | 2.15.1 JS |
| jQuery Slim | 3.7.1 JS |
| FontAwesome | 5.15.4 CSS + Webfonts (`.woff2`, `.woff`, `.ttf`, `.eot`, `.svg`) |

Verify full offline compliance by running:

```bash
python -m unittest tests/test_offline.py -v
```

This test checks that no `<script src>` or `<link href>` in the HTML template references an external URL.

---

## 🔨 Building the Package

```bash
# Clean and build both sdist (.tar.gz) and wheel (.whl)
rm -rf dist build
python -m build --no-isolation
```

Output in `dist/`:
- `configwebui_lucien-<version>-py3-none-any.whl`
- `configwebui_lucien-<version>.tar.gz`

---

## 🧪 Running the Test Suite

```bash
# Run all 27 unit tests
python -m unittest discover -s tests -v

# Run offline asset tests only
python -m unittest tests/test_offline.py -v

# Run browser interaction test (requires a running server)
python tests/test_browser_ui.py
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
