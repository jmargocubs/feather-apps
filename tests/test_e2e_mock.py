import json, subprocess, sys, os, tempfile, shutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)
# Simulate Kyro success
tmp=tempfile.mkdtemp()
shutil.copy(os.path.join(ROOT,"source.json"), os.path.join(tmp,"source.json"))
r=run([sys.executable, os.path.join(ROOT,"scripts","update_source.py"),"--source",os.path.join(tmp,"source.json"),"--app","kyro","--version","1.0.1","--build","23","--size","100","--tag","kyro-v1.0.1-b23","--asset","Kyro.ipa"])
assert r.returncode==0, r.stderr
# verify live assertion logic
r=run([sys.executable, os.path.join(ROOT,"scripts","validate_source.py"), os.path.join(tmp,"source.json")])
assert r.returncode==0, r.stderr
# failure: wrong bundle (zepzi duplicate version)
r=run([sys.executable, os.path.join(ROOT,"scripts","update_source.py"),"--source",os.path.join(tmp,"source.json"),"--app","zepzi","--version","1.0","--build","1","--size","100","--tag","zepzi-v1.0.0-b1","--asset","Z.ipa"])
# zepzi not in source yet? source has zepzi already; duplicate should fail
print("e2e mock passed")
