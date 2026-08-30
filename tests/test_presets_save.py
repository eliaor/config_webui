import os
import sys
import unittest
from copy import deepcopy

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from configwebui import ConfigEditor, ResultStatus


class TestPresetSaveAsGuest(unittest.TestCase):
    def setUp(self):
        self.schema = {
            "type": "object",
            "properties": {
                "server": {
                    "type": "object",
                    "properties": {
                        "port": {"type": "integer", "default": 8080},
                        "host": {"type": "string", "default": "127.0.0.1"},
                    },
                },
                "system_protected": {
                    "type": "object",
                    "properties": {
                        "cluster_uuid": {
                            "type": "string",
                            "readOnly": True,
                            "default": "CLS-DEFAULT",
                        },
                        "tier": {
                            "type": "string",
                            "readOnly": True,
                            "default": "Dev",
                        },
                    },
                },
            },
        }
        self.presets = {
            "Development": {
                "server": {"port": 8080, "host": "127.0.0.1"},
                "system_protected": {
                    "cluster_uuid": "CLS-DEV-001",
                    "tier": "Development",
                },
            },
            "Production": {
                "server": {"port": 443, "host": "0.0.0.0"},
                "system_protected": {
                    "cluster_uuid": "CLS-PROD-999",
                    "tier": "Production",
                },
            },
        }
        self.editor = ConfigEditor(
            app_name="TestApp",
            schema=self.schema,
            presets=self.presets,
            default_preset="Development",
            admin_password="secret_admin_pass",
        )
        self.client = self.editor.app.test_client()

    def test_guest_can_apply_and_save_preset(self):
        # 1. Initially active is Development
        cfg = self.editor.get_config()
        self.assertEqual(cfg["system_protected"]["tier"], "Development")

        # 2. Guest applies Production preset via API
        resp = self.client.post(
            "/api/presets/Production/apply", json={"save": True}
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(
            data["config"]["system_protected"]["tier"], "Production"
        )

        # 3. Guest modifies editable field (server.port) on top of Production preset and saves
        new_cfg = deepcopy(data["config"])
        new_cfg["server"]["port"] = 8443
        save_resp = self.client.patch("/api/config", json={"config": new_cfg})
        self.assertEqual(save_resp.status_code, 200)
        save_data = save_resp.get_json()
        self.assertTrue(save_data["success"])
        self.assertEqual(self.editor.get_config()["server"]["port"], 8443)
        self.assertEqual(
            self.editor.get_config()["system_protected"]["tier"], "Production"
        )

    def test_guest_cannot_tamper_readonly_field(self):
        # Guest tries to set cluster_uuid to an unauthorized value
        cfg = self.editor.get_config()
        tampered_cfg = deepcopy(cfg)
        tampered_cfg["system_protected"]["cluster_uuid"] = (
            "ILLEGAL-CLUSTER-ID"
        )

        save_resp = self.client.patch(
            "/api/config", json={"config": tampered_cfg}
        )
        self.assertEqual(save_resp.status_code, 400)
        save_data = save_resp.get_json()
        self.assertFalse(save_data["success"])
        self.assertTrue(
            any("read-only" in msg for msg in save_data["messages"])
        )

    def test_admin_can_modify_readonly_field(self):
        # 1. Login as admin
        login_resp = self.client.post(
            "/api/login", json={"password": "secret_admin_pass"}
        )
        self.assertEqual(login_resp.status_code, 200)

        # 2. Admin modifies readonly field
        cfg = self.editor.get_config()
        custom_cfg = deepcopy(cfg)
        custom_cfg["system_protected"]["cluster_uuid"] = (
            "CUSTOM-ADMIN-CLUSTER-OVERRIDE"
        )

        save_resp = self.client.patch(
            "/api/config", json={"config": custom_cfg}
        )
        self.assertEqual(save_resp.status_code, 200)
        self.assertTrue(save_resp.get_json()["success"])
        self.assertEqual(
            self.editor.get_config()["system_protected"]["cluster_uuid"],
            "CUSTOM-ADMIN-CLUSTER-OVERRIDE",
        )


if __name__ == "__main__":
    unittest.main()
