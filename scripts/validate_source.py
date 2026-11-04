#!/usr/bin/env python3
import json, sys, os

def main(path):
    with open(path) as f:
        data = json.load(f)
    assert "apps" in data and isinstance(data["apps"], list)
    ids = set()
    for app in data["apps"]:
        bid = app["bundleIdentifier"]
        assert bid not in ids, f"duplicate bundle id {bid}"
        ids.add(bid)
        for v in app.get("versions", []):
            assert "version" in v and "buildVersion" in v
            assert str(v.get("downloadURL","")).startswith("https://")
            assert v.get("size",0) > 0
    print("source valid:", len(data["apps"]), "apps")
    print("OK")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv)>1 else "source.json")
