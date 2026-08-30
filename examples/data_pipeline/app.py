"""
Example 2: Data Pipeline Configuration with Custom Business Rule Validation
"""

import os
import sys

try:
    from configwebui import ConfigEditor, ResultStatus
except ImportError:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
    from configwebui import ConfigEditor, ResultStatus

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCHEMA_FILE = os.path.join(BASE_DIR, "schema", "schema.json")
CONFIG_FILE = os.path.join(BASE_DIR, "config", "config.json")
PRESETS_DIR = os.path.join(BASE_DIR, "config", "presets")

PRESETS = {
    "Batch ETL (S3)": os.path.join(PRESETS_DIR, "batch_etl.json"),
    "Realtime Streaming (Kafka)": os.path.join(PRESETS_DIR, "realtime_streaming.json"),
    "Memory-Optimized Edge": os.path.join(PRESETS_DIR, "memory_optimized.json"),
}


def validate_pipeline_logic(config: dict) -> ResultStatus:
    """
    Custom business validations:
    1. Buffer size must be at least double the batch size.
    2. If encryption is enabled, KMS key ID is required.
    """
    proc = config.get("processing", {})
    batch = proc.get("batch_size", 0)
    buf = proc.get("buffer_size", 0)

    if buf < batch * 2:
        return ResultStatus(
            False,
            f"Buffer size ({buf}) must be at least 2x batch size ({batch * 2}) to prevent backpressure drops.",
        )

    sec = config.get("security", {})
    if sec.get("enable_encryption") and not sec.get("kms_key_id", "").strip():
        return ResultStatus(
            False,
            "KMS Key ID cannot be empty when encryption is enabled.",
        )

    return ResultStatus(True)


editor = ConfigEditor(
    app_name="Data Pipeline Config",
    config_file=CONFIG_FILE,
    schema=SCHEMA_FILE,
    presets=PRESETS,
    default_preset="Batch ETL (S3)",
    admin_password="etladminsecret",
    extra_validation_func=validate_pipeline_logic,
)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Loaded schema: {SCHEMA_FILE}")
    print(f"Target config: {CONFIG_FILE}")
    print(f"Presets: {list(PRESETS.keys())}")
    print(f"Starting Data Pipeline Editor on http://127.0.0.1:{port} ...")
    editor.run(host="0.0.0.0", port=port)
