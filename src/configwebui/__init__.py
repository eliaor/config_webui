"""
configwebui - A simple web-based configuration editor for Python applications.

This package provides tools for editing a global configuration file
(like json or yaml) in a user-friendly web interface with preset selection,
schema validation, admin mode for overriding readonly variables, and interactive
program execution.

The primary components of this module include:
- `ConfigEditor`: The main class that manages the global configuration editor,
  preset management, admin authentication, launching the web server, and executing
  the main program.
- `ResultStatus`: A class representing the status of an operation (success/failure)
  with associated messages.

Usage Example:
    ```python
    from configwebui import ConfigEditor

    # Initialize the ConfigEditor with a config file and schema
    editor = ConfigEditor(
        app_name="My App Config",
        config_file="config/main.json",
        schema={...},
        presets={
            "Default": "presets/default.json",
            "Performance": {"threads": 8, "fast_mode": True},
        },
        admin_password="secretadminpassword",
    )

    # Run the configuration editor
    editor.run()
    ```
"""

import json
import logging
import os
import sys
import threading
import time
import traceback
import webbrowser
from collections.abc import Callable
from copy import deepcopy
from importlib.metadata import PackageNotFoundError, version
from socket import setdefaulttimeout
from typing import Any

from flask import Flask
from jsonschema import ValidationError, validate
from werkzeug.serving import make_server

from .utils import (
    BASE_ERROR_STREAM,
    BASE_OUTPUT_STREAM,
    ProgramRunner,
    ResultStatus,
    ThreadOutputStream,
)

try:
    __version__ = version("configwebui-lucien")
except PackageNotFoundError:
    pass

__all__ = ["ConfigEditor", "ResultStatus", "UserConfig"]

SERVER_TIMEOUT = 3
DAEMON_CHECK_INTERVAL = 1
logging.getLogger("werkzeug").disabled = True


class ConfigEditor:
    """
    A class for managing a single global web-based configuration editor.

    Features:
        - Single global configuration file management.
        - JSON schema validation with property ordering.
        - Preset configuration selection and application.
        - Admin authentication to enable editing and overriding readonly fields.
        - Main entry execution with captured real-time terminal output.
        - Local web server lifecycle management.

    Attributes:
        app_name (str): The display name of the application.
        config_file (str | None): Path to the global configuration file.
        schema (dict): The active JSON schema.
        config (dict): The current configuration dictionary in memory.
        presets (dict[str, dict]): Available preset configurations.
        admin_password (str): Password required for admin mode.
        extra_validation_func (Callable | None): Optional custom validation function.
        save_func (Callable | None): Optional custom save function.
        load_func (Callable | None): Optional custom load function.
        main_entry_runner (ProgramRunner): Runner for executing the main program.
        running (bool): Whether the web server is running.
        saving (bool): Whether a save operation is in progress.
        app (Flask): The Flask application instance.
    """

    DEFAULT_VALUE = {
        "string": "",
        "number": 0,
        "integer": 0,
        "boolean": False,
        "null": None,
    }

    def __init__(
        self,
        app_name: str = "Config Editor",
        config_file: str | None = None,
        schema: dict | str | None = None,
        config: dict | None = None,
        presets: dict[str, dict | str] | None = None,
        default_preset: str | None = None,
        admin_password: str = "admin",
        extra_validation_func: Callable | None = None,
        save_func: Callable | None = None,
        load_func: Callable | None = None,
        main_entry: Callable | None = None,
    ) -> None:
        """
        Initializes a ConfigEditor instance.

        Args:
            app_name (str): Application display name. Defaults to "Config Editor".
            config_file (str | None): Path to the global config file.
            schema (dict | str | None): JSON schema dict or path to schema JSON file.
            config (dict | None): Initial configuration dictionary.
            presets (dict[str, dict | str] | None): Dictionary mapping preset names to
                config dicts or file paths.
            default_preset (str | None): Optional preset name to apply by default.
            admin_password (str): Password for admin mode. Defaults to "admin".
            extra_validation_func (Callable | None): Optional custom validation callable.
            save_func (Callable | None): Optional custom save callable.
            load_func (Callable | None): Optional custom load callable.
            main_entry (Callable | None): Optional main entry function to run.

        Raises:
            TypeError: If arguments are of invalid types.
            ValueError: If `app_name` or `admin_password` is empty.
        """
        from . import app
        from .config import AppConfig

        if not isinstance(app_name, str):
            raise TypeError(f"app_name must be a string, not {type(app_name)}.")
        app_name = app_name.strip()
        if app_name == "":
            raise ValueError("app_name cannot be empty.")
        self.app_name = app_name

        if config_file is not None:
            if not isinstance(config_file, str):
                raise TypeError(
                    f"config_file must be a string or None, not {type(config_file)}."
                )
            config_file = config_file.strip()
        self.config_file = config_file

        if not isinstance(admin_password, str):
            raise TypeError(
                f"admin_password must be a string, not {type(admin_password)}."
            )
        self.admin_password = admin_password

        if extra_validation_func is not None and not callable(extra_validation_func):
            raise TypeError("extra_validation_func must be a callable function.")
        self.extra_validation_func = extra_validation_func

        if save_func is not None and not callable(save_func):
            raise TypeError("save_func must be a callable function.")
        self.save_func = save_func

        if load_func is not None and not callable(load_func):
            raise TypeError("load_func must be a callable function.")
        self.load_func = load_func

        if main_entry is None:
            self.main_entry_runner = ProgramRunner(
                function=ConfigEditor.default_main_entry,
                hide_terminal_output=False,
                hide_terminal_error=False,
            )
        else:
            if not callable(main_entry):
                raise TypeError("main_entry must be a callable function.")
            self.main_entry_runner = ProgramRunner(
                function=main_entry,
                hide_terminal_output=False,
                hide_terminal_error=False,
            )

        self.running = False
        self.saving = False
        self.presets: dict[str, dict] = {}

        # Set schema
        self.set_schema(schema)

        # Register presets
        if presets is not None:
            if not isinstance(presets, dict):
                raise TypeError(
                    f"presets must be a dictionary, not {type(presets)}."
                )
            for preset_name, preset_val in presets.items():
                self.add_preset(preset_name, preset_val)

        # Initialize config
        self.config = {}
        if config is not None:
            if not isinstance(config, dict):
                raise TypeError(f"config must be a dictionary, not {type(config)}.")
            self.config = deepcopy(config)
        elif self.load_func is not None:
            loaded_config = self.load_func()
            if isinstance(loaded_config, dict):
                self.config = deepcopy(loaded_config)
        elif self.config_file and os.path.exists(self.config_file):
            self.load()
        elif default_preset and default_preset in self.presets:
            self.config = deepcopy(self.presets[default_preset])
        elif "Default" in self.presets:
            self.config = deepcopy(self.presets["Default"])
        else:
            self.config = ConfigEditor.generate_default_json(self.schema)

        # Ensure a Default preset exists if none was specified
        if "Default" not in self.presets:
            self.presets["Default"] = deepcopy(self.config)

        flask_app = Flask(
            import_name=app_name,
            template_folder="templates",
            static_folder="static",
            root_path=os.path.dirname(os.path.abspath(__file__)),
        )
        flask_app.config.from_object(AppConfig)
        flask_app.config["app_name"] = app_name
        flask_app.config["ConfigEditor"] = self
        flask_app.register_blueprint(app.main)

        self.app = flask_app

    @staticmethod
    def default_main_entry() -> ResultStatus:
        """
        Default entry point function when none is provided.

        Returns:
            ResultStatus: Status indicating main entry is undefined.
        """
        return ResultStatus(False, "Main entry is undefined.")

    @staticmethod
    def add_order(schema: dict, property_order: int = 0) -> dict:
        """
        Adds a `propertyOrder` field to a JSON schema for UI ordering.

        Args:
            schema (dict): The JSON schema to modify.
            property_order (int): The order value to assign.

        Returns:
            dict: The schema with `propertyOrder` fields added.
        """
        if not isinstance(schema, dict):
            return schema
        ordered_schema = deepcopy(schema)
        ordered_schema["propertyOrder"] = property_order
        current_type = schema.get("type", None)
        if current_type == "object" or "properties" in schema:
            properties = ordered_schema.get("properties", {})
            for order, prop in enumerate(properties):
                if "." in prop:
                    raise ValueError("Property name cannot contain '.'")
                ordered_schema["properties"][prop] = ConfigEditor.add_order(
                    schema=properties[prop], property_order=order
                )
        elif current_type == "array" or "items" in schema:
            ordered_schema["items"] = ConfigEditor.add_order(
                schema=ordered_schema.get("items", {}), property_order=0
            )
        elif current_type is None:
            for array_indicator in ["oneOf", "anyOf", "allOf"]:
                if array_indicator in ordered_schema:
                    for index, item in enumerate(ordered_schema[array_indicator]):
                        ordered_schema[array_indicator][index] = (
                            ConfigEditor.add_order(schema=item, property_order=0)
                        )
        return ordered_schema

    @staticmethod
    def generate_default_json(schema: dict) -> Any:
        """
        Generates a default JSON configuration inferred from a schema.

        Args:
            schema (dict): The JSON schema to use.

        Returns:
            Any: Default configuration data inferred from the schema.
        """
        if not isinstance(schema, dict):
            return {}
        if "default" in schema:
            return deepcopy(schema["default"])
        if "enum" in schema and len(schema["enum"]) > 0:
            return schema["enum"][0]
        current_type = schema.get("type", None)
        if current_type is None:
            return {}
        if current_type == "object" or "properties" in schema:
            obj = {}
            properties: dict = schema.get("properties", {})
            required: list = schema.get("required", [])
            for key, value in properties.items():
                if key in required or "default" in value:
                    obj[key] = ConfigEditor.generate_default_json(value)
                elif isinstance(value, dict) and (
                    value.get("type") == "object" or "properties" in value
                ):
                    nested = ConfigEditor.generate_default_json(value)
                    if nested:
                        obj[key] = nested
            return obj
        elif current_type == "array":
            min_items = schema.get("minItems", 0)
            items_schema = schema.get("items", {})
            return [
                ConfigEditor.generate_default_json(items_schema)
                for _ in range(min_items)
            ]
        else:
            if isinstance(current_type, list):
                return ConfigEditor.DEFAULT_VALUE.get(current_type[0], None)
            else:
                return ConfigEditor.DEFAULT_VALUE.get(current_type, None)

    @staticmethod
    def strip_readonly(schema: Any) -> Any:
        """
        Recursively creates a copy of the schema with all `readOnly` and `readonly`
        flags set to False, allowing all fields to be editable in admin mode.

        Args:
            schema (Any): The schema object or dictionary.

        Returns:
            Any: A modified schema with readonly disabled.
        """
        if isinstance(schema, dict):
            new_dict = {}
            for k, v in schema.items():
                if k in ("readOnly", "readonly"):
                    new_dict[k] = False
                elif k == "options" and isinstance(v, dict):
                    new_options = {}
                    for ok, ov in v.items():
                        if ok == "input_attributes" and isinstance(ov, dict):
                            new_attr = {
                                ak: av
                                for ak, av in ov.items()
                                if ak.lower() != "readonly"
                            }
                            new_options[ok] = new_attr
                        else:
                            new_options[ok] = ConfigEditor.strip_readonly(ov)
                    new_dict[k] = new_options
                else:
                    new_dict[k] = ConfigEditor.strip_readonly(v)
            return new_dict
        elif isinstance(schema, list):
            return [ConfigEditor.strip_readonly(item) for item in schema]
        else:
            return schema

    @staticmethod
    def extract_readonly_paths(
        schema: dict, current_path: tuple = ()
    ) -> set[tuple]:
        """
        Finds all property paths in the schema that are marked as readonly.

        Args:
            schema (dict): The JSON schema to inspect.
            current_path (tuple): The current property path tuple.

        Returns:
            set[tuple]: Set of property paths (tuples of strings) that are readonly.
        """
        paths = set()
        if not isinstance(schema, dict):
            return paths

        if schema.get("readOnly") is True or schema.get("readonly") is True:
            if current_path:
                paths.add(current_path)

        schema_type = schema.get("type", None)
        if schema_type == "object" or "properties" in schema:
            properties = schema.get("properties", {})
            for prop_name, prop_schema in properties.items():
                paths.update(
                    ConfigEditor.extract_readonly_paths(
                        prop_schema, current_path + (prop_name,)
                    )
                )
        elif schema_type == "array" or "items" in schema:
            items = schema.get("items", {})
            if isinstance(items, dict):
                paths.update(
                    ConfigEditor.extract_readonly_paths(
                        items, current_path + ("*",)
                    )
                )
            elif isinstance(items, list):
                for idx, item in enumerate(items):
                    paths.update(
                        ConfigEditor.extract_readonly_paths(
                            item, current_path + (str(idx),)
                        )
                    )
        for combiner in ("oneOf", "anyOf", "allOf"):
            if combiner in schema and isinstance(schema[combiner], list):
                for sub_schema in schema[combiner]:
                    paths.update(
                        ConfigEditor.extract_readonly_paths(
                            sub_schema, current_path
                        )
                    )
        return paths

    @staticmethod
    def get_path_value(data: Any, path: tuple) -> Any:
        """
        Retrieves a nested value from a dictionary or list given a path tuple.

        Args:
            data (Any): The root data dictionary/list.
            path (tuple): Tuple of string or int keys.

        Returns:
            Any: Value at the path or None.
        """
        current = data
        for part in path:
            if current is None:
                return None
            if isinstance(current, dict):
                current = current.get(part, None)
            elif isinstance(current, list):
                if part == "*":
                    return current
                try:
                    current = current[int(part)]
                except (IndexError, ValueError):
                    return None
            else:
                return None
        return current

    def check_readonly_modified(
        self, old_config: dict, new_config: dict
    ) -> ResultStatus:
        """
        Checks if any read-only fields were modified between old and new configs.

        Args:
            old_config (dict): Previous configuration data.
            new_config (dict): Proposed new configuration data.

        Returns:
            ResultStatus: Success if no readonly fields were modified, False otherwise.
        """
        readonly_paths = ConfigEditor.extract_readonly_paths(self.schema)
        for path in readonly_paths:
            old_val = ConfigEditor.get_path_value(old_config, path)
            new_val = ConfigEditor.get_path_value(new_config, path)
            if old_val != new_val:
                path_str = ".".join(map(str, path))
                return ResultStatus(
                    False,
                    f"Field '{path_str}' is read-only. Please log in as admin to modify it.",
                )
        return ResultStatus(True)

    def set_schema(self, schema: dict | str | None) -> None:
        """
        Sets or updates the JSON schema.

        Args:
            schema (dict | str | None): Schema dict or file path.

        Raises:
            TypeError: If `schema` is not a dict, str, or None.
        """
        if schema is None:
            schema = {}
        elif isinstance(schema, str):
            if os.path.exists(schema):
                with open(schema, "r", encoding="utf-8") as f:
                    schema = json.load(f)
            else:
                raise FileNotFoundError(f"Schema file not found: {schema}")
        elif not isinstance(schema, dict):
            raise TypeError(
                f"schema must be a dictionary or file path string, not {type(schema)}."
            )
        self.schema = ConfigEditor.add_order(schema)

    def get_schema(self, is_admin: bool = False) -> dict:
        """
        Retrieves the JSON schema. If `is_admin=True`, all readonly properties
        are unlocked.

        Args:
            is_admin (bool): Whether the requesting user has admin privileges.

        Returns:
            dict: The JSON schema.
        """
        if is_admin:
            return ConfigEditor.strip_readonly(self.schema)
        return deepcopy(self.schema)

    def get_config(self) -> dict:
        """
        Retrieves the current global configuration dictionary.

        Returns:
            dict: The configuration data.
        """
        return deepcopy(self.config)

    def set_config(
        self,
        config: dict,
        skip_schema_validations: bool = False,
        skip_extra_validations: bool = False,
        save_file: bool = False,
        is_admin: bool = False,
    ) -> ResultStatus:
        """
        Validates and updates the global configuration.

        Args:
            config (dict): New configuration data.
            skip_schema_validations (bool): Whether to skip schema validation.
            skip_extra_validations (bool): Whether to skip extra validation.
            save_file (bool): Whether to persist to file/save_func.
            is_admin (bool): Whether caller is admin.

        Returns:
            ResultStatus: Result of the operation.
        """
        if not isinstance(config, dict):
            return ResultStatus(
                False, f"config must be a dictionary, not {type(config)}."
            )

        res_check = self.check(
            config=config,
            skip_schema_validations=skip_schema_validations,
            skip_extra_validations=skip_extra_validations,
            is_admin=is_admin,
        )
        if not res_check.get_status():
            return res_check

        self.config = deepcopy(config)

        if save_file:
            res_save = self.save(self.config)
            if not res_save.get_status():
                return res_save

        return ResultStatus(True)

    def add_preset(self, name: str, preset: dict | str) -> None:
        """
        Adds a preset configuration.

        Args:
            name (str): Preset name.
            preset (dict | str): Configuration dictionary or path to a JSON file.

        Raises:
            TypeError: If name or preset is not of expected type.
        """
        if not isinstance(name, str) or name.strip() == "":
            raise ValueError("Preset name must be a non-empty string.")
        name = name.strip()

        if isinstance(preset, str):
            if os.path.exists(preset):
                with open(preset, "r", encoding="utf-8") as f:
                    preset_data = json.load(f)
            else:
                raise FileNotFoundError(f"Preset file not found: {preset}")
        elif isinstance(preset, dict):
            preset_data = deepcopy(preset)
        else:
            raise TypeError(
                f"preset must be a dict or file path string, not {type(preset)}."
            )

        self.presets[name] = preset_data

    def get_presets(self) -> dict[str, dict]:
        """
        Retrieves all preset configurations.

        Returns:
            dict[str, dict]: Mapping of preset names to config dictionaries.
        """
        return deepcopy(self.presets)

    def get_preset_names(self) -> list[str]:
        """
        Retrieves a list of all available preset names.

        Returns:
            list[str]: Preset names.
        """
        return list(self.presets.keys())

    def get_preset(self, name: str) -> dict | None:
        """
        Retrieves the configuration for a specific preset name.

        Args:
            name (str): Preset name.

        Returns:
            dict | None: Configuration data or None if not found.
        """
        if name in self.presets:
            return deepcopy(self.presets[name])
        return None

    def apply_preset(
        self, name: str, save_file: bool = False
    ) -> ResultStatus:
        """
        Overwrites the current global configuration with the specified preset.

        Args:
            name (str): Preset name to apply.
            save_file (bool): Whether to save to file immediately.

        Returns:
            ResultStatus: Result of applying the preset.
        """
        preset_config = self.get_preset(name)
        if preset_config is None:
            return ResultStatus(False, f"Preset '{name}' not found.")

        return self.set_config(
            config=preset_config,
            skip_schema_validations=False,
            skip_extra_validations=False,
            save_file=save_file,
            is_admin=True,
        )

    def check(
        self,
        config: dict,
        skip_schema_validations: bool = False,
        skip_extra_validations: bool = False,
        is_admin: bool = False,
    ) -> ResultStatus:
        """
        Validates a configuration against the schema, readonly constraints, and extra validation.

        Args:
            config (dict): The configuration data to validate.
            skip_schema_validations (bool): Whether to skip schema validation.
            skip_extra_validations (bool): Whether to skip extra validation.
            is_admin (bool): Whether the user is authenticated as admin.

        Returns:
            ResultStatus: Validation result.
        """
        result = ResultStatus(True)
        if not isinstance(config, dict):
            result.set_status(False)
            result.add_message(
                f"TypeError: config must be a dictionary, not {type(config)}."
            )
            return result

        if not is_admin and self.config:
            ro_check = self.check_readonly_modified(self.config, config)
            if not ro_check.get_status():
                return ro_check

        if not skip_schema_validations and self.schema:
            try:
                validate(instance=config, schema=self.schema)
            except ValidationError as e:
                result.set_status(False)
                result.add_message(f"Schema validation error: {e.message}")
                return result

        if not skip_extra_validations and self.extra_validation_func is not None:
            try:
                import inspect

                sig = inspect.signature(self.extra_validation_func)
                param_count = len(sig.parameters)
                if param_count == 1:
                    extra_res = self.extra_validation_func(config)
                else:
                    extra_res = self.extra_validation_func(
                        self.app_name, config
                    )

                if isinstance(extra_res, ResultStatus):
                    return extra_res
                elif isinstance(extra_res, bool):
                    if not extra_res:
                        result.set_status(False)
                        result.add_message("Extra validation failed.")
                        return result
            except Exception as e:
                result.set_status(False)
                result.add_message("Extra validation failed.")
                result.add_message(
                    "".join(traceback.format_exception_only(type(e), e)).strip()
                )
                return result

        return result

    def verify_admin_password(self, password: str) -> bool:
        """
        Checks if the provided password matches the admin password.

        Args:
            password (str): Password to verify.

        Returns:
            bool: True if password matches, False otherwise.
        """
        if not isinstance(password, str):
            return False
        return password == self.admin_password

    def set_admin_password(self, password: str) -> None:
        """
        Sets a new admin password.

        Args:
            password (str): New admin password.
        """
        if not isinstance(password, str):
            raise TypeError("admin_password must be a string.")
        self.admin_password = password

    def load(self) -> dict:
        """
        Loads the configuration from `load_func`, `config_file`, or defaults.

        Returns:
            dict: The loaded configuration.
        """
        if self.load_func is not None:
            try:
                loaded = self.load_func()
                if isinstance(loaded, dict):
                    self.config = deepcopy(loaded)
                    return self.get_config()
            except Exception:
                pass

        if self.config_file and os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                if isinstance(loaded, dict):
                    self.config = deepcopy(loaded)
                    return self.get_config()
            except Exception:
                pass

        return self.get_config()

    def save(self, config: dict | None = None) -> ResultStatus:
        """
        Saves the configuration to persistent storage using `save_func` or `config_file`.

        Args:
            config (dict | None): Configuration data to save. Defaults to current config.

        Returns:
            ResultStatus: Result of the save operation.
        """
        if self.saving:
            return ResultStatus(
                False,
                "Last save process has not finished yet, please try again later.",
            )
        self.saving = True

        if config is None:
            config = self.config

        try:
            if self.save_func is not None:
                import inspect

                sig = inspect.signature(self.save_func)
                param_count = len(sig.parameters)
                if param_count == 1:
                    res = self.save_func(config)
                elif param_count == 2:
                    res = self.save_func(
                        self.config_file or self.app_name, config
                    )
                elif param_count >= 3:
                    res = self.save_func(self.app_name, "default", config)
                else:
                    res = self.save_func(config)
            elif self.config_file:
                os.makedirs(
                    os.path.dirname(os.path.abspath(self.config_file)),
                    exist_ok=True,
                )
                with open(self.config_file, "w", encoding="utf-8") as f:
                    json.dump(config, f, indent=4)
                res = ResultStatus(True)
            else:
                res = ResultStatus(True)
        except Exception as e:
            res = ResultStatus(False, str(e))

        self.saving = False

        if isinstance(res, ResultStatus):
            return res
        elif isinstance(res, bool):
            if res:
                return ResultStatus(True)
            return ResultStatus(False, "An error occurred during file saving.")
        return ResultStatus(True)

    def launch_main_entry(self) -> ResultStatus:
        """
        Launches the main entry point function in a separate thread.

        Returns:
            ResultStatus: Status indicating whether program launch succeeded.
        """
        return self.main_entry_runner.run()

    def stop_server(self) -> None:
        """
        Stops the running server.
        """
        self.running = False

    def start_server(self) -> None:
        """
        Starts the web server.
        """
        self.server.serve_forever()

    def clean_up(self) -> None:
        """
        Gracefully shuts down the server and cleans up resources.
        """
        print("\nGracefully terminating...", file=BASE_OUTPUT_STREAM)
        print("Please wait for the server to stop...", end="", file=BASE_OUTPUT_STREAM)
        self.server.shutdown()
        self.server_thread.join()
        print(f'\rServer stopped.{" "*25}', file=BASE_OUTPUT_STREAM)

        print("Restoring stdout and stderr...", end="", file=BASE_OUTPUT_STREAM)
        sys.stdout = BASE_OUTPUT_STREAM
        sys.stderr = BASE_ERROR_STREAM
        print(f'\rRestored stdout and stderr.{" "*5}')
        print("Please wait for the remaining threads to stop...")
        self.main_entry_runner.wait_for_join()
        print("All remaining threads stopped.")

    def run(self, host: str = "localhost", port: int = 80) -> None:
        """
        Starts the web server and opens the configuration editor in a browser.

        Args:
            host (str): Host to bind. Defaults to "localhost".
            port (int): Port to bind. Defaults to 80.
        """
        url = (
            f"http://"
            f'{host if host != "0.0.0.0" and host != "[::]" else "localhost"}'
            f'{f":{port}" if port != 80 else ""}/'
        )
        print(f"Config Editor ({self.app_name}) URL: {url}")
        print("Open the above link in your browser if it does not pop up.")
        print("\nPress Ctrl+C to stop.")
        threading.Thread(target=webbrowser.open, args=(url,)).start()
        setdefaulttimeout(SERVER_TIMEOUT)
        self.server = make_server(host, port, self.app)

        sys.stdout = ThreadOutputStream(base_stream=BASE_OUTPUT_STREAM)
        sys.stderr = ThreadOutputStream(base_stream=BASE_ERROR_STREAM)

        self.server_thread = threading.Thread(target=self.start_server)
        self.server_thread.start()
        self.running = True
        while self.running:
            try:
                time.sleep(DAEMON_CHECK_INTERVAL)
            except KeyboardInterrupt:
                if self.running:
                    self.stop_server()
        self.clean_up()


class UserConfig:
    """
    Backwards compatibility wrapper for UserConfig.
    Delegates to global config schema and validation mechanisms.
    """

    DEFAULT_PROFILE_NAME = "Default"

    def __init__(
        self,
        name: str = "config",
        friendly_name: str = "Configuration",
        schema: dict | None = None,
        extra_validation_func: Callable | None = None,
        save_func: Callable | None = None,
        default_profile_only: bool = True,
    ) -> None:
        self.name = name
        self.friendly_name = friendly_name
        self.schema = ConfigEditor.add_order(schema or {})
        self.extra_validation_func = extra_validation_func
        self.save_func = save_func
        self.default_profile_only = default_profile_only
        self.config: dict[str, dict] = {
            UserConfig.DEFAULT_PROFILE_NAME: ConfigEditor.generate_default_json(
                self.schema
            )
        }

    def get_name(self) -> str:
        return self.name

    def get_friendly_name(self) -> str:
        return self.friendly_name

    def get_schema(self) -> dict:
        return deepcopy(self.schema)

    def set_schema(self, schema: dict) -> None:
        self.schema = ConfigEditor.add_order(schema or {})

    def get_profile_names(self) -> list[str]:
        return list(self.config.keys())

    def has_profile(self, name: str) -> bool:
        return name in self.config

    def get_config(self, profile_name: str = "Default") -> dict | None:
        return self.config.get(profile_name, None)

    def update_profile(
        self,
        name: str = "Default",
        config: dict | None = None,
        skip_schema_validations: bool = False,
        skip_extra_validations: bool = False,
        save_file: bool = False,
    ) -> ResultStatus:
        if config is None:
            config = ConfigEditor.generate_default_json(self.schema)
        self.config[name] = config
        return ResultStatus(True)
