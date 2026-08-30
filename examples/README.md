# pyConfigWebUI Examples & Demos

This directory demonstrates the recommended architectural pattern for **pyConfigWebUI**:
- **One Unified Schema** (`schema.json`): A single, comprehensive JSON Schema covering all components (Server, Database, Caching, Logging, Features, and Admin-Protected parameters).
- **Multiple Full Presets** (`presets/*.json`): Complete, standalone configuration profiles for different deployment tiers (Development, Staging, Production HA, and Testing CI).
- **One Active Configuration File** (`config.json`): The single active configuration file edited in the UI and read by the application.

---

## 📁 File Structure

```
examples/
├── schema.json               # The single unified application schema
├── config.json               # The single active configuration file
├── presets/                  # Multiple complete preset configurations
│   ├── development.json      # Local development preset (SQLite, debug logging)
│   ├── staging.json          # Staging cluster preset (PostgreSQL, Redis)
│   ├── production.json       # Production HA preset (high pool size, TLS, rate limits)
│   └── testing_ci.json       # Ephemeral CI testing preset (in-memory)
├── run_basic_editor.py       # Basic editor with preset switching & admin login
├── run_with_custom_validation.py # Editor with custom business rule validation
├── run_with_task_runner.py   # Editor with background service execution & live logs
└── README.md
```

---

## 🚀 Running the Examples

### 1. Basic Editor with Presets & Admin Security
Loads `schema.json`, registers all presets, and saves to `config.json`:
```bash
python examples/run_basic_editor.py
```
- Open `http://localhost:5000/` in your browser.
- Switch between **Development**, **Staging**, **Production (High Availability)**, and **Testing (CI)**.
- Notice `system_protected` fields are locked for guests. Click **Admin Login** (Password: `superadminsecret`) to unlock and edit them.

### 2. Editor with Custom Multi-Field Business Validation
Adds custom cross-field validation rules (e.g. requiring TLS in Production, validating Redis URL format):
```bash
python examples/run_with_custom_validation.py
```

### 3. Editor with Live Background Task Execution & Logs
Hooks a Python startup worker to read `config.json` and stream live console logs to the web interface:
```bash
python examples/run_with_task_runner.py
```
