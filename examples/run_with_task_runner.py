"""
Example: Unified Config with Program Execution & Live Terminal Logs

Demonstrates connecting a main task entry point (`main_entry`) that reads
the unified `config.json` and streams live server initialization logs to the browser.
"""

import json
import os
import sys
import time

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


def start_application_service():
    """
    Simulated application bootstrap worker.
    Reads current config.json and prints startup progress.
    """
    print("=" * 60)
    print(">>> INITIALIZING APPLICATION BACKEND SERVICE")
    print("=" * 60)

    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = json.load(f)
    else:
        print("[ERROR] Configuration file not found!")
        return ResultStatus(False, "Configuration file missing.")

    server = cfg.get("server", {})
    db = cfg.get("database", {})
    cache = cfg.get("caching", {})
    system = cfg.get("system_protected", {})

    print(f"[*] Environment Tier : {system.get('environment_tier', 'Unknown')}")
    print(f"[*] Cluster UUID     : {system.get('cluster_uuid', 'N/A')}")
    print(f"[*] Binding Address  : {server.get('host', '0.0.0.0')}:{server.get('port', 8080)}")
    print(f"[*] Worker Count     : {server.get('workers', 1)}")
    print(f"[*] TLS / HTTPS      : {'Enabled' if server.get('enable_tls') else 'Disabled'}")

    time.sleep(0.6)
    print(f"[*] Connecting to {db.get('engine')} database at '{db.get('host')}:{db.get('port')}' (pool: {db.get('pool_size')})...")
    time.sleep(0.8)
    print("[+] Database connection pool established.")

    time.sleep(0.5)
    if cache.get("enabled"):
        print(f"[*] Connecting to {cache.get('backend')} cache store (TTL: {cache.get('default_ttl_seconds')}s)...")
        time.sleep(0.6)
        print("[+] Cache connected successfully.")
    else:
        print("[-] Caching disabled.")

    print("\n[+] All backend services initialized.")
    print("[+] Application ready to accept incoming traffic.")
    print("=" * 60)
    return ResultStatus(True, "Service booted successfully.")


editor = ConfigEditor(
    app_name="Enterprise Service Manager",
    config_file=CONFIG_FILE,
    schema=SCHEMA_FILE,
    presets=PRESETS,
    default_preset="Development",
    admin_password="superadminsecret",
    main_entry=start_application_service,
)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting Enterprise Service Manager on http://127.0.0.1:{port} ...")
    print("Modify settings, apply presets, and execute the service to view real-time logs.")
    editor.run(host="0.0.0.0", port=port)
