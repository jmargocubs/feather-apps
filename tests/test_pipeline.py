import json, subprocess, sys, os, tempfile, shutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)
r=run([sys.executable, os.path.join(ROOT,"scripts","validate_source.py"), os.path.join(ROOT,"source.json")])
assert r.returncode==0, r.stderr
ipa=os.environ.get("KYRO_IPA")
if ipa and os.path.isfile(ipa):
    r=run([sys.executable, os.path.join(ROOT,"scripts","scan_ipa.py"), ipa])
    assert r.returncode==0, r.stderr
    r=run([sys.executable, os.path.join(ROOT,"scripts","validate_ipa.py"), ipa, "--bundle","com.cubbiestream.kyro","--version","1.0.0","--build","22","--minos","18.0"])
    assert r.returncode==0, r.stderr
# duplicate rejection
tmp=tempfile.mkdtemp()
shutil.copy(os.path.join(ROOT,"source.json"), os.path.join(tmp,"source.json"))
subprocess.run([sys.executable, os.path.join(ROOT,"scripts","update_source.py"),"--source",os.path.join(tmp,"source.json"),"--app","kyro","--version","9.9.9","--build","999","--size","100","--tag","kyro-v9.9.9-b999","--asset","x.ipa"],check=True)
r=subprocess.run([sys.executable, os.path.join(ROOT,"scripts","update_source.py"),"--source",os.path.join(tmp,"source.json"),"--app","kyro","--version","9.9.9","--build","999","--size","100","--tag","kyro-v9.9.9-b999","--asset","x.ipa"],capture_output=True,text=True)
assert r.returncode!=0, "duplicate not rejected"
# date check
d=json.load(open(os.path.join(tmp,"source.json")))
versions=[v for a in d["apps"] if a["bundleIdentifier"]=="com.cubbiestream.kyro" for v in a["versions"] if v["version"]=="9.9.9"]
from datetime import date
assert versions and versions[0]["date"] == date.today().isoformat(), "date should be today"
print("tests passed")
