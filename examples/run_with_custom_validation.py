"""
Example: Unified Config with Custom Business Rule Validation

This demo adds custom multi-field validation (`extra_validation_func`)
to the unified schema (schema.json) and presets.
"""

import os
import sys

try:
    from configwebui import ConfigEditor, ResultStatus
except ImportError:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
    from configwebui import ConfigEditor, ResultStatus

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCHEMA_FILE = os.path.join(BASE_DIR, "schema.json")
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
PRESETS_DIR = os.path.join(BASE_DIR, "presets")

PRESETS = {
    "Development": os.path.join(PRESETS_DIR, "development.json"),
    "Staging": os.path.join(PRESETS_DIR, "staging.json"),
    "Production (High Availability)": os.path.join(PRESETS_DIR, "production.json"),
    "Testing (CI)": os.path.join(PRESETS_DIR, "testing_ci.json"),
}


def validate_enterprise_rules(config: dict) -> ResultStatus:
    """
    Custom business validations:
    1. If caching is enabled with Redis backend, redis_url must start with 'redis://' or 'rediss://'.
    2. In Production tier, TLS must be enabled and log level must not be DEBUG.
    3. If database engine is sqlite, database_name must end with .db or be :memory:.
    """
    caching = config.get("caching", {})
    if caching.get("enabled") and caching.get("backend") == "redis":
        redis_url = caching.get("redis_url", "")
        if not (redis_url.startswith("redis://") or redis_url.startswith("rediss://")):
            return ResultStatus(
                False,
                "Redis URL must begin with 'redis://' or 'rediss://' when Redis caching is enabled.",
            )

    system = config.get("system_protected", {})
    tier = system.get("environment_tier", "")
    server = config.get("server", {})
    logging_cfg = config.get("logging", {})

    if tier == "Production":
        if not server.get("enable_tls"):
            return ResultStatus(
                False,
                "TLS/HTTPS must be enabled (enable_tls = true) in Production environment!",
            )
        if logging_cfg.get("log_level") == "DEBUG":
            return ResultStatus(
                False,
                "Log level DEBUG is not allowed in Production tier for performance and security reasons.",
            )

    db = config.get("database", {})
    if db.get("engine") == "sqlite":
        db_name = db.get("database_name", "")
        if not (db_name.endswith(".db") or db_name == ":memory:"):
            return ResultStatus(
                False,
                f"SQLite database name must end in '.db' or be ':memory:' (got: '{db_name}').",
            )

    return ResultStatus(True)


editor = ConfigEditor(
    app_name="Enterprise Config (Validated)",
    config_file=CONFIG_FILE,
    schema=SCHEMA_FILE,
    presets=PRESETS,
    default_preset="Development",
    admin_password="superadminsecret",
    extra_validation_func=validate_enterprise_rules,
)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print("Starting Config Editor with Custom Business Validation...")
    print("Try triggering validation rules:")
    print("  - Selecting Production preset with enable_tls = False")
    print("  - Setting invalid Redis URL scheme")
    print("  - Setting invalid SQLite database filename")
    editor.run(host="0.0.0.0", port=port)
