"""
Example 3: Machine Learning Training Manager with Task Runner
"""

import os
import sys

try:
    from configwebui import ConfigEditor
except ImportError:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "src"))
    from configwebui import ConfigEditor

try:
    from .trainer import train_model
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from trainer import train_model

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCHEMA_FILE = os.path.join(BASE_DIR, "schema", "schema.json")
CONFIG_FILE = os.path.join(BASE_DIR, "config", "config.json")
PRESETS_DIR = os.path.join(BASE_DIR, "config", "presets")

PRESETS = {
    "Quick Experiment (3 Epochs)": os.path.join(PRESETS_DIR, "quick_experiment.json"),
    "Standard Training (ResNet-50)": os.path.join(PRESETS_DIR, "standard_training.json"),
    "High Accuracy GPU Cluster": os.path.join(PRESETS_DIR, "high_accuracy_gpu.json"),
}

editor = ConfigEditor(
    app_name="ML Training Manager",
    config_file=CONFIG_FILE,
    schema=SCHEMA_FILE,
    presets=PRESETS,
    default_preset="Standard Training (ResNet-50)",
    admin_password="gpuadminsecret",
    main_entry=train_model,
)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Loaded schema: {SCHEMA_FILE}")
    print(f"Target config: {CONFIG_FILE}")
    print(f"Presets: {list(PRESETS.keys())}")
    print(f"Starting ML Training Editor on http://127.0.0.1:{port} ...")
    editor.run(host="0.0.0.0", port=port)
