import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import resolve_versions  # noqa: E402

CORE_PY = "3.13.15"
TAGS = [
    "3.13.15-maafw5.16.0",
    "3.13.15-maafw5.15.0",
    "3.13.15-maafw5.14.3",
    "3.13.15-maafw5.13.1",
    "3.13.15-maafw5.13.0",
    "3.14.0-maafw5.13.1",
    "3.13.15-maafw5.15.0-beta.1",
]


class ReadTests(unittest.TestCase):
    def test_read_pin(self):
        self.assertEqual(
            resolve_versions.read_pin("maafw==5.13.1\nloguru\n"), "5.13.1"
        )

    def test_read_pin_missing(self):
        with self.assertRaises(ValueError):
            resolve_versions.read_pin("loguru\n")

    def test_read_core_py(self):
        self.assertEqual(
            resolve_versions.read_core_py('CORE_PY = "3.13.15"\n'), "3.13.15"
        )

    def test_read_core_py_missing(self):
        with self.assertRaises(ValueError):
            resolve_versions.read_core_py("CORE_TAG = 'x'\n")


class ResolveTests(unittest.TestCase):
    def test_exact_match(self):
        got = resolve_versions.resolve("5.15.0", CORE_PY, TAGS)
        self.assertEqual(got.core_tag, "3.13.15-maafw5.15.0")
        self.assertEqual(got.maafw_version, "5.15.0")
        self.assertFalse(got.degraded)
        self.assertEqual(got.warnings, ())

    def test_prerelease_spelling_matches(self):
        got = resolve_versions.resolve("5.15.0b1", CORE_PY, TAGS)
        self.assertEqual(got.core_tag, "3.13.15-maafw5.15.0-beta.1")
        self.assertEqual(got.maafw_version, "5.15.0-beta.1")
        self.assertFalse(got.degraded)

    def test_cpython_filter(self):
        got = resolve_versions.resolve("5.13.1", "3.14.0", TAGS)
        self.assertEqual(got.core_tag, "3.14.0-maafw5.13.1")

    def test_fallback_to_nearest_lower(self):
        got = resolve_versions.resolve("5.15.1", CORE_PY, TAGS)
        self.assertEqual(got.core_tag, "3.13.15-maafw5.15.0")
        self.assertEqual(got.maafw_version, "5.15.0")
        self.assertTrue(got.degraded)
        self.assertEqual(len(got.warnings), 1)

    def test_fallback_uses_highest_not_newer(self):
        # 5.16.0 比 5.15.1 新，不能选；应退到 5.15.0
        got = resolve_versions.resolve("5.15.1", CORE_PY, TAGS)
        self.assertEqual(got.maafw_version, "5.15.0")

    def test_no_eligible_pairing(self):
        with self.assertRaises(ValueError):
            resolve_versions.resolve("5.12.0", CORE_PY, TAGS)

    def test_no_pairing_for_cpython(self):
        with self.assertRaises(ValueError):
            resolve_versions.resolve("5.13.1", "3.12.0", TAGS)


class MaafwTagTests(unittest.TestCase):
    def test_stable_tag(self):
        tag, warning = resolve_versions.maafw_release_tag("5.16.0", ["v5.16.0"])
        self.assertEqual(tag, "v5.16.0")
        self.assertIsNone(warning)

    def test_prerelease_original_spelling(self):
        tag, warning = resolve_versions.maafw_release_tag(
            "5.15.0b1", ["v5.16.0", "v5.15.0-beta.1"]
        )
        self.assertEqual(tag, "v5.15.0-beta.1")
        self.assertIsNone(warning)

    def test_missing_tag_falls_back(self):
        tag, warning = resolve_versions.maafw_release_tag("5.15.0", ["v5.16.0"])
        self.assertEqual(tag, "v5.15.0")
        self.assertIsNotNone(warning)


class OverrideTests(unittest.TestCase):
    def test_override_same_version(self):
        got = resolve_versions.resolve(
            "5.13.1", CORE_PY, TAGS, "3.13.15-maafw5.13.1"
        )
        self.assertEqual(got.core_tag, "3.13.15-maafw5.13.1")
        self.assertFalse(got.degraded)
        self.assertEqual(got.warnings, ())

    def test_override_bumps_to_older_core(self):
        got = resolve_versions.resolve(
            "5.13.1", CORE_PY, TAGS, "3.13.15-maafw5.13.0"
        )
        self.assertEqual(got.core_tag, "3.13.15-maafw5.13.0")
        self.assertEqual(got.maafw_version, "5.13.0")
        self.assertEqual(len(got.warnings), 1)

    def test_override_wrong_cpython(self):
        with self.assertRaises(ValueError):
            resolve_versions.resolve(
                "5.13.1", CORE_PY, TAGS, "3.14.0-maafw5.13.1"
            )

    def test_override_bad_format(self):
        with self.assertRaises(ValueError):
            resolve_versions.resolve("5.13.1", CORE_PY, TAGS, "latest")


if __name__ == "__main__":
    unittest.main()
