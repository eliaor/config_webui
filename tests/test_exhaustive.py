import json
import os
import tempfile
import threading
import time
import unittest

from src.configwebui import ConfigEditor, ResultStatus, UserConfig
from src.configwebui.utils import ProgramRunner, ThreadOutputStream


class TestExhaustiveSuite(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_file = os.path.join(self.temp_dir.name, "app_config.json")
        self.schema_file = os.path.join(self.temp_dir.name, "app_schema.json")
        self.preset1_file = os.path.join(self.temp_dir.name, "preset_a.json")
        self.preset2_file = os.path.join(self.temp_dir.name, "preset_b.json")

        self.sample_schema = {
            "title": "Comprehensive Schema",
            "type": "object",
            "properties": {
                "app_name": {"type": "string", "default": "MyTestApp"},
                "port": {"type": "integer", "default": 8000, "minimum": 1024, "maximum": 65535},
                "features": {
                    "type": "array",
                    "items": {"type": "string"},
                    "default": ["auth", "logging"]
                },
                "immutable_secret": {
                    "type": "string",
                    "readOnly": True,
                    "default": "system_secret_key_abc"
                },
                "cluster_settings": {
                    "type": "object",
                    "properties": {
                        "node_count": {"type": "integer", "default": 3},
                        "datacenter_id": {"type": "string", "readOnly": True, "default": "DC-EAST-1"}
                    },
                    "required": ["node_count"]
                }
            },
            "required": ["app_name", "port", "immutable_secret"]
        }

        self.sample_config = {
            "app_name": "MyTestApp",
            "port": 8000,
            "features": ["auth", "logging"],
            "immutable_secret": "system_secret_key_abc",
            "cluster_settings": {
                "node_count": 3,
                "datacenter_id": "DC-EAST-1"
            }
        }

        self.preset_a_config = {
            "app_name": "PresetAppA",
            "port": 9001,
            "features": ["preset_feature"],
            "immutable_secret": "preset_secret_A",
            "cluster_settings": {
                "node_count": 10,
                "datacenter_id": "DC-WEST-2"
            }
        }

        with open(self.schema_file, "w", encoding="utf-8") as f:
            json.dump(self.sample_schema, f)
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(self.sample_config, f)
        with open(self.preset1_file, "w", encoding="utf-8") as f:
            json.dump(self.preset_a_config, f)

    def tearDown(self):
        self.temp_dir.cleanup()

    # -------------------------------------------------------------
    # 1. Schema & Ordering & Defaults Tests
    # -------------------------------------------------------------
    def test_schema_ordering(self):
        ordered = ConfigEditor.add_order(self.sample_schema)
        self.assertEqual(ordered.get("propertyOrder"), 0)
        self.assertEqual(ordered["properties"]["app_name"].get("propertyOrder"), 0)
        self.assertEqual(ordered["properties"]["port"].get("propertyOrder"), 1)
        self.assertEqual(ordered["properties"]["cluster_settings"]["properties"]["node_count"].get("propertyOrder"), 0)

    def test_schema_defaults_generation(self):
        defaults = ConfigEditor.generate_default_json(self.sample_schema)
        self.assertEqual(defaults["app_name"], "MyTestApp")
        self.assertEqual(defaults["port"], 8000)
        self.assertEqual(defaults["immutable_secret"], "system_secret_key_abc")
        self.assertEqual(defaults["cluster_settings"]["node_count"], 3)

    def test_strip_readonly_functionality(self):
        stripped = ConfigEditor.strip_readonly(self.sample_schema)
        self.assertFalse(stripped["properties"]["immutable_secret"]["readOnly"])
        self.assertFalse(stripped["properties"]["cluster_settings"]["properties"]["datacenter_id"]["readOnly"])

    def test_extract_readonly_paths(self):
        paths = ConfigEditor.extract_readonly_paths(self.sample_schema)
        self.assertIn(("immutable_secret",), paths)
        self.assertIn(("cluster_settings", "datacenter_id"), paths)

    # -------------------------------------------------------------
    # 2. ConfigEditor Initialization Scenarios
    # -------------------------------------------------------------
    def test_init_from_file_path_schema(self):
        editor = ConfigEditor(
            app_name="PathSchemaApp",
            config_file=self.config_file,
            schema=self.schema_file,
            admin_password="pass123"
        )
        self.assertEqual(editor.get_config()["app_name"], "MyTestApp")
        self.assertTrue(editor.verify_admin_password("pass123"))

    def test_init_creates_missing_config_file(self):
        missing_cfg_path = os.path.join(self.temp_dir.name, "nested/dir/new_config.json")
        editor = ConfigEditor(
            app_name="NewApp",
            config_file=missing_cfg_path,
            schema=self.sample_schema,
        )
        # Should populate from schema defaults
        self.assertEqual(editor.get_config()["port"], 8000)
        # Saving should create directory and file
        res = editor.save()
        self.assertTrue(res.get_status())
        self.assertTrue(os.path.exists(missing_cfg_path))

    def test_init_with_invalid_arguments(self):
        with self.assertRaises(TypeError):
            ConfigEditor(app_name=123)
        with self.assertRaises(ValueError):
            ConfigEditor(app_name="   ")
        with self.assertRaises(TypeError):
            ConfigEditor(admin_password=999)
        with self.assertRaises(TypeError):
            ConfigEditor(extra_validation_func="not_callable")
        with self.assertRaises(TypeError):
            ConfigEditor(presets=["not_a_dict"])

    # -------------------------------------------------------------
    # 3. Presets Management Tests
    # -------------------------------------------------------------
    def test_presets_dict_and_file(self):
        editor = ConfigEditor(
            app_name="PresetApp",
            config_file=self.config_file,
            schema=self.sample_schema,
            presets={
                "PresetA": self.preset1_file,
                "PresetB": {"app_name": "DirectDictPreset", "port": 9999, "immutable_secret": "sec", "cluster_settings": {"node_count": 1}}
            }
        )
        self.assertIn("PresetA", editor.get_preset_names())
        self.assertIn("PresetB", editor.get_preset_names())

        # Apply Preset A
        res_a = editor.apply_preset("PresetA", save_file=True)
        self.assertTrue(res_a.get_status())
        self.assertEqual(editor.get_config()["app_name"], "PresetAppA")

        # Apply Preset B
        res_b = editor.apply_preset("PresetB", save_file=True)
        self.assertTrue(res_b.get_status())
        self.assertEqual(editor.get_config()["port"], 9999)

        # Apply Non-existent Preset
        res_non = editor.apply_preset("NonExistentPreset")
        self.assertFalse(res_non.get_status())

    # -------------------------------------------------------------
    # 4. Readonly & Admin Authentication Security Tests
    # -------------------------------------------------------------
    def test_guest_cannot_modify_nested_readonly(self):
        editor = ConfigEditor(
            app_name="SecApp",
            config_file=self.config_file,
            schema=self.sample_schema,
            admin_password="supersecretadmin"
        )
        curr = editor.get_config()

        # Modify top-level readonly
        curr_top = dict(curr, immutable_secret="tampered_secret")
        res_top = editor.set_config(curr_top, is_admin=False)
        self.assertFalse(res_top.get_status())

        # Modify nested readonly
        curr_nested = json.loads(json.dumps(curr))
        curr_nested["cluster_settings"]["datacenter_id"] = "DC-HACKED"
        res_nested = editor.set_config(curr_nested, is_admin=False)
        self.assertFalse(res_nested.get_status())
        self.assertIn("datacenter_id", res_nested.get_messages()[0])

    def test_admin_can_modify_all_readonly(self):
        editor = ConfigEditor(
            app_name="SecApp",
            config_file=self.config_file,
            schema=self.sample_schema,
            admin_password="supersecretadmin"
        )
        curr = json.loads(json.dumps(editor.get_config()))
        curr["immutable_secret"] = "admin_overwritten_secret"
        curr["cluster_settings"]["datacenter_id"] = "DC-ADMIN-APPROVED"

        res = editor.set_config(curr, is_admin=True, save_file=True)
        self.assertTrue(res.get_status())
        self.assertEqual(editor.get_config()["immutable_secret"], "admin_overwritten_secret")
        self.assertEqual(editor.get_config()["cluster_settings"]["datacenter_id"], "DC-ADMIN-APPROVED")

    # -------------------------------------------------------------
    # 5. Full REST API Endpoint Tests
    # -------------------------------------------------------------
    def test_rest_api_full_cycle(self):
        editor = ConfigEditor(
            app_name="RestApp",
            config_file=self.config_file,
            schema=self.sample_schema,
            presets={"PresetA": self.preset1_file},
            admin_password="mypass"
        )
        editor.app.config["TESTING"] = True
        client = editor.app.test_client()

        # 1. GET / and /config
        resp = client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"RestApp", resp.data)

        resp_redir = client.get("/config")
        self.assertEqual(resp_redir.status_code, 302)

        # 2. GET /api/config
        cfg_resp = client.get("/api/config")
        self.assertEqual(cfg_resp.status_code, 200)
        cfg_json = cfg_resp.get_json()
        self.assertTrue(cfg_json["success"])
        self.assertFalse(cfg_json["is_admin"])
        # Guest schema has readonly true
        self.assertTrue(cfg_json["schema"]["properties"]["immutable_secret"]["readOnly"])

        # 3. PATCH /api/config with valid data (guest)
        new_data = cfg_json["config"]
        new_data["port"] = 8088
        patch_resp = client.patch("/api/config", json={"config": new_data})
        self.assertEqual(patch_resp.status_code, 200)
        self.assertEqual(editor.get_config()["port"], 8088)

        # 4. PATCH /api/config with schema violation (port out of range)
        invalid_data = json.loads(json.dumps(new_data))
        invalid_data["port"] = 10  # minimum is 1024
        patch_fail = client.patch("/api/config", json={"config": invalid_data})
        self.assertEqual(patch_fail.status_code, 400)
        self.assertIn("Schema validation error", patch_fail.get_json()["messages"][0])

        # 5. PATCH /api/config tampering readonly (guest)
        tamper_data = json.loads(json.dumps(new_data))
        tamper_data["immutable_secret"] = "tampered"
        patch_tamper = client.patch("/api/config", json={"config": tamper_data})
        self.assertEqual(patch_tamper.status_code, 400)
        self.assertIn("read-only", patch_tamper.get_json()["messages"][0])

        # 6. Admin Login
        login_fail = client.post("/api/login", json={"password": "bad"})
        self.assertEqual(login_fail.status_code, 401)
        login_ok = client.post("/api/login", json={"password": "mypass"})
        self.assertEqual(login_ok.status_code, 200)
        self.assertTrue(login_ok.get_json()["is_admin"])

        # 7. Check unlocked schema after admin login
        admin_cfg_resp = client.get("/api/config")
        self.assertTrue(admin_cfg_resp.get_json()["is_admin"])
        self.assertFalse(admin_cfg_resp.get_json()["schema"]["properties"]["immutable_secret"]["readOnly"])

        # 8. Admin patches readonly field
        tamper_data["immutable_secret"] = "admin_valid_update"
        patch_admin = client.patch("/api/config", json={"config": tamper_data})
        self.assertEqual(patch_admin.status_code, 200)
        self.assertEqual(editor.get_config()["immutable_secret"], "admin_valid_update")

        # 9. Presets API
        presets_resp = client.get("/api/presets")
        self.assertIn("PresetA", presets_resp.get_json()["presets"])

        preset_detail = client.get("/api/presets/PresetA")
        self.assertEqual(preset_detail.status_code, 200)
        self.assertEqual(preset_detail.get_json()["config"]["app_name"], "PresetAppA")

        apply_resp = client.post("/api/presets/PresetA/apply")
        self.assertEqual(apply_resp.status_code, 200)
        self.assertEqual(editor.get_config()["app_name"], "PresetAppA")

        # 10. Reset API
        editor.config["port"] = 1111  # modify in memory without save
        reset_resp = client.post("/api/reset")
        self.assertEqual(reset_resp.status_code, 200)
        self.assertEqual(editor.get_config()["port"], 9001)  # reloaded from presetA saved file

        # 11. Admin Logout
        logout_resp = client.post("/api/logout")
        self.assertEqual(logout_resp.status_code, 200)
        auth_resp = client.get("/api/auth_status")
        self.assertFalse(auth_resp.get_json()["is_admin"])

    # -------------------------------------------------------------
    # 6. Extra Validation Callback Variations
    # -------------------------------------------------------------
    def test_extra_validation_return_types(self):
        # Case A: returns ResultStatus(False)
        def val_res_status(cfg):
            return ResultStatus(False, "Custom validation failure message")

        ed_a = ConfigEditor(app_name="A", schema=self.sample_schema, config=self.sample_config, extra_validation_func=val_res_status)
        res_a = ed_a.set_config(self.sample_config, is_admin=True)
        self.assertFalse(res_a.get_status())
        self.assertEqual(res_a.get_messages(), ["Custom validation failure message"])

        # Case B: returns bool
        def val_bool(cfg):
            return False

        ed_b = ConfigEditor(app_name="B", schema=self.sample_schema, config=self.sample_config, extra_validation_func=val_bool)
        res_b = ed_b.set_config(self.sample_config, is_admin=True)
        self.assertFalse(res_b.get_status())

        # Case C: 2-argument extra validation (name, config)
        def val_two_args(name, cfg):
            if name == "C":
                return ResultStatus(True)
            return ResultStatus(False)

        ed_c = ConfigEditor(app_name="C", schema=self.sample_schema, config=self.sample_config, extra_validation_func=val_two_args)
        res_c = ed_c.set_config(self.sample_config, is_admin=True)
        self.assertTrue(res_c.get_status())

    # -------------------------------------------------------------
    # 7. ProgramRunner & Background Execution Tests
    # -------------------------------------------------------------
    def test_program_runner_execution_and_errors(self):
        def worker_success():
            print("Line 1 output")
            print("Line 2 output")
            return ResultStatus(True, "All tasks completed.")

        runner = ProgramRunner(function=worker_success)
        res_start = runner.run()
        self.assertTrue(res_start.get_status())
        runner.wait_for_join()

        output = runner.get_combined_output()
        self.assertIn("Line 1 output", output)
        self.assertIn("Line 2 output", output)
        self.assertTrue(runner.get_res().get_status())

        # Test runner exception capture
        def worker_crash():
            raise RuntimeError("Intentional test crash")

        runner_crash = ProgramRunner(function=worker_crash, hide_terminal_error=True)
        runner_crash.run()
        runner_crash.wait_for_join()
        self.assertFalse(runner_crash.get_res().get_status())
        self.assertIn("RuntimeError: Intentional test crash", runner_crash.get_res().get_messages()[0])

    # -------------------------------------------------------------
    # 8. UserConfig Backward Compatibility Wrapper
    # -------------------------------------------------------------
    def test_user_config_compat_wrapper(self):
        uc = UserConfig(name="compat_test", friendly_name="Compat Test", schema=self.sample_schema)
        self.assertEqual(uc.get_name(), "compat_test")
        self.assertEqual(uc.get_friendly_name(), "Compat Test")
        self.assertIn("Default", uc.get_profile_names())
        self.assertTrue(uc.has_profile("Default"))
        self.assertIsNotNone(uc.get_config("Default"))


if __name__ == "__main__":
    unittest.main()
