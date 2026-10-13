# Compatibility and limits

| Item | Status |
|---|---|
| Host installation ABI | ARM64 only |
| Original game engine | ARM32, translated |
| Android minimum | Host manifest targets Android 8+; not tested across all versions |
| Device tested | Android 16 / API 36, model 26077PC53G, ARM64 only |
| Test device page size | 4 KiB |
| Runtime ELF alignment | 16 KiB aligned; a 16 KiB device was not tested |
| Menu language | Russian in the tested APK |
| Game language | Original English assets |
| Monster rank range | 1–72 |
| Purchases and network services | Not tested; legacy services may be unavailable |

The first real-device launch crashed because an old Unity Ads connectivity thread called a restricted telephony API without catching `SecurityException`. The patch returns `NETWORK_TYPE_UNKNOWN` when access is denied, rather than requesting extra phone permissions.

The old Vungle internal receiver now uses `RECEIVER_NOT_EXPORTED` on API 33+. The host manifest also prevents duplicate launcher activity declarations after repeated rebuilds.

The final cold-launch process showed no fatal error or Vungle receiver registration error in the captured observation. This establishes a successful tested session, not stability on every phone or an exhaustive playthrough. Translation adds startup time and may affect performance. Sound engine activity was seen in logs; audible output was not assessed.
