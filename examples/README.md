# pyConfigWebUI Example Projects

This directory contains standalone, self-contained project folders. Each demo project has its own dedicated folder containing:
- `app.py`: The executable UI runner.
- `schema/schema.json`: One unified JSON schema for the project.
- `config/config.json`: The single active configuration file.
- `config/presets/*.json`: Multiple complete preset configurations for instant switching.
- `README.md`: Project-specific instructions.

---

## 📁 Projects Overview

### 1. [`web_service/`](web_service/)
- **Use Case**: Enterprise Web Service & Infrastructure Manager.
- **Key Features**: Multi-preset switching (Development, Staging, Production HA, CI Testing), locked infrastructure parameters (`readOnly: true`), Admin Login password unlock.
- **Run**:
  ```bash
  python examples/web_service/app.py
  ```

### 2. [`data_pipeline/`](data_pipeline/)
- **Use Case**: Ingestion & ETL Data Pipeline Config.
- **Key Features**: Custom cross-field validation rules (`extra_validation_func`) enforcing buffer sizing and KMS encryption requirements.
- **Run**:
  ```bash
  python examples/data_pipeline/app.py
  ```

### 3. [`model_training/`](model_training/)
- **Use Case**: ML Model Training & Hyperparameter Tuning.
- **Key Features**: Background task execution (`main_entry`), live terminal stdout/stderr streaming in the browser, GPU cluster quota protections.
- **Run**:
  ```bash
  python examples/model_training/app.py
  ```

---

## 🎯 Full Interactive Demo
For the full end-to-end appointment booking reservation system, see the [`demo/`](../demo/) directory:
```bash
python demo/demo_ui.py
```
