# pyConfigWebUI Demo

This directory contains an end-to-end interactive reservation management system demo.

## Structure

- `demo_ui.py`: Launches the ConfigEditor web interface configured with presets, admin credentials, and a hooked main application function.
- `demo_main.py`: The Python application backend that reads the configured `config/main.json`, validates credentials, and processes applicant reservations.
- `schema/`: JSON schemas (`main.json`, `applicant_information.json`, `reservation_detail.json`, `user_credential.json`).
- `config/`: Active configuration files.
- `presets/`: Ready-to-use presets (`default.json`, `christmas.json`, `vip.json`).

## Running the Demo

```bash
python demo/demo_ui.py
```

1. Open `http://localhost:5000/` in your browser.
2. Select and apply different presets (**Default**, **Christmas Special**, **VIP Applicant**).
3. Try modifying the fields. Notice `system_settings.system_id` and `server_environment` are read-only for guests.
4. Click **Admin Login** (Password: `admin`) to unlock and edit read-only parameters.
5. Save your changes.
6. The updated settings are saved to `demo/config/main.json` and consumed by `demo_main.py`.
