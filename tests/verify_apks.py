"""Verify actual packaged ABI, unchanged engine/assets, payload, DEX and signature."""
from pathlib import Path
import zipfile, io, sys, hashlib, json, subprocess
ROOT=Path(__file__).resolve().parents[1]
TOOLS=Path(__import__('os').environ.get('HATCHIMON_TOOLS', str(ROOT/'tools')))

from elftools.elf.elffile import ELFFile
JAVA=Path(__import__('os').environ.get('HATCHIMON_JAVA', 'java'))
base=Path(str(ROOT/'inputs/base.apk'))
payload=ROOT/'output/Merge-Hatchimon-Dev5-ARM32.apk'
wrapper=ROOT/'output/Merge-Hatchimon-Dev5-ARM64.apk'
runtime=TOOLS/'ZettaBridge-0.1.0.apk'
checks=[]
def ok(value,label):
    assert value,label
    checks.append(label)
def sha(b):return hashlib.sha256(b).hexdigest()
with zipfile.ZipFile(base) as original,zipfile.ZipFile(payload) as guest:
    ok(guest.testzip() is None,'guest ZIP CRC')
    ok(len(guest.namelist())==len(set(guest.namelist())),'guest unique ZIP entries')
    assets=[n for n in original.namelist() if n.startswith('assets/') and not n.endswith('/')]
    ok(all(original.read(n)==guest.read(n) for n in assets),'all original game assets unchanged')
    ok(original.read('lib/armeabi/libMyGame.so')==guest.read('lib/armeabi/libMyGame.so'),'original game engine unchanged')
    elf=ELFFile(io.BytesIO(guest.read('lib/armeabi/libHatchimonDev.so')))
    ok(elf.elfclass==32 and elf.header['e_machine']=='EM_ARM','guest bridge is real ARM32 ELF')
    ok(b'Lorg/cocos2dx/cpp/DevMenu;' in guest.read('classes.dex'),'guest menu packaged')
with zipfile.ZipFile(wrapper) as host,zipfile.ZipFile(runtime) as upstream:
    ok(host.testzip() is None,'wrapper ZIP CRC')
    ok(len(host.namelist())==len(set(host.namelist())),'wrapper unique ZIP entries')
    libs=[n for n in host.namelist() if n.startswith('lib/') and n.endswith('.so')]
    ok(libs==['lib/arm64-v8a/libzbridge.so'],'outer APK has only ARM64 installation ABI')
    elf=ELFFile(io.BytesIO(host.read(libs[0])))
    ok(elf.elfclass==64 and elf.header['e_machine']=='EM_AARCH64','translator is real AArch64 ELF')
    ok(all(s['p_align']>=16384 for s in elf.iter_segments() if s['p_type']=='PT_LOAD'),'translator ELF load segments support 16 KiB alignment')
    ok(host.read(libs[0])==upstream.read(libs[0]),'translator binary unchanged from upstream release')
    system=[n for n in upstream.namelist() if n.startswith('assets/zb/') and not n.endswith('/')]
    ok(all(host.read(n)==upstream.read(n) for n in system),'upstream guest sysroot and proxy unchanged')
    ok(sha(host.read('assets/bundled/plugin.apk'))==sha(payload.read_bytes()),'bundled payload matches signed patched game')
    dex=host.read('classes.dex')
    ok(b'Lcom/zettabridge/launcher/HatchimonLaunchActivity;' in dex,'custom launcher packaged')
    ok(b'Compile-only stub' not in dex,'no Cocos compile stub packaged')
    ok(any(n in host.namelist() for n in ['assets/licenses/ZettaBridge.txt','assets/licenses/ZettaBridge-LICENSE.txt']),'translator license packaged')
for apk in [payload,wrapper]:
    process=subprocess.run([str(JAVA),'-jar',str(TOOLS/'signer.jar'),'--apks',str(apk),'--onlyVerify'],capture_output=True,text=True)
    (ROOT/'output'/(apk.stem+'-signature.txt')).write_text(process.stdout+process.stderr,encoding='utf-8')
    ok(process.returncode==0,'signature/alignment verification: '+apk.name)
result={'checks':checks,'original':{'path':str(base),'sha256':sha(base.read_bytes())},
        'artifacts':[{'path':str(p),'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size} for p in [payload,wrapper]],
        'game_assets_preserved':len(assets),'wrapper_kind':'ARM64 host translating an unchanged ARM32 game engine',
        'device_runtime_test':'NOT RUN: no connected Android device',
        'spawn_levels':'1..72 (24 tiers x 3 forms); 37..72 use original glow behavior',
        'maximum_grant':1000000000,'maximum_balance':2000000000}
device_record=ROOT/'evidence/local-device-verification.json'
if device_record.exists():
    device=json.loads(device_record.read_text(encoding='utf-8'))
    if device.get('installed_apk_sha256')==sha(wrapper.read_bytes()):
        result['device_runtime_test']=device
(ROOT/'output/verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
