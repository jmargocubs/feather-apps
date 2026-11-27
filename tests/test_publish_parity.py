#!/usr/bin/env python3
"""Local and cloud publishing produce identical results (audit 2026-11-27).

Every publish path runs scripts/publish_ipa.py. These tests feed the same
synthetic IPA under the file names each environment produces (local package
scripts vs. cloud build artifacts) and check that the publish plan — tag,
release title/notes, asset name, download URL, catalog entries and listing
name — is identical, that nothing is uploaded without --approved, and that the
per-app version policy is enforced. No network, no gh, no builds.
"""
import json
import os
import pathlib
import plistlib
import stat
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from apps import APPS  # noqa: E402

# (app, version, build, local file name, cloud artifact file name)
CASES = [
    ("kyro", "1.0.140", "140", "Kyro-iOS-v1.0.140-Build140-Unsigned.ipa", "Kyro-1.0.140-140-ios-unsigned-arm64.ipa"),
    ("kyro-tvos", "1.0.109", "109", "Kyro-tvOS-v1.0.109-Build109-Unsigned.ipa", "Kyro-1.0.109-109-tvos-unsigned-arm64.ipa"),
    ("zepzi", "1.0.0", "20", "Zepzi-1.0.0-20.ipa", "Zepzi-v1.0.0-b20-unsigned.ipa"),
    ("sunnymeadow", "0.3.51", "51", "SunnyMeadow-v0.3.51-b51-beta-unsigned.ipa", "build/SunnyMeadow.ipa"),
]
EXPECTED_ASSET = {
    "kyro": "Kyro-iOS-v1.0.140-Build140-Unsigned.ipa",
    "kyro-tvos": "Kyro-tvOS-v1.0.109-Build109-Unsigned.ipa",
    "zepzi": "Zepzi-v1.0.0-b20-unsigned.ipa",
    "sunnymeadow": "SunnyMeadow-v0.3.51-b51-beta-unsigned.ipa",
}
EXPECTED_TAG = {
    "kyro": "kyro-ios-v1.0.140-build140-rc1",
    "kyro-tvos": "kyro-tvos-v1.0.109-build109-rc1",
    "zepzi": "zepzi-v1.0.0-b20",
    "sunnymeadow": "sunnymeadow-v0.3.51-b51",
}


def make_ipa(path: pathlib.Path, app: str, version: str, build: str) -> None:
    meta = APPS[app]
    path.parent.mkdir(parents=True, exist_ok=True)
    plist = {
        "CFBundleIdentifier": meta["bundle"],
        "CFBundleShortVersionString": version,
        "CFBundleVersion": build,
        "MinimumOSVersion": meta["min_os"],
        "CFBundleExecutable": "App",
    }
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("Payload/App.app/Info.plist", plistlib.dumps(plist))
        z.writestr("Payload/App.app/App", b"\0" * 64)


class PublishParityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = pathlib.Path(self.tmp.name)
        # A fake gh that records any call: plan-only runs must never invoke it.
        self.bin = self.dir / "bin"
        self.bin.mkdir()
        self.gh_log = self.dir / "gh-called"
        gh = self.bin / "gh"
        gh.write_text(f"#!/bin/sh\necho \"$@\" >> '{self.gh_log}'\nexit 1\n")
        gh.chmod(gh.stat().st_mode | stat.S_IEXEC)

    def tearDown(self):
        self.tmp.cleanup()

    def plan(self, ipa, app, version, build, *extra):
        env = dict(os.environ, PATH=f"{self.bin}{os.pathsep}{os.environ['PATH']}")
        r = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "publish_ipa.py"), str(ipa), "--app", app,
             "--version", version, "--build", build, "--source-commit", "0123456789abcdef0123456789abcdef01234567",
             "--notes", "Approved test notes", "--release-date", "2026-11-27", *extra],
            capture_output=True, text=True, env=env,
        )
        return r

    def test_local_and_cloud_file_names_give_identical_plans(self):
        for app, version, build, local_name, cloud_name in CASES:
            with self.subTest(app=app):
                local_ipa = self.dir / "local" / local_name
                cloud_ipa = self.dir / "cloud" / cloud_name
                make_ipa(local_ipa, app, version, build)
                make_ipa(cloud_ipa, app, version, build)
                plans = []
                for ipa in (local_ipa, cloud_ipa):
                    r = self.plan(ipa, app, version, build)
                    self.assertEqual(r.returncode, 3, r.stderr)  # not approved -> not published
                    self.assertIn("NOT PUBLISHED", r.stderr)
                    plans.append(json.loads(r.stdout))
                self.assertEqual(plans[0], plans[1])
                p = plans[0]
                meta = APPS[app]
                self.assertEqual(p["asset"], EXPECTED_ASSET[app])
                self.assertEqual(p["tag"], EXPECTED_TAG[app])
                self.assertEqual(p["release_repo"], meta["release_repo"])
                self.assertEqual(
                    p["download_url"],
                    f"https://github.com/{meta['release_repo']}/releases/download/{EXPECTED_TAG[app]}/{EXPECTED_ASSET[app]}",
                )
                self.assertEqual(p["title"], f"{meta['display_name']} {version} (Build {build}) Beta")
                self.assertIn(f"Catalog listing title: `{meta['source_name']} — Build {build}`", p["notes"])
                self.assertIn("Approved test notes", p["notes"])
                self.assertEqual(p["listing_name"], f"{meta['source_name']} — Build {build}")
                # Tag target only when the source repo is the release repo (Kyro).
                self.assertEqual(p["target"] is not None, meta["source_repo"] == meta["release_repo"])
                expected_catalogs = ["source.json"] + (["tvos-source.json"] if meta["update_tvos_source"] else [])
                self.assertEqual(sorted(p["catalog_preview"]), sorted(expected_catalogs))
                for entry in p["catalog_preview"].values():
                    self.assertEqual(entry["name"], f"{meta['source_name']} — Build {build}")
                    self.assertEqual(entry["bundleIdentifier"], meta["bundle"])
                    head = entry["head"]
                    self.assertEqual(
                        (head["version"], head["buildVersion"], head["downloadURL"], head["size"], head["minOSVersion"], head["date"]),
                        (version, build, p["download_url"], p["size"], meta["min_os"], "2026-11-27"),
                    )
        self.assertFalse(self.gh_log.exists(), "gh was called by a plan-only run")

    def test_dry_run_and_plan_only_never_publish(self):
        ipa = self.dir / "k.ipa"
        make_ipa(ipa, "kyro", "1.0.140", "140")
        r = self.plan(ipa, "kyro", "1.0.140", "140", "--dry-run")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse(self.gh_log.exists())

    def test_kyro_requires_aligned_marketing_version(self):
        ipa = self.dir / "k.ipa"
        make_ipa(ipa, "kyro", "1.0.0", "140")
        r = self.plan(ipa, "kyro", "1.0.0", "140")
        self.assertNotIn(r.returncode, (0, 3))
        self.assertIn("major.minor.140", r.stderr + r.stdout)

    def test_mismatched_ipa_metadata_is_refused(self):
        ipa = self.dir / "z.ipa"
        make_ipa(ipa, "zepzi", "1.0.0", "21")
        r = self.plan(ipa, "zepzi", "1.0.0", "20")
        self.assertNotIn(r.returncode, (0, 3))

    def test_retired_apps_cannot_be_published(self):
        ipa = self.dir / "x.ipa"
        make_ipa(ipa, "zepzi", "1.0.0", "20")
        r = self.plan(ipa, "kyrox", "1.0.0", "20")
        self.assertEqual(r.returncode, 2)  # argparse: not an allowed app


if __name__ == "__main__":
    unittest.main()
