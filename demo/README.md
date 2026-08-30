# pyConfigWebUI Demo: Reservation Booking System

This directory is an interactive demo project demonstrating a complete end-to-end application.

## Project Structure

```
demo/
├── demo_ui.py             # Web UI launcher
├── demo_main.py           # Backend application worker
├── schema/
│   └── schema.json        # One unified JSON schema for the entire application
├── config/
│   ├── config.json        # Active configuration file
│   └── presets/           # Preset configurations
│       ├── default.json
│       ├── christmas.json
│       └── vip.json
└── README.md
```

## Running the Demo

```bash
python demo/demo_ui.py
```

1. Open `http://localhost:5000/` in your browser.
2. Switch presets using the Presets dropdown.
3. Test guest vs admin mode (`system_settings` is locked for guests, unlocked with admin password `admin`).
4. Click Save to persist changes to `config/config.json`.
