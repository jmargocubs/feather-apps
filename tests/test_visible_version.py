#!/usr/bin/env python3
"""Marketing version and build number stay independent catalog fields."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from apps import assert_independent_version_fields  # noqa: E402


class IndependentVersionFieldsTests(unittest.TestCase):
    def test_accepts_independent_marketing_and_build(self):
        self.assertEqual(
            assert_independent_version_fields("1.0.0", 106),
            ("1.0.0", "106"),
        )
        self.assertEqual(
            assert_independent_version_fields("1.0.0", "105"),
            ("1.0.0", "105"),
        )
        self.assertEqual(
            assert_independent_version_fields("0.3.0", 48),
            ("0.3.0", "48"),
        )

    def test_accepts_aligned_form_without_requiring_it(self):
        # major.minor.<build> remains valid; it is not required.
        self.assertEqual(
            assert_independent_version_fields("1.0.106", 106),
            ("1.0.106", "106"),
        )

    def test_rejects_non_numeric_marketing_version(self):
        with self.assertRaises(ValueError):
            assert_independent_version_fields("v1.0.0", 106)
        with self.assertRaises(ValueError):
            assert_independent_version_fields("1", 106)

    def test_rejects_non_numeric_build(self):
        with self.assertRaises(ValueError):
            assert_independent_version_fields("1.0.0", "106a")
        with self.assertRaises(ValueError):
            assert_independent_version_fields("1.0.0", "1.0.106")

    def test_update_source_accepts_independent_1_0_0_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = os.path.join(tmp, "source.json")
            with open(os.path.join(ROOT, "source.json"), encoding="utf-8") as handle:
                data = handle.read()
            with open(source, "w", encoding="utf-8") as handle:
                handle.write(data)
            result = subprocess.run(
                [
                    sys.executable,
                    os.path.join(ROOT, "scripts", "update_source.py"),
                    "--source",
                    source,
                    "--app",
                    "kyro",
                    "--version",
                    "1.0.0",
                    "--build",
                    "1000",
                    "--size",
                    "100",
                    "--tag",
                    "kyro-ios-v1.0.0-build1000-rc1",
                    "--asset",
                    "Kyro-v1.0.0-Build1000-Unsigned.ipa",
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                result.returncode,
                0,
                msg=f"stdout={result.stdout!r} stderr={result.stderr!r}",
            )
            import json

            with open(source, encoding="utf-8") as catalog_handle:
                catalog = json.load(catalog_handle)
            kyro = next(
                app
                for app in catalog["apps"]
                if app["bundleIdentifier"] == "com.cubbiestream.kyro"
            )
            head = kyro["versions"][0]
            self.assertEqual(head["version"], "1.0.0")
            self.assertEqual(head["buildVersion"], "1000")
            self.assertEqual(kyro["name"], "Kyro X — Build 1000")


if __name__ == "__main__":
    unittest.main()
