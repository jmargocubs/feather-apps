#!/usr/bin/env python3
"""Check every GitHub Actions publish path for the four active apps (read-only).

Fetches workflow files with `gh api` (no Actions runs) and asserts that each
path that can write the catalog: (1) is behind an explicit publish_approved gate,
(2) publishes only through feather-apps scripts/publish_ipa.py --approved, and
(3) has no bespoke tag / asset / catalog logic of its own.
"""
import base64
import json
import subprocess
import sys

PATHS = [
    # repo, ref, workflow file, app ids it may publish
    ("jmargocubs/Kyro", "kyro/m1-rebrand", ".github/workflows/publish-approved-ipa.yml", "kyro kyro-tvos"),
    ("jmargocubs/Kyro", "kyro/m1-rebrand", ".github/workflows/cloud-unsigned-ipa.yml", None),
    ("jmargocubs/flippy", "main", ".github/workflows/build-unsigned-ipa.yml", "zepzi"),
    ("jmargocubs/sunnyhill", "main", ".github/workflows/build-unsigned-ipa.yml", "sunnymeadow"),
    ("jmargocubs/sunnyhill", "feature/build-50-recovery-polish", ".github/workflows/build-unsigned-ipa.yml", "sunnymeadow"),
    ("jmargocubs/feather-apps", "main", ".github/workflows/publish-beta.yml", "any"),
]
FORBIDDEN = ["gh release create", "--asset-name", "visible-version", "json.dumps(data", "update_source.py --idempotent"]


def fetch(repo, ref, path):
    out = subprocess.run(["gh", "api", f"repos/{repo}/contents/{path}?ref={ref}"], capture_output=True, text=True)
    if out.returncode:
        raise SystemExit(f"cannot read {repo}@{ref}:{path}: {out.stderr.strip()}")
    return base64.b64decode(json.loads(out.stdout)["content"]).decode()


def main():
    failures = 0
    for repo, ref, path, apps in PATHS:
        text = fetch(repo, ref, path)
        checks = {"publish_approved gate": "publish_approved" in text}
        if apps:
            checks["calls publish_ipa.py --approved"] = "scripts/publish_ipa.py" in text and "--approved" in text
            checks["no bespoke release/catalog logic"] = not [f for f in FORBIDDEN if f in text]
            checks["no push-triggered publish"] = "inputs.publish_approved" in text or "display_title" in text
        else:
            checks["approval recorded for publisher"] = "publish_approved: $PUBLISH_APPROVED" in text and "[publish-approved]" in text
        ok = all(checks.values())
        failures += not ok
        print(("OK  " if ok else "FAIL") + f" {repo}@{ref} {path}")
        for name, passed in checks.items():
            if not passed:
                print(f"       ✗ {name}")
    print("all publish paths gated and shared" if not failures else f"{failures} path(s) need attention")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
