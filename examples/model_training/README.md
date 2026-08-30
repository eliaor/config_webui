# ML Model Training Project

Demonstrates an ML model training configuration manager with background task runner and streamed console logs.

## Structure

```
03_model_training/
├── app.py                     # Web UI launcher with main_entry hook
├── trainer.py                 # Background training worker
├── schema/
│   └── schema.json            # Unified hyperparameters & hardware schema
├── config/
│   ├── config.json            # Active configuration file
│   └── presets/               # Complete configuration presets
│       ├── quick_experiment.json
│       ├── standard_training.json
│       └── high_accuracy_gpu.json
└── README.md
```

## Running

```bash
python examples/03_model_training/app.py
```
