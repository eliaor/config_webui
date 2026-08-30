import json
import os
import tempfile
import unittest

from src.configwebui import ConfigEditor, ResultStatus


class TestConfigWebUI(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_path = os.path.join(self.temp_dir.name, "config.json")
        self.preset_path = os.path.join(self.temp_dir.name, "preset1.json")

        self.schema = {
            "title": "Test Schema",
            "type": "object",
            "properties": {
                "server_port": {"type": "integer", "default": 8080},
                "debug": {"type": "boolean", "default": False},
                "api_key": {"type": "string", "readOnly": True, "default": "read_only_key_123"},
                "sub_config": {
                    "type": "object",
                    "properties": {
                        "read_only_var": {"type": "string", "readOnly": True, "default": "locked_val"},
                        "editable_var": {"type": "string", "default": "can_edit"}
                    }
                }
            },
            "required": ["server_port", "api_key"]
        }

        self.initial_config = {
            "server_port": 8080,
            "debug": False,
            "api_key": "read_only_key_123",
            "sub_config": {
                "read_only_var": "locked_val",
                "editable_var": "can_edit"
            }
        }

        self.preset1_config = {
            "server_port": 9000,
            "debug": True,
            "api_key": "preset_api_key_456",
            "sub_config": {
                "read_only_var": "preset_locked",
                "editable_var": "preset_edit"
            }
        }

        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.initial_config, f, indent=4)

        with open(self.preset_path, "w", encoding="utf-8") as f:
            json.dump(self.preset1_config, f, indent=4)

        self.editor = ConfigEditor(
            app_name="Test Editor",
            config_file=self.config_path,
            schema=self.schema,
            presets={
                "Default": self.initial_config,
                "CustomPreset": self.preset_path,
            },
            admin_password="testadminpass"
        )
        self.editor.app.config["TESTING"] = True
        self.client = self.editor.app.test_client()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_initial_state(self):
        config = self.editor.get_config()
        self.assertEqual(config["server_port"], 8080)
        self.assertEqual(config["api_key"], "read_only_key_123")
        self.assertEqual(self.editor.get_preset_names(), ["Default", "CustomPreset"])

    def test_index_and_redirects(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Test Editor", res.data)
        self.assertIn(b"CustomPreset", res.data)

        # /config should redirect to /
        redir = self.client.get("/config")
        self.assertEqual(redir.status_code, 302)
        self.assertEqual(redir.headers["Location"], "/")

    def test_presets_apply(self):
        # Apply custom preset from file
        res = self.editor.apply_preset("CustomPreset", save_file=True)
        self.assertTrue(res.get_status())
        current = self.editor.get_config()
        self.assertEqual(current["server_port"], 9000)
        self.assertEqual(current["api_key"], "preset_api_key_456")

        # Verify saved to file
        with open(self.config_path, "r", encoding="utf-8") as f:
            saved_file_content = json.load(f)
        self.assertEqual(saved_file_content["server_port"], 9000)

    def test_readonly_restrictions_for_guest(self):
        guest_schema = self.editor.get_schema(is_admin=False)
        self.assertTrue(guest_schema["properties"]["api_key"]["readOnly"])
        self.assertTrue(guest_schema["properties"]["sub_config"]["properties"]["read_only_var"]["readOnly"])

        # Try to modify read-only field as guest
        modified_config = self.editor.get_config()
        modified_config["api_key"] = "hacked_key"

        res = self.editor.set_config(modified_config, is_admin=False)
        self.assertFalse(res.get_status())
        self.assertIn("read-only", res.get_messages()[0])

        # Modifying non-readonly field should succeed
        modified_config["api_key"] = "read_only_key_123"
        modified_config["server_port"] = 3000
        res = self.editor.set_config(modified_config, is_admin=False)
        self.assertTrue(res.get_status())
        self.assertEqual(self.editor.get_config()["server_port"], 3000)

    def test_admin_mode_unlocks_readonly(self):
        admin_schema = self.editor.get_schema(is_admin=True)
        self.assertFalse(admin_schema["properties"]["api_key"]["readOnly"])
        self.assertFalse(admin_schema["properties"]["sub_config"]["properties"]["read_only_var"]["readOnly"])

        # Admin modifying read-only field should succeed
        modified_config = self.editor.get_config()
        modified_config["api_key"] = "admin_changed_key"
        modified_config["sub_config"]["read_only_var"] = "admin_changed_var"

        res = self.editor.set_config(modified_config, is_admin=True, save_file=True)
        self.assertTrue(res.get_status())
        self.assertEqual(self.editor.get_config()["api_key"], "admin_changed_key")

    def test_admin_login_logout_flow(self):
        # Incorrect login
        res = self.client.post("/api/login", json={"password": "wrongpassword"})
        self.assertEqual(res.status_code, 401)
        self.assertFalse(res.get_json()["success"])

        # Check auth status
        auth_res = self.client.get("/api/auth_status")
        self.assertFalse(auth_res.get_json()["is_admin"])

        # Correct login
        login_res = self.client.post("/api/login", json={"password": "testadminpass"})
        self.assertEqual(login_res.status_code, 200)
        self.assertTrue(login_res.get_json()["is_admin"])

        # Check auth status now
        auth_res = self.client.get("/api/auth_status")
        self.assertTrue(auth_res.get_json()["is_admin"])

        # Schema returned via API is unlocked
        config_res = self.client.get("/api/config")
        schema = config_res.get_json()["schema"]
        self.assertFalse(schema["properties"]["api_key"]["readOnly"])

        # Admin saves modified readonly field via API
        current_data = config_res.get_json()["config"]
        current_data["api_key"] = "new_admin_api_key_via_api"
        patch_res = self.client.patch("/api/config", json={"config": current_data})
        self.assertEqual(patch_res.status_code, 200)

        # Logout
        logout_res = self.client.post("/api/logout")
        self.assertEqual(logout_res.status_code, 200)
        self.assertFalse(logout_res.get_json()["is_admin"])

        # Guest trying to modify readonly via API should now fail (400)
        current_data["api_key"] = "guest_trying_to_modify"
        patch_res = self.client.patch("/api/config", json={"config": current_data})
        self.assertEqual(patch_res.status_code, 400)
        self.assertIn("read-only", patch_res.get_json()["messages"][0])

    def test_presets_api(self):
        # List presets
        res = self.client.get("/api/presets")
        self.assertEqual(res.status_code, 200)
        self.assertIn("CustomPreset", res.get_json()["presets"])

        # Get preset data
        res = self.client.get("/api/presets/CustomPreset")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["config"]["server_port"], 9000)

        # Apply preset
        res = self.client.post("/api/presets/CustomPreset/apply")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(self.editor.get_config()["server_port"], 9000)

    def test_reset_api(self):
        # Change in memory without saving to file
        self.editor.config["server_port"] = 1234
        res = self.client.post("/api/reset")
        self.assertEqual(res.status_code, 200)
        # Should reload original from file (8080)
        self.assertEqual(self.editor.get_config()["server_port"], 8080)

    def test_extra_validation(self):
        def port_validator(cfg):
            if cfg.get("server_port", 0) < 1024:
                return ResultStatus(False, "Port must be >= 1024")
            return ResultStatus(True)

        val_editor = ConfigEditor(
            app_name="Val Editor",
            schema=self.schema,
            config=self.initial_config,
            extra_validation_func=port_validator,
        )

        invalid_cfg = dict(self.initial_config, server_port=80)
        res = val_editor.set_config(invalid_cfg, is_admin=True)
        self.assertFalse(res.get_status())
        self.assertIn("Port must be >= 1024", res.get_messages())

    def test_custom_save_and_load_callbacks(self):
        store = {"saved": None}

        def custom_save(cfg):
            store["saved"] = dict(cfg)
            return ResultStatus(True)

        def custom_load():
            return {"server_port": 7777, "api_key": "callback_key"}

        cb_editor = ConfigEditor(
            app_name="Callback Editor",
            schema=self.schema,
            save_func=custom_save,
            load_func=custom_load,
        )

        self.assertEqual(cb_editor.get_config()["server_port"], 7777)
        cb_editor.set_config({"server_port": 8888, "api_key": "callback_key"}, save_file=True, is_admin=True)
        self.assertEqual(store["saved"]["server_port"], 8888)

    def test_program_runner_and_output(self):
        def sample_program():
            print("Hello from test program!")
            return ResultStatus(True, "Finished successfully.")

        runner_editor = ConfigEditor(
            app_name="Runner Editor",
            config_file=self.config_path,
            schema=self.schema,
            main_entry=sample_program,
        )
        runner_client = runner_editor.app.test_client()

        launch_res = runner_client.get("/api/launch")
        self.assertEqual(launch_res.status_code, 200)

        # Wait for thread to finish
        runner_editor.main_entry_runner.wait_for_join()

        output_res = runner_client.get("/api/get_terminal_output")
        self.assertEqual(output_res.status_code, 200)
        self.assertIn("Hello from test program!", output_res.get_json()["combined_output"])

        # Clear output
        clear_res = runner_client.post("/api/clear_terminal_output")
        self.assertEqual(clear_res.status_code, 204)


if __name__ == "__main__":
    unittest.main()
