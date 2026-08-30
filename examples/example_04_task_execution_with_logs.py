"""
Example 4: Task Execution with Real-Time Output

This script demonstrates:
1. Attaching a Python task function (`main_entry`).
2. Triggering the task directly from the UI.
3. Viewing streamed stdout / stderr logs in real-time.
"""

import os
import time
try:
    from configwebui import ConfigEditor, ResultStatus
except ImportError:
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
    from configwebui import ConfigEditor, ResultStatus

SCHEMA = {
    "title": "Model Training Parameters",
    "type": "object",
    "properties": {
        "epochs": {"title": "Epochs", "type": "integer", "default": 5, "minimum": 1},
        "learning_rate": {"title": "Learning Rate", "type": "number", "default": 0.001},
        "model_architecture": {
            "title": "Model Architecture",
            "type": "string",
            "enum": ["ResNet50", "EfficientNet", "Transformer-Base"],
            "default": "ResNet50",
        },
    },
}

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "output_model_config.json")


def train_model_task():
    """
    Simulated long-running task.
    Output printed to stdout/stderr is automatically captured and streamed to the UI.
    """
    import json

    print("=" * 50)
    print("Starting Model Training Pipeline...")
    print("=" * 50)

    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            cfg = json.load(f)
    else:
        cfg = {"epochs": 5, "learning_rate": 0.001, "model_architecture": "ResNet50"}

    epochs = cfg.get("epochs", 5)
    lr = cfg.get("learning_rate", 0.001)
    arch = cfg.get("model_architecture", "ResNet50")

    print(f"Loaded Architecture: {arch}")
    print(f"Learning Rate: {lr}")
    print(f"Total Epochs: {epochs}")
    print("-" * 50)

    for i in range(1, epochs + 1):
        time.sleep(0.8)
        loss = round(1.0 / (i + 1) + 0.05, 4)
        acc = round(100 * (1 - 1.0 / (i + 2)), 2)
        print(f"Epoch [{i}/{epochs}] - Loss: {loss} - Accuracy: {acc}%")

    print("\nTraining completed successfully!")
    print("=" * 50)
    return ResultStatus(True, "Training finished successfully.")


editor = ConfigEditor(
    app_name="ML Trainer UI",
    config_file=CONFIG_FILE,
    schema=SCHEMA,
    main_entry=train_model_task,
)

if __name__ == "__main__":
    print("Task Execution with Output Demo")
    print("- Modify hyperparameters and click Save.")
    print("- Click 'Launch main program' in the UI or call the run endpoint to watch live logs.")
    editor.run(host="127.0.0.1", port=5000)
