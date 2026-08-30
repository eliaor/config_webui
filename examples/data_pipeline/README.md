# Data Pipeline Configuration Project

Demonstrates an ETL data pipeline configuration editor with custom cross-field validation rules.

## Structure

```
02_data_pipeline/
├── app.py                     # Project runner with validation callback
├── schema/
│   └── schema.json            # Unified pipeline schema
├── config/
│   ├── config.json            # Active configuration file
│   └── presets/               # Complete configuration presets
│       ├── batch_etl.json
│       ├── realtime_streaming.json
│       └── memory_optimized.json
└── README.md
```

## Running

```bash
python examples/02_data_pipeline/app.py
```
