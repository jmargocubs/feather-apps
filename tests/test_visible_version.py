#!/usr/bin/env python3
"""Visible marketing version = major.minor.<build> for signing-app display."""

from __future__ import annotations

import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from apps import assert_version_aligned_with_build, visible_marketing_version  # noqa: E402


class VisibleMarketingVersionTests(unittest.TestCase):
    def test_kyro_style_base(self):
        self.assertEqual(visible_marketing_version("1.0.0", 105), "1.0.105")
        self.assertEqual(visible_marketing_version("1.0.0", "102"), "1.0.102")

    def test_two_component_base(self):
        self.assertEqual(visible_marketing_version("1.0", 18), "1.0.18")

    def test_sunny_base(self):
        self.assertEqual(visible_marketing_version("0.3.0", 48), "0.3.48")

    def test_idempotent_when_already_aligned(self):
        self.assertEqual(visible_marketing_version("1.0.105", 105), "1.0.105")
        self.assertEqual(visible_marketing_version("0.3.48", "48"), "0.3.48")

    def test_replaces_mismatched_patch_with_build(self):
        # Base keeps major.minor; build always becomes the patch.
        self.assertEqual(visible_marketing_version("1.0.0", 106), "1.0.106")
        self.assertEqual(visible_marketing_version("1.0.105", 106), "1.0.106")

    def test_assert_aligned(self):
        self.assertEqual(assert_version_aligned_with_build("1.0.105", 105), "1.0.105")
        with self.assertRaises(ValueError):
            assert_version_aligned_with_build("1.0.0", 105)

    def test_cli_visible_version(self):
        result = subprocess.run(
            [sys.executable, os.path.join(ROOT, "scripts", "apps.py"), "visible-version", "1.0.0", "105"],
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertEqual(result.stdout.strip(), "1.0.105")


if __name__ == "__main__":
    unittest.main()
