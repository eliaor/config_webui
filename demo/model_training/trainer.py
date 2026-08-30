"""
Trainer Worker: Reads config/config.json and simulates model training.
"""

import json
import os
import time

try:
    from configwebui import ResultStatus
except ImportError:
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
    from configwebui import ResultStatus

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config", "config.json")


def train_model():
    print("=" * 60)
    print(">>> INITIALIZING MODEL TRAINING RUNNER")
    print("=" * 60)

    if not os.path.exists(CONFIG_FILE):
        print(f"[ERROR] Config file not found: {CONFIG_FILE}")
        return ResultStatus(False, "Config file missing.")

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    model = cfg.get("model", {})
    hyp = cfg.get("hyperparameters", {})
    hw = cfg.get("hardware_protected", {})

    print(f"[*] Architecture   : {model.get('architecture')}")
    print(f"[*] Pretrained     : {model.get('pretrained_weights')}")
    print(f"[*] Hardware       : {hw.get('gpu_device_id')} ({hw.get('max_vram_gb')} GB VRAM)")
    print(f"[*] Optimizer      : {hyp.get('optimizer')} (LR: {hyp.get('learning_rate')})")
    print(f"[*] Batch Size     : {hyp.get('batch_size')}")
    print(f"[*] Total Epochs   : {hyp.get('epochs')}")
    print("-" * 60)

    epochs = hyp.get("epochs", 5)
    for epoch in range(1, epochs + 1):
        time.sleep(0.5)
        loss = round(1.0 / (epoch + 1) + 0.02, 4)
        acc = round(100 * (1 - 1.0 / (epoch + 2)), 2)
        print(f"Epoch [{epoch}/{epochs}] -> Loss: {loss:.4f} | Accuracy: {acc:.2f}% | Val Loss: {loss * 1.05:.4f}")

    print("-" * 60)
    print("[+] Training completed successfully! Model checkpoint saved.")
    print("=" * 60)
    return ResultStatus(True, "Training finished successfully.")
