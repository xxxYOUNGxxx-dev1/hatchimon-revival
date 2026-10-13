# Validation

The published Dev5 ARM64 APK is the exact binary installed and exercised on the test phone. Its SHA-256 is recorded in [release evidence](../evidence/release-verification.json).

## Automated checks

- 455 native bridge cases under Unicorn: input bounds, currency saturation, scene guards, capacity, and spawn arguments.
- 288 checks against the original ARM32 engine covering level/type combinations, IDs, composition behavior, and sprite selection.
- ELF linkage checks for the translated guest's imports.
- Package verification: ZIP integrity, ABI, runtime identity, unchanged original engine and all 358 original game assets, embedded signed payload, menu/launcher classes, signatures, and alignment.
- Public CI checks patch idempotence and Android API branching using small synthetic Smali fixtures. Native/APK checks run locally because original input binaries are not checked into Git.

Native tests validate specific calls and assets; they do not simulate an entire Android device.

## Device observations

Android 16 / API 36, ARM64-only model 26077PC53G, 4 KiB pages:

1. Cold launch, title screen, farm, tutorial, ordinary hatching, and evolution.
2. Grants of 1,000,000,000 gold, Cash, and rubies; repeated gold grant capped at 2,000,000,000.
3. Rank 37 and rank 72 spawning with original glow sprites.
4. Battle with extended-rank monsters and return to the farm.
5. Save persistence after force-stop/relaunch and Dev4 → Dev5 upgrade/reimport.
6. Foreground/background resume.

![Verified farm and balances](images/dev-farm.png)

![Battle with extended ranks](images/battle.png)

Full bugreports, phone identifiers, private preferences, and signing credentials are excluded from the repository. The published evidence is a sanitized summary. No listening test, purchase test, every-map playthrough, prolonged stress test, or 16 KiB-device test was performed.
