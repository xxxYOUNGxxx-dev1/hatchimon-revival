# Contributing

Useful contributions include device compatibility reports, reproducible crash fixes, translation, tests, and improvements to the build workflow.

For bugs, include the release version, Android/API version, model, ABI, page size, steps, and the smallest redacted log excerpt showing the failure. Keep signing keys, saves, account data, and full bugreports private.

Read [architecture](docs/ARCHITECTURE.md) before changing native offsets or JNI behavior. Run the affected tests and explain device coverage separately from static checks. Preserve original copyright notices and distinguish project-owned code from the game and runtime.

Open an issue to discuss broader scope changes. Pull requests should explain the observed problem, resulting behavior, validation, and remaining limits. Do not claim a native ARM64 port or unlimited monster ranks without implementing and validating them.
