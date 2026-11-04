#!/usr/bin/env python3
import argparse, json, re, sys

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source",default="source.json")
    ap.add_argument("--app",required=True)
    ap.add_argument("--version",required=True)
    ap.add_argument("--build",required=True)
    ap.add_argument("--size",type=int,required=True)
    ap.add_argument("--tag",required=True)
    ap.add_argument("--asset",required=True)
    args=ap.parse_args()

    d=json.load(open(args.source))
    bid="com.cubbiestream.kyro" if args.app=="kyro" else "app.flippy.reader"
    app=None
    for a in d["apps"]:
        if a["bundleIdentifier"]==bid:
            app=a
    if app is None:
        print("app not found"); sys.exit(1)

    url=f"https://github.com/jmargocubs/feather-apps/releases/download/{args.tag}/{args.asset}"
    for v in app.get("versions",[]):
        if v.get("version")==args.version and v.get("buildVersion")==args.build:
            print("duplicate version/build"); sys.exit(1)
    entry={
        "version":args.version,
        "buildVersion":args.build,
        "date":"2026-11-04",
        "downloadURL":url,
        "size":args.size,
        "minOSVersion":"18.0"
    }
    app.setdefault("versions",[]).insert(0,entry)
    app["size"]=args.size
    json.dump(d,open(args.source,"w"),indent=2)
    print("updated", args.app, args.version, args.build)

if __name__=="__main__":
    main()
