"""
Example 5: Rich Schema Types and Form Controls

This script demonstrates the variety of JSON Schema field types and UI controls
supported by pyConfigWebUI:
- Text inputs & textareas
- Integers, floats, ranges, steps
- Booleans (switches / checkboxes)
- Enums / Select dropdowns
- Array tables with add/remove items
- Nested objects and fieldsets
- Password masking in form and JSON code view
"""

import os
try:
    from configwebui import ConfigEditor
except ImportError:
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
    from configwebui import ConfigEditor

SCHEMA = {
    "title": "Full-Featured Application Configuration",
    "type": "object",
    "properties": {
        "app_info": {
            "title": "Application Information",
            "type": "object",
            "properties": {
                "service_name": {
                    "title": "Service Name",
                    "type": "string",
                    "default": "PaymentGatewayService",
                },
                "environment": {
                    "title": "Environment",
                    "type": "string",
                    "enum": ["development", "testing", "staging", "production"],
                    "default": "development",
                },
                "description": {
                    "title": "Service Description",
                    "type": "string",
                    "format": "textarea",
                    "default": "Core payment gateway handling credit card and ACH transactions.",
                },
            },
            "required": ["service_name", "environment"],
        },
        "security": {
            "title": "Security & Credentials",
            "type": "object",
            "properties": {
                "api_key": {
                    "title": "API Key",
                    "type": "string",
                    "format": "password",
                    "default": "sk_live_9384029482048204",
                    "description": "Masked in both the UI and JSON preview",
                },
                "jwt_secret": {
                    "title": "JWT Secret Key",
                    "type": "string",
                    "format": "password",
                    "default": "super-secret-jwt-token-key-2026",
                },
                "token_ttl_minutes": {
                    "title": "Token Expiration (minutes)",
                    "type": "integer",
                    "default": 60,
                    "minimum": 5,
                    "maximum": 1440,
                },
            },
        },
        "endpoints": {
            "title": "Upstream Endpoints (Array of Objects)",
            "type": "array",
            "items": {
                "type": "object",
                "title": "Endpoint",
                "properties": {
                    "name": {"title": "Name", "type": "string", "default": "Primary DB"},
                    "url": {"title": "URL", "type": "string", "default": "https://db.internal:5432"},
                    "timeout_ms": {"title": "Timeout (ms)", "type": "integer", "default": 3000},
                    "enabled": {"title": "Enabled", "type": "boolean", "default": True},
                },
                "required": ["name", "url"],
            },
            "default": [
                {"name": "Primary DB", "url": "https://db.internal:5432", "timeout_ms": 3000, "enabled": True},
                {"name": "Cache Redis", "url": "https://redis.internal:6379", "timeout_ms": 1000, "enabled": True},
            ],
        },
        "tags": {
            "title": "Metadata Tags (Array of Strings)",
            "type": "array",
            "items": {"type": "string"},
            "default": ["v2-release", "critical-infra", "pci-dss"],
        },
    },
}

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "output_rich_config.json")

editor = ConfigEditor(
    app_name="Rich Schema Form Showcase",
    config_file=CONFIG_FILE,
    schema=SCHEMA,
)

if __name__ == "__main__":
    print("Rich Schema Form Demo running on http://127.0.0.1:5000")
    editor.run(host="127.0.0.1", port=5000)
