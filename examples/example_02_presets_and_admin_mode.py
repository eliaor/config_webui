"""
Example 2: Presets and Admin Mode

This script demonstrates:
1. Defining named presets (in-memory dicts and/or file paths).
2. Locking sensitive infrastructure settings with `readOnly: true`.
3. Unlocking and editing locked settings by logging in with an Admin password.
"""

import os
try:
    from configwebui import ConfigEditor
except ImportError:
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
    from configwebui import ConfigEditor

SCHEMA = {
    "title": "Database & Cluster Configuration",
    "type": "object",
    "properties": {
        "cluster_name": {
            "title": "Cluster Name",
            "type": "string",
            "default": "prod-cluster-01",
        },
        "system_cluster_id": {
            "title": "System Cluster ID (Protected)",
            "type": "string",
            "default": "SYS-9821-X",
            "readOnly": True,
            "description": "Critical system identifier. Requires Admin login to modify.",
        },
        "max_connections": {
            "title": "Max Connections",
            "type": "integer",
            "default": 100,
            "minimum": 10,
            "maximum": 5000,
        },
        "replica_count": {
            "title": "Replica Count (Protected)",
            "type": "integer",
            "default": 3,
            "readOnly": True,
            "description": "Number of active cluster replicas. Admin only.",
        },
        "read_timeout_seconds": {
            "title": "Read Timeout (seconds)",
            "type": "number",
            "default": 5.0,
        },
    },
    "required": ["cluster_name", "system_cluster_id", "max_connections"],
}

# Define multiple configuration presets
PRESETS = {
    "Development": {
        "cluster_name": "dev-local-01",
        "system_cluster_id": "SYS-0001-DEV",
        "max_connections": 20,
        "replica_count": 1,
        "read_timeout_seconds": 30.0,
    },
    "Staging": {
        "cluster_name": "staging-cluster-01",
        "system_cluster_id": "SYS-0050-STAGE",
        "max_connections": 100,
        "replica_count": 2,
        "read_timeout_seconds": 10.0,
    },
    "Production": {
        "cluster_name": "prod-cluster-east-01",
        "system_cluster_id": "SYS-9999-PROD",
        "max_connections": 1000,
        "replica_count": 5,
        "read_timeout_seconds": 3.0,
    },
}

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "output_cluster_config.json")

editor = ConfigEditor(
    app_name="Cluster Config Manager",
    config_file=CONFIG_FILE,
    schema=SCHEMA,
    presets=PRESETS,
    default_preset="Development",
    admin_password="supersecretadmin",  # Admin password for unlocking read-only fields
)

if __name__ == "__main__":
    print("Presets and Admin Mode Demo")
    print("1. Notice 'system_cluster_id' and 'replica_count' are read-only for guests.")
    print("2. Click 'Admin Login' in top nav bar and enter password: 'supersecretadmin'.")
    print("3. Read-only fields are immediately unlocked for editing!")
    editor.run(host="127.0.0.1", port=5000)
