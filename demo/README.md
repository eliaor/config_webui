# pyConfigWebUI Demo

This directory contains an end-to-end interactive demo application with one unified schema, multiple complete preset configurations, and one active config file.

## File Structure

- `schema.json`: The single comprehensive JSON schema defining all application parameters (user credentials, applicant details, reservation settings, and protected admin/system variables).
- `config.json`: The single active configuration file edited and persisted by the web UI.
- `presets/`: Complete configuration presets for instant switching:
  - `default.json`: Standard default configuration.
  - `christmas.json`: Holiday event preset with customized times and notes.
  - `vip.json`: High-priority VIP applicant configuration.
- `demo_ui.py`: Launches the ConfigEditor web interface.
- `demo_main.py`: The mock backend processing reservations from `config.json`.

## Running the Demo

```bash
python demo/demo_ui.py
```

1. Open `http://localhost:5000/` in your browser.
2. Switch between presets (**Default**, **Christmas Special**, **VIP Applicant**) using the Presets dropdown.
3. Notice that `system_settings` fields are marked `readOnly: true` and locked for guest users.
4. Click **Admin Login** (Password: `admin`) in the top navigation bar to unlock and edit all fields.
5. Click **Save** to update `config.json`.
