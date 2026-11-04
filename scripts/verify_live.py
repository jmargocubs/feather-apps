#!/usr/bin/env python3
import argparse, json, urllib.request, sys, time
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--url",default="https://jmargocubs.github.io/feather-apps/source.json")
    ap.add_argument("--app",required=True)
    ap.add_argument("--bundle",required=True)
    ap.add_argument("--version",required=True)
    ap.add_argument("--build",required=True)
    ap.add_argument("--size",type=int,required=True)
    ap.add_argument("--ipa-url",required=True)
    args=ap.parse_args()
    for attempt in range(5):
        try:
            d=json.load(urllib.request.urlopen(args.url))
            break
        except Exception as e:
            if attempt==4: raise
            time.sleep(5)
    app=None
    for a in d["apps"]:
        if a["bundleIdentifier"]==args.bundle:
            app=a
    assert app is not None, "app not found"
    v=app["versions"][0]
    assert v["version"]==args.version, f"version {v['version']}"
    assert v["buildVersion"]==args.build, f"build {v['buildVersion']}"
    assert v["downloadURL"]==args.ipa_url, f"url {v['downloadURL']}"
    assert v["size"]==args.size, f"size {v['size']}"
    # check ipa reachable
    req=urllib.request.urlopen(args.ipa_url)
    assert req.status in (200,302), f"ipa status {req.status}"
    print("live verification OK")
if __name__=="__main__":
    main()
