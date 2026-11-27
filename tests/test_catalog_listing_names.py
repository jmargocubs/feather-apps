#!/usr/bin/env python3
"""Tests for repository listing titles: App Name — Build N."""

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
    catalog_listing_name,
    current_listing_name,
    parse_catalog_listing_name,
)


class CatalogListingNameTests(unittest.TestCase):
    def run_update(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "update_source.py"), *args],
            capture_output=True,
            text=True,
        )

    def test_listing_name_format_for_all_apps(self):
        for app_id, meta in APPS.items():
            name = catalog_listing_name(app_id, 42)
            self.assertEqual(name, f"{meta['source_name']} — Build 42")
            parsed = parse_catalog_listing_name(name)
            self.assertEqual(parsed, (meta["source_name"], "42"))

    def test_current_listing_name_uses_head_version(self):
        versions = [
            {"version": "1.0.0", "buildVersion": "101"},
            {"version": "1.0.0", "buildVersion": "100"},
        ]
        self.assertEqual(current_listing_name("kyro", versions, "1"), "Kyro X — Build 101")

    def test_publish_sets_listing_name_and_preserves_history(self):
        with tempfile.TemporaryDirectory() as directory:
            source = pathlib.Path(directory) / "source.json"
            shutil.copy(ROOT / "source.json", source)
            before = json.loads(source.read_text())
            kyro_before = next(
                app for app in before["apps"] if app["bundleIdentifier"] == "com.cubbiestream.kyro"
            )
            history_len = len(kyro_before["versions"])
            first_url = kyro_before["versions"][0]["downloadURL"]

            result = self.run_update(
                "--source",
                str(source),
                "--app",
                "kyro",
                "--version",
                "9.9.1001",
                "--build",
                "1001",
                "--size",
                "111",
                "--tag",
                "kyro-ios-v9.9.1001-build1001-rc1",
                "--asset",
                "Kyro-test.ipa",
                "--date",
                "2026-11-20",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            after = json.loads(source.read_text())
            kyro = next(
                app for app in after["apps"] if app["bundleIdentifier"] == "com.cubbiestream.kyro"
            )
            self.assertEqual(kyro["name"], "Kyro X — Build 1001")
            self.assertEqual(len(kyro["versions"]), history_len + 1)
            self.assertEqual(kyro["versions"][1]["downloadURL"], first_url)
            self.assertEqual(kyro["bundleIdentifier"], "com.cubbiestream.kyro")
            # Other apps untouched aside from optional pre-existing names.
            zepzi = next(
                app for app in after["apps"] if app["bundleIdentifier"] == "app.flippy.reader"
            )
            sunny = next(
                app
                for app in after["apps"]
                if app["bundleIdentifier"] == "com.sunnymeadow.app.beta"
            )
            self.assertEqual(zepzi["bundleIdentifier"], "app.flippy.reader")
            self.assertEqual(sunny["bundleIdentifier"], "com.sunnymeadow.app.beta")

    def test_idempotent_republish_refreshes_stale_listing_name_only(self):
        with tempfile.TemporaryDirectory() as directory:
            source = pathlib.Path(directory) / "source.json"
            data = json.loads((ROOT / "source.json").read_text())
            kyro = next(
                app for app in data["apps"] if app["bundleIdentifier"] == "com.cubbiestream.kyro"
            )
            head = copy.deepcopy(kyro["versions"][0])
            kyro["name"] = "Kyro"  # stale listing title
            source.write_text(json.dumps(data, indent=2) + "\n")

            asset = pathlib.Path(head["downloadURL"]).name
            # Reconstruct tag from known kyro pattern in URL path.
            tag = head["downloadURL"].split("/download/")[1].split("/")[0]
            common = [
                "--source",
                str(source),
                "--idempotent",
                "--app",
                "kyro",
                "--version",
                head["version"],
                "--build",
                str(head["buildVersion"]),
                "--size",
                str(head["size"]),
                "--tag",
                tag,
                "--asset",
                asset,
                "--download-url",
                head["downloadURL"],
                "--date",
                head["date"],
            ]
            first = self.run_update(*common)
            self.assertEqual(first.returncode, 0, first.stderr)
            mid = json.loads(source.read_text())
            kyro_mid = next(
                app for app in mid["apps"] if app["bundleIdentifier"] == "com.cubbiestream.kyro"
            )
            self.assertEqual(
                kyro_mid["name"], f"Kyro X — Build {head['buildVersion']}"
            )
            self.assertEqual(kyro_mid["versions"][0], head)

            before_bytes = source.read_bytes()
            second = self.run_update(*common)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual(source.read_bytes(), before_bytes)
            self.assertIn("already matches", second.stdout)

    def test_refresh_listing_names_updates_all_known_apps(self):
        with tempfile.TemporaryDirectory() as directory:
            source = pathlib.Path(directory) / "source.json"
            data = json.loads((ROOT / "source.json").read_text())
            for app in data["apps"]:
                app["name"] = "stale"
            source.write_text(json.dumps(data, indent=2) + "\n")
            result = self.run_update("--source", str(source), "--refresh-listing-names")
            self.assertEqual(result.returncode, 0, result.stderr)
            after = json.loads(source.read_text())
            by_bundle = {meta["bundle"]: app_id for app_id, meta in APPS.items()}
            for app in after["apps"]:
                app_id = by_bundle[app["bundleIdentifier"]]
                head_build = app["versions"][0]["buildVersion"]
                self.assertEqual(app["name"], catalog_listing_name(app_id, head_build))
                # History preserved
                self.assertGreaterEqual(len(app["versions"]), 1)

    def test_live_source_files_are_valid_json_with_listing_names(self):
        for relative in ("source.json", "tvos-source.json"):
            path = ROOT / relative
            data = json.loads(path.read_text())
            self.assertIsInstance(data["apps"], list)
            validate = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "validate_source.py"), str(path)],
                capture_output=True,
                text=True,
            )
            self.assertEqual(validate.returncode, 0, validate.stderr)
            by_bundle = {meta["bundle"]: app_id for app_id, meta in APPS.items()}
            for app in data["apps"]:
                app_id = by_bundle.get(app["bundleIdentifier"])
                if app_id is None:
                    continue
                expected = catalog_listing_name(app_id, app["versions"][0]["buildVersion"])
                self.assertEqual(app["name"], expected, relative)


if __name__ == "__main__":
    unittest.main(verbosity=2)
