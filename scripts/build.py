"""Build Dev5 payload and translation wrapper using local, untracked inputs."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / '.work'
OUTPUT = ROOT / 'output'
VERSION = '1.13-dev5'
RUNTIME_SHA256 = '75b95cc6b1aa567d8168dd02034af5d9bb7c8191fbe08144dfdda6ee79c65c41'

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=ROOT / 'config.json')
    parser.add_argument('--wrapper-only', action='store_true', help='Reuse an already built ARM32 payload')
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding='utf-8'))

    def path(value):
        p = Path(value)
        return p if p.is_absolute() else ROOT / p

    tools = path(config.get('tools_dir', 'tools'))
    base = path(config.get('base_apk', 'inputs/base.apk'))
    runtime_apk = path(config.get('runtime_apk', 'inputs/ZettaBridge-0.1.0.apk'))
    key = path(config.get('keystore', '.local/hatchimon-debug.jks'))
    java_bin = config.get('java_bin', '')

    def java_tool(name):
        if java_bin:
            return str(path(java_bin) / (name + ('.exe' if os.name == 'nt' else '')))
        found = shutil.which(name)
        if not found:
            raise RuntimeError(f'{name} is missing: configure java_bin or add a JDK to PATH')
        return found

    java, javac, keytool = [java_tool(n) for n in ['java', 'javac', 'keytool']]
    zig_value = config.get('zig', 'zig')
    zig = shutil.which(zig_value) or str(path(zig_value))
    for p in [base, runtime_apk, tools / 'apktool.jar', tools / 'r8.jar', tools / 'android.jar', tools / 'signer.jar']:
        if not p.is_file():
            raise RuntimeError(f'Missing build input: {p}')
    if hashlib.sha256(runtime_apk.read_bytes()).hexdigest() != RUNTIME_SHA256:
        raise RuntimeError('Runtime fingerprint mismatch: this workflow was tested with ZettaBridge 0.1.0')
    WORK.mkdir(exist_ok=True)
    OUTPUT.mkdir(exist_ok=True)
    os.environ['HATCHIMON_JAVA'] = java
    os.environ['HATCHIMON_TOOLS'] = str(tools)
    # Tests expect the same canonical, ignored input location.
    canonical = ROOT / 'inputs/base.apk'
    canonical.parent.mkdir(exist_ok=True)
    if base.resolve() != canonical.resolve():
        shutil.copy2(base, canonical)
    with zipfile.ZipFile(base) as archive:
        actual_engine = hashlib.sha256(archive.read('lib/armeabi/libMyGame.so')).hexdigest()
    expected_engine = json.loads((ROOT / 'evidence/engine-fingerprint.json').read_text())['sha256']
    if actual_engine != expected_engine:
        raise RuntimeError('Game engine fingerprint mismatch: native offsets and tests are specific to the analyzed 1.13 build')

    def run(*values):
        subprocess.run([str(v) for v in values], cwd=ROOT, check=True)

    def apktool(*values):
        run(java, '-jar', tools / 'apktool.jar', *values)

    def decode(apk, destination):
        if not (destination / 'apktool.yml').exists():
            apktool('d', apk, '-o', destination)

    def compile_java(name, sources, stubs):
        classes, dex = WORK / (name + '-classes'), WORK / (name + '-dex')
        classes.mkdir(exist_ok=True)
        dex.mkdir(exist_ok=True)
        run(javac, '-encoding', 'UTF-8', '-source', '8', '-target', '8', '-classpath', tools / 'android.jar', '-d', classes, *stubs, *sources)
        prefix = 'DevMenu' if name == 'menu' else 'HatchimonLaunchActivity'
        compiled = list(classes.rglob(prefix + '*.class'))
        run(java, '-cp', tools / 'r8.jar', 'com.android.tools.r8.D8', '--min-api', '14' if name == 'menu' else '26', '--lib', tools / 'android.jar', '--output', dex, *compiled)
        with zipfile.ZipFile(dex / 'classes.apk', 'w') as dst, zipfile.ZipFile(base) as src:
            dst.writestr('AndroidManifest.xml', src.read('AndroidManifest.xml'))
            dst.write(dex / 'classes.dex', 'classes.dex')
        decoded = WORK / (name + '-decoded')
        apktool('d', '-f', '-r', dex / 'classes.apk', '-o', decoded)
        return decoded / 'smali'

    def sign(unsigned, name):
        folder = OUTPUT / (name + '-signed')
        folder.mkdir(exist_ok=True)
        run(java, '-jar', tools / 'signer.jar', '--apks', unsigned, '--out', folder, '--ksDebug', key, '--allowResign')
        generated = folder / (unsigned.stem.removesuffix('-unsigned') + '-aligned-debugSigned.apk')
        destination = OUTPUT / (name + '.apk')
        shutil.copy2(generated, destination)
        return destination

    if not key.exists():
        key.parent.mkdir(parents=True, exist_ok=True)
        run(keytool, '-genkeypair', '-keystore', key, '-alias', 'androiddebugkey', '-keyalg', 'RSA', '-keysize', '2048', '-validity', '10000', '-storepass', 'android', '-keypass', 'android', '-dname', 'CN=Hatchimon Local Development')

    guest = WORK / 'guest-decoded'
    decode(base, guest)
    arm = ['cc', '-target', 'arm-linux-android', '-mcpu=arm926ej_s', '-mfloat-abi=soft', '-shared', '-fPIC', '-nostdlib', '-O2', '-Wl,--hash-style=both']
    payload = OUTPUT / 'Merge-Hatchimon-Dev5-ARM32.apk'
    if not args.wrapper_only:
        run(sys.executable, ROOT / 'scripts/patch_android16.py')
        run(zig, *arm, '-Wl,-soname,libdl.so', '-o', WORK / 'libdl.so', ROOT / 'src/native/dl-stub.c')
        run(zig, *arm, '-Wl,-soname,libHatchimonDev.so', '-L' + str(WORK), '-Wl,--no-as-needed', '-ldl', '-o', guest / 'lib/armeabi/libHatchimonDev.so', ROOT / 'src/native/bridge.c')
        smali = compile_java('menu', [ROOT / 'src/android/org/cocos2dx/cpp/DevMenu.java'], [ROOT / 'stubs/org/cocos2dx/lib/Cocos2dxActivity.java'])
        dest = guest / 'smali/org/cocos2dx/cpp'
        for p in (smali / 'org/cocos2dx/cpp').glob('DevMenu*.smali'):
            shutil.copy2(p, dest / p.name)
        activity = dest / 'AppActivity.smali'
        s = activity.read_text(encoding='utf-8')
        hook = 'invoke-static {p0}, Lorg/cocos2dx/cpp/DevMenu;->install(Lorg/cocos2dx/lib/Cocos2dxActivity;)V'
        if hook not in s:
            needle = 'invoke-super {p0, p1}, Lorg/cocos2dx/lib/Cocos2dxActivity;->onCreate(Landroid/os/Bundle;)V'
            if s.count(needle) != 1:
                raise RuntimeError('Cannot locate the expected AppActivity lifecycle hook')
            activity.write_text(s.replace(needle, needle + '\n\n    ' + hook, 1), encoding='utf-8')
        manifest = guest / 'AndroidManifest.xml'
        s = manifest.read_text(encoding='utf-8').replace('package="com.hyunmoo.hatchimon.farm"', 'package="com.hyunmoo.hatchimon.farm.dev"')
        s = s.replace('android:label="@string/app_name"', 'android:label="Merge Hatchimon Dev"')
        manifest.write_text(s, encoding='utf-8')
        yml = guest / 'apktool.yml'
        s = re.sub(r'versionName: .*', 'versionName: ' + VERSION, yml.read_text(encoding='utf-8'))
        s = s.replace('renameManifestPackage: null', 'renameManifestPackage: com.hyunmoo.hatchimon.farm.dev')
        yml.write_text(s, encoding='utf-8')
        for test in ['test_bridge.py', 'test_original_levels.py']:
            run(sys.executable, ROOT / 'tests' / test)
        apktool('b', guest, '-o', OUTPUT / 'guest-unsigned.apk')
        payload = sign(OUTPUT / 'guest-unsigned.apk', 'Merge-Hatchimon-Dev5-ARM32')
    if not payload.exists():
        raise RuntimeError('Build an ARM32 payload before using --wrapper-only')

    runtime = WORK / 'runtime-decoded'
    decode(runtime_apk, runtime)
    stubs = WORK / 'stubs/com/zettabridge/launcher'
    stubs.mkdir(parents=True, exist_ok=True)
    declarations = {
        'PluginRecord': 'class PluginRecord { String packageName,versionName; boolean hideAds,diagnostics; void save() throws java.io.IOException {} boolean isLaunchable(){return false;} String status(){return "stub";} }',
        'PluginStore': 'class PluginStore { static java.util.List<PluginRecord> list(android.content.Context c){return null;} static PluginRecord importApk(android.content.Context c,android.net.Uri u) throws java.io.IOException {return null;} }',
        'PluginSwitchActivity': 'class PluginSwitchActivity { static android.content.Intent intent(android.content.Context c,String n){return null;} }',
    }
    for name, declaration in declarations.items():
        (stubs / (name + '.java')).write_text('package com.zettabridge.launcher; ' + declaration, encoding='utf-8')
    smali = compile_java('launcher', [ROOT / 'src/android/com/zettabridge/launcher/HatchimonLaunchActivity.java'], list(stubs.glob('*.java')))
    for p in (smali / 'com/zettabridge/launcher').glob('HatchimonLaunchActivity*.smali'):
        shutil.copy2(p, runtime / 'smali/com/zettabridge/launcher' / p.name)
    guest_libs = runtime / 'assets/zb/guest/lib'
    for name, source in [('libOpenSLES.so', 'opensles-link-shim.c'), ('libGLESv1_CM.so', 'gles1-link-shim.c')]:
        run(zig, *arm, '-Wl,-soname,' + name, '-o', guest_libs / name, ROOT / 'src/native' / source)
    file_list = runtime / 'assets/zb-files.txt'
    s = file_list.read_text(encoding='utf-8')
    for name in ['libOpenSLES.so', 'libGLESv1_CM.so']:
        entry = 'zb/guest/lib/' + name
        if entry not in s.splitlines():
            s += entry + '\n'
    file_list.write_text(s, encoding='utf-8')
    (runtime / 'assets/zb-version.txt').write_text('hatchimon-dev5-zb0.1.0-linkshim1\n', encoding='utf-8')
    run(sys.executable, ROOT / 'tests/check_linkage.py')
    ET.register_namespace('android', 'http://schemas.android.com/apk/res/android')
    android = '{http://schemas.android.com/apk/res/android}'
    manifest = runtime / 'AndroidManifest.xml'
    tree = ET.fromstring(manifest.read_text(encoding='utf-8'))
    tree.set('package', 'com.hyunmoo.hatchimon.arm64.dev')
    app = tree.find('application')
    app.set(android + 'label', 'Merge Hatchimon Dev ARM64')
    app.set(android + 'extractNativeLibs', 'true')
    app.set(android + 'debuggable', 'true')
    seen = set()
    for element in list(app.findall('activity')):
        if element.find('intent-filter') is not None:
            element.set(android + 'name', 'com.zettabridge.launcher.HatchimonLaunchActivity')
            element.set(android + 'exported', 'true')
        name = element.get(android + 'name')
        if name in seen:
            app.remove(element)
            continue
        seen.add(name)
        affinity = element.get(android + 'taskAffinity', '')
        if affinity.startswith('com.zettabridge.launcher.'):
            element.set(android + 'taskAffinity', affinity.replace('com.zettabridge.launcher.', 'com.hyunmoo.hatchimon.arm64.dev.', 1))
    if 'com.zettabridge.launcher.LibraryActivity' not in seen:
        ET.SubElement(app, 'activity', {android + 'name': 'com.zettabridge.launcher.LibraryActivity', android + 'exported': 'false'})
    manifest.write_text(ET.tostring(tree, encoding='unicode'), encoding='utf-8')
    yml = runtime / 'apktool.yml'
    s = yml.read_text(encoding='utf-8').replace('renameManifestPackage: null', 'renameManifestPackage: com.hyunmoo.hatchimon.arm64.dev')
    yml.write_text(re.sub(r'versionName: .*', 'versionName: ' + VERSION + '-zb0.1.0', s), encoding='utf-8')
    bundled = runtime / 'assets/bundled'
    bundled.mkdir(exist_ok=True)
    shutil.copy2(payload, bundled / 'plugin.apk')
    notices = runtime / 'assets/licenses'
    notices.mkdir(exist_ok=True)
    for p in (ROOT / 'licenses').glob('*.txt'):
        shutil.copy2(p, notices / p.name)
    shutil.copy2(ROOT / 'THIRD_PARTY_NOTICES.md', notices / 'PROJECT-NOTICES.md')
    apktool('b', runtime, '-o', OUTPUT / 'arm64-wrapper-unsigned.apk')
    wrapper = sign(OUTPUT / 'arm64-wrapper-unsigned.apk', 'Merge-Hatchimon-Dev5-ARM64')
    # Verification expects a local copy of the upstream release as well.
    upstream = tools / 'ZettaBridge-0.1.0.apk'
    if runtime_apk.resolve() != upstream.resolve():
        shutil.copy2(runtime_apk, upstream)
    run(sys.executable, ROOT / 'tests/verify_apks.py')
    print('Built:', payload, wrapper, sep='\n')

if __name__ == '__main__':
    main()
