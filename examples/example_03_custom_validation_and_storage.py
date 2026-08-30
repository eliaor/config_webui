"""
Example 3: Custom Validation and Storage Handlers

This script demonstrates:
1. Adding cross-field and business rule validation (`extra_validation_func`).
2. Providing custom save (`save_func`) and load (`load_func`) handlers.
   (Useful for persisting to YAML, SQLite, Redis, or cloud config stores).
"""

import json
import os
try:
    from configwebui import ConfigEditor, ResultStatus
except ImportError:
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
    from configwebui import ConfigEditor, ResultStatus

SCHEMA = {
    "title": "Data Pipeline Configuration",
    "type": "object",
    "properties": {
        "batch_size": {
            "title": "Batch Size",
            "type": "integer",
            "default": 500,
            "minimum": 1,
            "maximum": 10000,
        },
        "buffer_size": {
            "title": "Buffer Size",
            "type": "integer",
            "default": 2000,
            "minimum": 1,
            "maximum": 50000,
        },
        "compression": {
            "title": "Compression Algorithm",
            "type": "string",
            "enum": ["none", "gzip", "zstd", "snappy"],
            "default": "zstd",
        },
        "enable_encryption": {
            "title": "Enable Encryption",
            "type": "boolean",
            "default": True,
        },
        "encryption_key_id": {
            "title": "Encryption Key ID",
            "type": "string",
            "default": "kms-key-99128",
        },
    },
    "required": ["batch_size", "buffer_size"],
}

# In-memory storage mock (could be SQLite, Redis, remote API, etc.)
STORAGE = {
    "batch_size": 500,
    "buffer_size": 2000,
    "compression": "zstd",
    "enable_encryption": True,
    "encryption_key_id": "kms-key-99128",
}


def custom_validator(config: dict) -> ResultStatus:
    """
    Business logic validation:
    1. Buffer size must be at least 2x the batch size.
    2. If encryption is enabled, encryption_key_id must not be empty.
    """
    batch = config.get("batch_size", 0)
    buffer = config.get("buffer_size", 0)
    if buffer < batch * 2:
        return ResultStatus(
            False,
            f"Buffer size ({buffer}) must be at least double the batch size ({batch} * 2 = {batch * 2})!",
        )

    if config.get("enable_encryption") and not config.get("encryption_key_id", "").strip():
        return ResultStatus(
            False,
            "Encryption Key ID is required when encryption is enabled.",
        )

    return ResultStatus(True)


def custom_load() -> dict:
    """Load config from storage."""
    print("[Custom Storage] Loading configuration...")
    return STORAGE


def custom_save(config: dict) -> ResultStatus:
    """Save config to storage."""
    print(f"[Custom Storage] Persisting configuration: {config}")
    STORAGE.clear()
    STORAGE.update(config)
    return ResultStatus(True, "Saved to custom storage successfully.")


editor = ConfigEditor(
    app_name="Data Pipeline Config",
    schema=SCHEMA,
    extra_validation_func=custom_validator,
    load_func=custom_load,
    save_func=custom_save,
)

if __name__ == "__main__":
    print("Custom Validation & Storage Handlers Demo")
    print("- Try setting Buffer Size smaller than 2x Batch Size to see validation in action!")
    print("- Changes are saved via the custom `save_func` callback.")
    editor.run(host="127.0.0.1", port=5000)
