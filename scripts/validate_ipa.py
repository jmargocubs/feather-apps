#!/usr/bin/env python3
import zipfile, plistlib, sys, hashlib, os

def main(ipa):
    if not os.path.isfile(ipa):
        print("IPA not found"); sys.exit(1)
    z = zipfile.ZipFile(ipa)
    apps = [n for n in z.namelist() if n.endswith(".app/Info.plist") and "/PlugIns/" not in n and n.count("/") <= 3]
    if not apps:
        print("No app Info.plist found"); sys.exit(1)
    plist = plistlib.loads(z.read(apps[0]))
    print("bundle:", plist.get("CFBundleIdentifier"))
    print("version:", plist.get("CFBundleShortVersionString"))
    print("build:", plist.get("CFBundleVersion"))
    print("minOS:", plist.get("MinimumOSVersion"))
    print("size:", os.path.getsize(ipa))
    print("sha256:", hashlib.sha256(open(ipa,'rb').read()).hexdigest())
    # check no provisioning profile
    profiles = [n for n in z.namelist() if n.endswith(".mobileprovision")]
    if profiles:
        print("WARNING: embedded provisioning profiles:", profiles)
    print("OK")

if __name__ == "__main__":
    main(sys.argv[1])
