# Building Dev5

This workflow targets the inspected Merge Hatchimon 1.13 engine only. Native offsets are tied to its fingerprint; a different game binary must be analyzed again.

## Dependencies

- Python 3.10+ and `pip install -r requirements.txt`
- A JDK with `java`, `javac`, and `keytool` (Java 17 works)
- Zig 0.13.0
- Apktool 2.9.3 as `tools/apktool.jar`
- Android D8/R8 as `tools/r8.jar`, Android API 25 `android.jar` as `tools/android.jar`
- Uber APK Signer 1.3.0 as `tools/signer.jar`
- The inspected input APK as `inputs/base.apk`
- [ZettaBridge v0.1.0](https://github.com/ZailoxTT/ZettaBridge/releases/tag/v0.1.0) APK as `inputs/ZettaBridge-0.1.0.apk`

Download tools from their upstream projects; tool binaries and SDK files are not committed. See [research references](RESEARCH.md). The build validates the runtime and engine fingerprints before modifying files.

## Configure and build

Copy `config.example.json` to `config.json`. Relative paths resolve from the repository root. Set `java_bin` to a JDK's `bin` directory if Java is not on PATH; set `zig` to an executable path if needed.

```sh
python -m pip install -r requirements.txt
python scripts/build.py
```

The script decodes both APKs, applies Android compatibility patches, compiles the developer menu and native bridge, checks the native functions, signs the ARM32 payload, embeds it in the ARM64 wrapper, and verifies the result. Outputs are `output/Merge-Hatchimon-Dev5-ARM32.apk` and `output/Merge-Hatchimon-Dev5-ARM64.apk`.

Generated files are under `.work/` and `output/`. Delete `.work/` when changing input APKs or runtime versions. `--wrapper-only` reuses an existing ARM32 payload.

The first build creates an ignored local development key. Keep this key private and backed up: Android requires the same key for an in-place upgrade. A new local key cannot update the published APK directly. Export progress before replacing an installation. This is a reproducible build *workflow*, not a claim of byte-identical APKs: signing keys, ZIP timestamps, and tool versions affect the output hash.

## Install and diagnose

Use [Android platform-tools](https://developer.android.com/tools/releases/platform-tools), enable USB debugging, and authorize your computer on the phone.

```sh
adb devices
python scripts/adb.py --serial YOUR_DEVICE install output/Merge-Hatchimon-Dev5-ARM64.apk
python scripts/adb.py --serial YOUR_DEVICE launch
python scripts/adb.py --serial YOUR_DEVICE capture
```

Capture writes logs, a screenshot, and a bugreport under ignored `device-debug/`. These can contain personal data: inspect and redact them before sharing. Capture does not clear logcat or app data. Installation uses `adb install -r` and never uninstalls the game automatically.
