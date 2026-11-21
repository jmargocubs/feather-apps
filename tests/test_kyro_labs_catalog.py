#!/usr/bin/env python3
"""Kyro Labs is a separate catalog app: own bundle, tags, listing and history.

Publishing Labs must never alter stable Kyro's entry, and publishing stable Kyro must never
alter Labs's. Every publish here runs against a temporary copy of source.json.
"""

from __future__ import annotations

import copy
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from apps import (  # noqa: E402
    APPS,
    bundle_for,
    catalog_listing_name,
    download_url_for,
    tag_for,
)

STABLE = "com.cubbiestream.kyro"
LABS = "com.cubbiestream.kyro.labs"


def entry(data: dict, bundle: str):
    return next((app for app in data["apps"] if app["bundleIdentifier"] == bundle), None)


class KyroLabsCatalogTests(unittest.TestCase):
    def update(self, source: pathlib.Path, app: str, version: str, build: str, tag: str, asset: str):
        return subprocess.run(
            [
                sys.executable, str(ROOT / "scripts" / "update_source.py"),
                "--source", str(source), "--app", app, "--version", version, "--build", build,
                "--size", "123", "--tag", tag, "--asset", asset, "--date", "2026-11-22",
                "--allow-create",  # as publish_ipa.py does
            ],
            capture_output=True, text=True,
        )

    def test_identities_never_collide(self):
        self.assertEqual(bundle_for("kyro"), STABLE)
        self.assertEqual(bundle_for("kyro-labs"), LABS)
        bundles = [meta["bundle"] for meta in APPS.values()]
        self.assertEqual(len(bundles), len(set(bundles)), "two catalog apps share a bundle ID")
        kyro, labs = APPS["kyro"], APPS["kyro-labs"]
        for key in ("bundle", "tag_template", "source_name", "display_name", "icon_url"):
            self.assertNotEqual(kyro[key], labs[key], f"{key} is shared with stable Kyro")

    def test_tags_listing_and_assets_are_separate_for_the_same_numbers(self):
        self.assertNotEqual(tag_for("kyro", "1.0.110", "110"), tag_for("kyro-labs", "1.0.110", "110"))
        self.assertEqual(tag_for("kyro-labs", "1.0.0", "1"), "kyro-labs-ios-v1.0.0-build1-rc1")
        self.assertEqual(catalog_listing_name("kyro-labs", 1), "Kyro Labs — Build 1")
        self.assertNotEqual(catalog_listing_name("kyro", 1), catalog_listing_name("kyro-labs", 1))
        # A stable tag never matches a Labs tag by prefix, so tooling that finds one by prefix
        # cannot pick up the other.
        self.assertFalse(tag_for("kyro-labs", "1.0.0", "1").startswith("kyro-ios-"))
        self.assertFalse(tag_for("kyro", "1.0.110", "110").startswith("kyro-labs-"))
        labs_url = download_url_for("kyro-labs", "1.0.0", "1", "Kyro-Labs-1.0.0-1-ios-unsigned-arm64.ipa")
        self.assertIn("/releases/download/kyro-labs-ios-v1.0.0-build1-rc1/", labs_url)

    def test_labs_icon_is_its_own_file(self):
        stable_icon = ROOT / "assets" / "kyro" / "icon.png"
        labs_icon = ROOT / "assets" / "kyro-labs" / "icon.png"
        self.assertTrue(labs_icon.is_file())
        self.assertNotEqual(stable_icon.read_bytes(), labs_icon.read_bytes())

    def test_publishing_labs_leaves_stable_and_other_apps_untouched(self):
        with tempfile.TemporaryDirectory() as directory:
            source = pathlib.Path(directory) / "source.json"
            shutil.copy(ROOT / "source.json", source)
            before = json.loads(source.read_text())
            self.assertIsNone(entry(before, LABS), "Labs must not exist before its first publish")

            result = self.update(source, "kyro-labs", "1.0.0", "1",
                                 "kyro-labs-ios-v1.0.0-build1-rc1", "Kyro-Labs-1.0.0-1-ios-unsigned-arm64.ipa")
            self.assertEqual(result.returncode, 0, result.stderr)
            after = json.loads(source.read_text())

            labs = entry(after, LABS)
            self.assertIsNotNone(labs)
            self.assertEqual(labs["name"], "Kyro Labs — Build 1")
            self.assertEqual(labs["bundleIdentifier"], LABS)
            self.assertEqual(len(labs["versions"]), 1)
            self.assertIn("kyro-labs-ios-v1.0.0-build1-rc1", labs["versions"][0]["downloadURL"])
            # Every pre-existing app, stable Kyro included, is byte-for-byte the same.
            for app in before["apps"]:
                self.assertEqual(entry(after, app["bundleIdentifier"]), app,
                                 f"{app['bundleIdentifier']} changed when Labs was published")
            self.assertEqual(len(after["apps"]), len(before["apps"]) + 1)

    def test_publishing_stable_leaves_labs_untouched(self):
        with tempfile.TemporaryDirectory() as directory:
            source = pathlib.Path(directory) / "source.json"
            shutil.copy(ROOT / "source.json", source)
            self.assertEqual(self.update(source, "kyro-labs", "1.0.0", "1",
                                         "kyro-labs-ios-v1.0.0-build1-rc1", "labs.ipa").returncode, 0)
            labs_before = copy.deepcopy(entry(json.loads(source.read_text()), LABS))

            result = self.update(source, "kyro", "9.9.2001", "2001",
                                 "kyro-ios-v9.9.2001-build2001-rc1", "Kyro-test.ipa")
            self.assertEqual(result.returncode, 0, result.stderr)
            after = json.loads(source.read_text())
            self.assertEqual(entry(after, LABS), labs_before)
            self.assertEqual(entry(after, STABLE)["name"], "Kyro — Build 2001")

    def test_labs_build_numbers_are_independent_of_stable(self):
        with tempfile.TemporaryDirectory() as directory:
            source = pathlib.Path(directory) / "source.json"
            shutil.copy(ROOT / "source.json", source)
            # Stable is already past build 100; Labs must still accept build 1.
            result = self.update(source, "kyro-labs", "1.0.0", "1",
                                 "kyro-labs-ios-v1.0.0-build1-rc1", "labs.ipa")
            self.assertEqual(result.returncode, 0, result.stderr)
            labs = entry(json.loads(source.read_text()), LABS)
            self.assertEqual(labs["versions"][0]["buildVersion"], "1")


if __name__ == "__main__":
    unittest.main()
