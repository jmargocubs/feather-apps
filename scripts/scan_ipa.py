#!/usr/bin/env python3
import zipfile, sys, re, os
PATTERNS = [r"AKIA[0-9A-Z]{16}", r"ghp_[A-Za-z0-9]{36}", r"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+"]
def main(ipa):
    z=zipfile.ZipFile(ipa)
    hits=0
    for n in z.namelist():
        if n.endswith(".mobileprovision"):
            print("FAIL: embedded provisioning profile", n); hits+=1
    for n in z.namelist():
        try:
            data=z.read(n)
        except Exception:
            continue
        text=data.decode("latin-1")
        for p in PATTERNS:
            if re.search(p,text):
                print("FAIL: secret pattern in",n); hits+=1
    if hits:
        sys.exit(1)
    print("scan OK")
if __name__=="__main__":
    import glob
    for ipa in (sys.argv[1:] or glob.glob("*.ipa")):
        main(ipa)
