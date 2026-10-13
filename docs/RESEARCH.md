# Research and upstream references

Repository presentation follows the clear overview, installation, build, contribution, and licensing sections used by mature Android tooling projects. Their prose and branding were not copied.

## Tools used

- [Apktool](https://github.com/iBotPeaches/Apktool): resource/Smali decode and rebuild. It does not recover original native C++ source.
- [JADX](https://github.com/skylot/jadx): Android Java/DEX analysis reference.
- [Uber APK Signer](https://github.com/patrickfav/uber-apk-signer): alignment, signing, and verification.
- [Zig](https://github.com/ziglang/zig): ARM32 native cross-compilation.
- [pyelftools](https://github.com/eliben/pyelftools), [Capstone](https://github.com/capstone-engine/capstone), and [Unicorn](https://github.com/unicorn-engine/unicorn): ELF analysis, disassembly, and isolated native execution tests.
- [ZettaBridge](https://github.com/ZailoxTT/ZettaBridge), [v0.1.0](https://github.com/ZailoxTT/ZettaBridge/releases/tag/v0.1.0): the upstream ARM32-on-ARM64 runtime used in the release.
- [Android platform-tools](https://developer.android.com/tools/releases/platform-tools): ADB installation, logcat, bugreport, and device verification.
- [Android OpenSL interface IDs](https://android.googlesource.com/platform/frameworks/wilhelm/+/refs/heads/master/src/OpenSLES_IID.cpp): interface constants with retained Khronos copyright.

## MCP and skill references investigated

- [Apktool MCP](https://github.com/zinja-coder/apktool-mcp-server)
- [JADX headless MCP](https://github.com/1013503897/jadx-headless-mcp)
- [GhidraMCP](https://github.com/LaurieWired/GhidraMCP)
- [APK workflow skill](https://github.com/4thel00z/apktool-skill/blob/master/SKILL.md)
- [Cocos2d native dependencies](https://github.com/cocos2d/cocos2d-x-3rd-party-libs-src)
- [32matrix](https://github.com/Chucny/32matrix)

The MCP analysis servers and APK skill were investigated as references, not installed or used as the execution backend. Existing CLI tools and Python libraries performed the work. Building Cocos2d dependencies cannot replace the missing game's C++ source; a genuine native ARM64 port still needs that source or a compatible original ARM64 engine.
