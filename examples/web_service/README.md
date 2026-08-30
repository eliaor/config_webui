# Web Service Configuration Project

Demonstrates an enterprise web service config manager with Presets and Admin security.

## Structure

```
01_web_service/
├── app.py                     # Project runner
├── schema/
│   └── schema.json            # Unified schema (server, db, cache, logging, security)
├── config/
│   ├── config.json            # Active configuration file
│   └── presets/               # Complete configuration presets
│       ├── development.json
│       ├── staging.json
│       ├── production.json
│       └── testing_ci.json
└── README.md
```

## Running

```bash
python examples/01_web_service/app.py
```
