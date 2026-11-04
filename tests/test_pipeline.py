import json, subprocess, sys, os, tempfile, shutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)
# validate source
r=run([sys.executable, os.path.join(ROOT,"scripts","validate_source.py"), os.path.join(ROOT,"source.json")])
assert r.returncode==0, r.stderr
# scan kyro ipa
ipa="/Users/paolazanetti/.t3/scratch/kyro-silo/artifacts/kyro-b22/Kyro-Build22-Stabilization-Unsigned.ipa"
r=run([sys.executable, os.path.join(ROOT,"scripts","scan_ipa.py"), ipa])
assert r.returncode==0, r.stderr
# duplicate version rejection test
tmp=tempfile.mkdtemp()
shutil.copy(os.path.join(ROOT,"source.json"), os.path.join(tmp,"source.json"))
# inject duplicate by running update_source twice
subprocess.run([sys.executable, os.path.join(ROOT,"scripts","update_source.py"),"--source",os.path.join(tmp,"source.json"),"--app","kyro","--version","9.9.9","--build","999","--size","100","--tag","kyro-v9.9.9-b999","--asset","x.ipa"],check=True)
r=subprocess.run([sys.executable, os.path.join(ROOT,"scripts","update_source.py"),"--source",os.path.join(tmp,"source.json"),"--app","kyro","--version","9.9.9","--build","999","--size","100","--tag","kyro-v9.9.9-b999","--asset","x.ipa"],capture_output=True,text=True)
assert r.returncode!=0, "duplicate not rejected"
print("tests passed")
