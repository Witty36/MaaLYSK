import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import prepare  # noqa: E402

SOURCE = {
    "interface_version": 2,
    "version": "v0.4.3-beta1",
    "mirrorchyan_rid": "MaaLYSK",
    "mirrorchyan_multiplatform": True,
    "controller": [
        {"name": "ADB模拟器", "type": "Adb"},
        {"name": "PlayCover", "type": "PlayCover"},
    ],
    "agent": {"child_exec": "python", "child_args": ["-u", "../agent/main.py"]},
}


class AndroidInterfaceTests(unittest.TestCase):
    def test_version_is_replaced_without_touching_source(self):
        interface = prepare.android_interface(SOURCE, "v0.4.6-beta1")
        self.assertEqual(interface["version"], "v0.4.6-beta1")
        self.assertEqual(SOURCE["version"], "v0.4.3-beta1")

    def test_mirrorchyan_fields_removed(self):
        interface = prepare.android_interface(SOURCE, "v0.4.6-beta1")
        self.assertNotIn("mirrorchyan_rid", interface)
        self.assertNotIn("mirrorchyan_multiplatform", interface)

    def test_agent_args_are_payload_relative(self):
        interface = prepare.android_interface(SOURCE, "v0.4.6-beta1")
        self.assertEqual(
            interface["agent"],
            {"child_exec": "python3", "child_args": ["-u", "agent/main.py"]},
        )

    def test_controllers_keep_names(self):
        interface = prepare.android_interface(SOURCE, "v0.4.6-beta1")
        self.assertEqual(
            [item["name"] for item in interface["controller"]],
            ["ADB模拟器", "PlayCover"],
        )

    def test_license_points_to_combined_notice(self):
        interface = prepare.android_interface(SOURCE, "v0.4.6-beta1")
        self.assertEqual(interface["license"], "LICENSES.md")

    def test_requires_adb_controller(self):
        source = dict(SOURCE, controller=[{"name": "PC", "type": "Win32"}])
        with self.assertRaises(ValueError):
            prepare.android_interface(source, "v0.4.6-beta1")


class VersionTests(unittest.TestCase):
    def test_release_and_ci_versions(self):
        for version in ("v0.4.6-beta1", "0.4.6", "ci.123-abc1234"):
            self.assertEqual(prepare.validate_version(version), version)

    def test_rejects_unknown_version(self):
        for version in ("latest", "", "v0.4", "../escape"):
            with self.assertRaises(ValueError):
                prepare.validate_version(version)


if __name__ == "__main__":
    unittest.main()
