# pyConfigWebUI Examples

This directory contains standalone, ready-to-run examples demonstrating different features of **pyConfigWebUI**.

## Examples Overview

| File | Description | Key Features Demonstrated |
|---|---|---|
| [`example_01_basic_usage.py`](example_01_basic_usage.py) | Minimal quick start | JSON Schema form generation, file auto-save, split view |
| [`example_02_presets_and_admin_mode.py`](example_02_presets_and_admin_mode.py) | Configuration Presets & Admin Security | Named presets switching, `readOnly` fields, Admin login & unlock |
| [`example_03_custom_validation_and_storage.py`](example_03_custom_validation_and_storage.py) | Advanced validation & storage | Custom cross-field validation (`extra_validation_func`), `save_func`, `load_func` |
| [`example_04_task_execution_with_logs.py`](example_04_task_execution_with_logs.py) | Background task execution | Attaching `main_entry`, streaming stdout/stderr terminal logs |
| [`example_05_rich_schema_forms.py`](example_05_rich_schema_forms.py) | Rich Schema Controls | Nested objects, dynamic array tables, enums, passwords, textareas |

## Running the Examples

Ensure requirements or package is installed:
```bash
pip install -r requirements.txt
```

Run any example:
```bash
python examples/example_01_basic_usage.py
python examples/example_02_presets_and_admin_mode.py
python examples/example_03_custom_validation_and_storage.py
python examples/example_04_task_execution_with_logs.py
python examples/example_05_rich_schema_forms.py
```

Then open your browser at the URL shown in terminal (default: `http://localhost:5000/`).
