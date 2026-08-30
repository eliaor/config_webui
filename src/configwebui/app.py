"""
Flask web application for managing and interacting with a global configuration.

This application provides routes and APIs for:
- Viewing and editing a single global configuration file via a web interface.
- Switching between different predefined configuration presets.
- Admin authentication allowing users to edit/override readonly configuration properties.
- Launching, stopping, and interacting with the main program runner.
- Viewing real-time terminal output logs and handling server lifecycle events.
"""

from flask import (
    Blueprint,
    current_app,
    flash,
    make_response,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)
from markupsafe import escape

from . import ConfigEditor

ICON_CLASS = {
    "info": "fas fa-info-circle",
    "success": "fas fa-check-circle",
    "warning": "fas fa-exclamation-triangle",
    "danger": "fas fa-times-circle",
}
ICON = {
    category: f'<i class="{ICON_CLASS[category]}"></i>'
    for category in ICON_CLASS.keys()
}

main = Blueprint("main", __name__)


@main.route("/")
def index():
    """
    Renders the main configuration editor web page.
    """
    current_config_editor: ConfigEditor = current_app.config["ConfigEditor"]
    is_admin = session.get("is_admin", False)

    return render_template(
        "index.html",
        title=current_app.config["app_name"],
        presets=current_config_editor.get_preset_names(),
        is_admin=is_admin,
        config_file=current_config_editor.config_file or "Global Config",
    )


@main.route("/config")
@main.route("/config/<path:path>")
def config_redirect(path=None):
    """
    Redirects legacy /config paths to the root index.
    """
    return redirect(url_for("main.index"))


@main.route("/api/config", methods=["GET", "POST", "PATCH"])
def config_api():
    """
    API endpoint for getting and updating the global configuration.
    - GET: Returns the configuration, schema (unlocked if admin), admin status, and presets list.
    - POST / PATCH: Validates and saves updated configuration.
    """
    current_config_editor: ConfigEditor = current_app.config["ConfigEditor"]
    is_admin = session.get("is_admin", False)

    if request.method == "GET":
        return make_response(
            {
                "success": True,
                "messages": [""],
                "config": current_config_editor.get_config(),
                "schema": current_config_editor.get_schema(is_admin=is_admin),
                "is_admin": is_admin,
                "presets": current_config_editor.get_preset_names(),
            },
            200,
        )

    # POST or PATCH
    data = request.get_json() or {}
    if "config" not in data:
        return make_response(
            {
                "success": False,
                "messages": ["No config data provided."],
            },
            400,
        )

    res = current_config_editor.set_config(
        config=data["config"],
        save_file=True,
        is_admin=is_admin,
    )

    if res.get_status():
        return make_response(
            {
                "success": True,
                "messages": ["Configuration saved successfully."],
                "config": current_config_editor.get_config(),
            },
            200,
        )
    else:
        return make_response(
            {
                "success": False,
                "messages": list(map(escape, res.get_messages())),
            },
            400,
        )


@main.route("/api/reset", methods=["GET", "POST"])
def reset_api():
    """
    Reloads the configuration from file or defaults.
    """
    current_config_editor: ConfigEditor = current_app.config["ConfigEditor"]
    config = current_config_editor.load()
    return make_response(
        {
            "success": True,
            "messages": ["Configuration reset to saved state."],
            "config": config,
        },
        200,
    )


@main.route("/api/presets", methods=["GET"])
def presets_list_api():
    """
    Returns a list of all available preset configuration names.
    """
    current_config_editor: ConfigEditor = current_app.config["ConfigEditor"]
    return make_response(
        {
            "success": True,
            "presets": current_config_editor.get_preset_names(),
        },
        200,
    )


@main.route("/api/presets/<preset_name>", methods=["GET"])
def preset_get_api(preset_name: str):
    """
    Retrieves the configuration for a specific preset name.
    """
    current_config_editor: ConfigEditor = current_app.config["ConfigEditor"]
    preset_config = current_config_editor.get_preset(preset_name)
    if preset_config is None:
        return make_response(
            {
                "success": False,
                "messages": [f"Preset <strong>{escape(preset_name)}</strong> not found."],
            },
            404,
        )
    return make_response(
        {
            "success": True,
            "preset_name": preset_name,
            "config": preset_config,
        },
        200,
    )


@main.route("/api/presets/<preset_name>/apply", methods=["POST"])
@main.route("/api/preset/<preset_name>", methods=["POST"])
def preset_apply_api(preset_name: str):
    """
    Applies the specified preset to the active configuration and saves it.
    """
    current_config_editor: ConfigEditor = current_app.config["ConfigEditor"]
    data = request.get_json(silent=True) or {}
    save_file = data.get("save", True)

    res = current_config_editor.apply_preset(name=preset_name, save_file=save_file)
    if res.get_status():
        return make_response(
            {
                "success": True,
                "messages": [
                    f"Preset <strong>{escape(preset_name)}</strong> applied successfully."
                ],
                "config": current_config_editor.get_config(),
            },
            200,
        )
    else:
        return make_response(
            {
                "success": False,
                "messages": list(map(escape, res.get_messages())),
            },
            400,
        )


@main.route("/api/login", methods=["POST"])
def login_api():
    """
    Handles admin authentication with password.
    """
    current_config_editor: ConfigEditor = current_app.config["ConfigEditor"]
    data = request.get_json(silent=True) or {}
    password = data.get("password", "")

    if current_config_editor.verify_admin_password(password):
        session["is_admin"] = True
        return make_response(
            {
                "success": True,
                "is_admin": True,
                "messages": ["Logged in as Admin. Readonly fields can now be edited."],
            },
            200,
        )
    else:
        return make_response(
            {
                "success": False,
                "is_admin": False,
                "messages": ["Invalid admin password."],
            },
            401,
        )


@main.route("/api/logout", methods=["GET", "POST"])
def logout_api():
    """
    Logs out from admin mode.
    """
    session.pop("is_admin", None)
    return make_response(
        {
            "success": True,
            "is_admin": False,
            "messages": ["Logged out from admin mode."],
        },
        200,
    )


@main.route("/api/auth_status", methods=["GET"])
def auth_status_api():
    """
    Returns current authentication status.
    """
    return make_response(
        {
            "success": True,
            "is_admin": session.get("is_admin", False),
        },
        200,
    )


@main.route("/api/launch")
def launch():
    """
    Launches the main program in a separate thread.
    """
    current_config_editor: ConfigEditor = current_app.config["ConfigEditor"]
    res = current_config_editor.launch_main_entry()
    if res.get_status():
        return make_response(
            {
                "success": True,
                "messages": [
                    f"The main program has been successfully requested to run. "
                    f'<a href="#terminal-output-display" class="alert-link">'
                    f"Check it out below"
                    f"</a>.",
                ],
            },
            200,
        )
    else:
        return make_response(
            {
                "success": False,
                "messages": ["Main program is already running"],
            },
            503,
        )


@main.route("/api/shutdown")
def shutdown():
    """
    Shuts down the web server.
    """
    current_config_editor: ConfigEditor = current_app.config["ConfigEditor"]
    current_config_editor.stop_server()
    return make_response("", 204)


@main.route("/api/clear_terminal_output", methods=["POST"])
def clear_terminal_output():
    """
    Clears the stored terminal output.
    """
    current_config_editor: ConfigEditor = current_app.config["ConfigEditor"]
    current_config_editor.main_entry_runner.clear()
    return make_response("", 204)


@main.route("/api/get_terminal_output")
def get_terminal_output():
    """
    Retrieves captured output from the main program runner.
    """
    recent_only = bool(int(request.args.get("recent_only", "0")))
    current_config_editor: ConfigEditor = current_app.config["ConfigEditor"]
    res = current_config_editor.main_entry_runner.get_res()
    return make_response(
        {
            "success": True,
            "messages": list(map(escape, res.get_messages())),
            "state": res.get_status(),
            "has_warning": current_config_editor.main_entry_runner.has_warning(),
            "running": current_config_editor.main_entry_runner.is_running(),
            "combined_output": current_config_editor.main_entry_runner.get_combined_output(
                recent_only=recent_only
            ),
        },
        200,
    )


@main.route("/<path:path>")
def catch_all(path):
    """
    Catch-all route for static assets, trailing slashes, and 404s.
    """
    if path == "favicon.ico":
        return send_from_directory("static/icon", "favicon.ico")
    if path.endswith("/"):
        return redirect(f"/{path[:-1]}")
    flash(
        f'<span>{ICON["danger"]}</span> <span>Page not found</span>',
        "danger",
    )
    return redirect(url_for("main.index"))
