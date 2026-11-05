#!/usr/bin/env python3
import zipfile, plistlib, sys, hashlib, os, argparse

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("ipa")
    ap.add_argument("--bundle",default=None)
    ap.add_argument("--version",default=None)
    ap.add_argument("--build",default=None)
    ap.add_argument("--minos",default=None)
    args=ap.parse_args()
    ipa=args.ipa
    if not os.path.isfile(ipa):
        print("IPA not found"); sys.exit(1)
    z=zipfile.ZipFile(ipa)
    apps=[n for n in z.namelist() if n.endswith(".app/Info.plist") and "/PlugIns/" not in n and n.count("/")<=3]
    if not apps:
        print("No app Info.plist"); sys.exit(1)
    plist=plistlib.loads(z.read(apps[0]))
    bid=plist.get("CFBundleIdentifier"); ver=plist.get("CFBundleShortVersionString"); build=plist.get("CFBundleVersion"); minos=plist.get("MinimumOSVersion")
    if args.bundle and bid!=args.bundle: print("bundle mismatch",bid,args.bundle); sys.exit(1)
    if args.version and ver!=args.version: print("version mismatch",ver,args.version); sys.exit(1)
    if args.build and str(build)!=str(args.build): print("build mismatch",build,args.build); sys.exit(1)
    if args.minos and minos!=args.minos: print("minOS mismatch",minos,args.minos); sys.exit(1)
    print("bundle:",bid); print("version:",ver); print("build:",build); print("minOS:",minos)
    print("size:",os.path.getsize(ipa))
    print("sha256:",hashlib.sha256(open(ipa,'rb').read()).hexdigest())
    profiles=[n for n in z.namelist() if n.endswith(".mobileprovision")]
    if profiles: print("WARNING: embedded provisioning profiles:",profiles)
    print("OK")

if __name__=="__main__":
    main()
