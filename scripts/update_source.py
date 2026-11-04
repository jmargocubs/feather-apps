#!/usr/bin/env python3
import argparse, json, os
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--app",required=True)
    ap.add_argument("--version",required=True)
    ap.add_argument("--build",required=True)
    ap.add_argument("--size",type=int,required=True)
    ap.add_argument("--sha",required=True)
    ap.add_argument("--tag",required=True)
    args=ap.parse_args()
    src="source.json"
    d=json.load(open(src))
    bid = "com.cubbiestream.kyro" if args.app=="kyro" else "app.flippy.reader"
    app=None
    for a in d["apps"]:
        if a["bundleIdentifier"]==bid:
            app=a
    if app is None:
        print("app not found"); raise SystemExit(1)
    url=f"https://github.com/jmargocubs/feather-apps/releases/download/{args.tag}/"
    # find ipa filename from rc? Use tag-based placeholder; operator must set exact filename
    print("update_source: update downloadURL manually to exact asset name")
    json.dump(d,open(src,"w"),indent=2)
if __name__=="__main__":
    main()
