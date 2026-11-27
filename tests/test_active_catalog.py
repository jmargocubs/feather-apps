#!/usr/bin/env python3
"""Catalog policy (audit 2026-11-27): exactly four active listings; retired ones can't return."""
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from apps import ACTIVE_BUNDLES, APP_IDS, APPS, RETIRED_APPS, RETIRED_BUNDLES  # noqa: E402

ACTIVE = {
    "com.cubbiestream.kyro": "Kyro X iOS",
    "com.cubbiestream.kyro.tvos": "Kyro X tvOS",
    "app.flippy.reader": "Zepzi",
    "com.sunnymeadow.app.beta": "Sunny Meadow",
}


class ActiveCatalogTests(unittest.TestCase):
    def test_exactly_four_active_apps(self):
        self.assertEqual(set(APP_IDS), {"kyro", "kyro-tvos", "zepzi", "sunnymeadow"})
        self.assertEqual(set(ACTIVE_BUNDLES), set(ACTIVE))
        for meta in APPS.values():
            self.assertEqual(meta["source_name"], ACTIVE[meta["bundle"]])

    def test_retired_bundles_are_not_active(self):
        self.assertEqual(
            RETIRED_BUNDLES,
            {"com.cubbiestream.kyro.labs", "com.cubbiestream.kyro.tvos.labs", "com.cubbiestream.kyrox"},
        )
        self.assertFalse(RETIRED_BUNDLES & ACTIVE_BUNDLES)
        self.assertFalse(set(RETIRED_APPS) & set(APPS))

    def test_committed_catalogs(self):
        src = json.loads((ROOT / "source.json").read_text())
        self.assertEqual({a["bundleIdentifier"] for a in src["apps"]}, set(ACTIVE))
        for app in src["apps"]:
            self.assertTrue(app["name"].startswith(ACTIVE[app["bundleIdentifier"]] + " — Build "))
            self.assertEqual(app["name"].rsplit(" ", 1)[1], str(app["versions"][0]["buildVersion"]))
        tv = json.loads((ROOT / "tvos-source.json").read_text())
        self.assertEqual([a["bundleIdentifier"] for a in tv["apps"]], ["com.cubbiestream.kyro.tvos"])

    def test_retired_listing_cannot_be_written_back(self):
        src = json.loads((ROOT / "source.json").read_text())
        src["apps"].append({"name": "Kyro X — Build 99", "bundleIdentifier": "com.cubbiestream.kyrox",
                            "versions": [{"version": "1.0", "buildVersion": "99",
                                          "downloadURL": "https://example.invalid/x.ipa", "size": 1}]})
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "source.json"
            path.write_text(json.dumps(src))
            v = subprocess.run([sys.executable, str(ROOT / "scripts" / "validate_source.py"), str(path)],
                               capture_output=True, text=True)
            self.assertNotEqual(v.returncode, 0)
            self.assertIn("retired listing", v.stdout + v.stderr)
            u = subprocess.run([sys.executable, str(ROOT / "scripts" / "update_source.py"), "--source",
                                str(path), "--refresh-listing-names"], capture_output=True, text=True)
            self.assertNotEqual(u.returncode, 0)
            r = subprocess.run([sys.executable, str(ROOT / "scripts" / "update_source.py"), "--source",
                                str(path), "--app", "kyrox", "--version", "1.0", "--build", "100",
                                "--size", "1", "--tag", "t", "--asset", "a.ipa"], capture_output=True, text=True)
            self.assertNotEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main()
