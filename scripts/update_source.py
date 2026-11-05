#!/usr/bin/env python3
import argparse, json, sys
from datetime import date

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source",default="source.json")
    ap.add_argument("--app",required=True,choices=("kyro", "zepzi"))
    ap.add_argument("--version",required=True)
    ap.add_argument("--build",required=True)
    ap.add_argument("--size",type=int,required=True)
    ap.add_argument("--tag",required=True)
    ap.add_argument("--asset",required=True)
    ap.add_argument("--idempotent",action="store_true")
    ap.add_argument("--date",default=date.today().isoformat())
    args=ap.parse_args()

    d=json.load(open(args.source))
    bid="com.cubbiestream.kyro" if args.app=="kyro" else "app.flippy.reader"
    app=None
    for a in d["apps"]:
        if a["bundleIdentifier"]==bid:
            app=a
    if app is None:
        print("app not found"); sys.exit(1)

    expected_url=f"https://github.com/jmargocubs/feather-apps/releases/download/{args.tag}/{args.asset}"
    for v in app.get("versions",[]):
        if v.get("version")==args.version and v.get("buildVersion")==args.build:
            expected={
                "version":args.version,
                "buildVersion":args.build,
                "downloadURL":expected_url,
                "size":args.size,
                "minOSVersion":"18.0",
                "date":args.date,
            }
            if (args.idempotent and all(v.get(k)==value for k,value in expected.items())
                    and app.get("size")==args.size):
                print("source entry already matches", args.app, args.version, args.build)
                return
            if args.idempotent:
                print("existing source entry does not match expected release")
                sys.exit(1)
            print("duplicate version/build"); sys.exit(1)
    entry={
        "version":args.version,
        "buildVersion":args.build,
        "date":args.date,
        "downloadURL":expected_url,
        "size":args.size,
        "minOSVersion":"18.0"
    }
    app.setdefault("versions",[]).insert(0,entry)
    app["size"]=args.size
    json.dump(d,open(args.source,"w"),indent=2)
    print("updated", args.app, args.version, args.build)

if __name__=="__main__":
    main()
