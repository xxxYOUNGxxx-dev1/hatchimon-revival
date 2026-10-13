# Third-party notices and license scope

Hatchimon Revival is an unofficial enthusiast preservation and compatibility project. It is not affiliated with the original developer or ZettaBridge authors.

## Original game

Merge Hatchimon 1.13, by Hyunmoo, retains its original engine, assets, and in-game copyright notices. The title screen identifies the 2017-era game. Original game material is not covered by this repository's MIT license, and this project does not claim ownership of it. Release APKs contain the game; repository source files cover the additions and tooling, not the original game's missing source project.

## Translation runtime

ZettaBridge 0.1.0: https://github.com/ZailoxTT/ZettaBridge

The runtime has cumulative PolyForm Noncommercial 1.0.0 and PolyForm Perimeter 1.0.1 terms, including restrictions on competing products. Read the complete [upstream license](licenses/ZettaBridge.txt), not an MIT label, before redistributing or modifying the runtime. This fan game wrapper uses its unchanged translator binary; it is not a new general-purpose translator implementation.

Upstream component notices are retained separately in [ZettaBridge third-party notices](licenses/ZettaBridge-THIRD-PARTY.txt). Runtime dependencies retain their own licenses. The tested release embeds the upstream license and third-party notices under `assets/licenses/`.

## Khronos interface constants

The OpenSL shim contains constants derived from Android's OpenSLES interface-ID source. Copyright (c) 2007–2009 The Khronos Group Inc. The full permission and warranty notice remains in `src/native/opensles-link-shim.c` and `licenses/Khronos-OpenSL.txt`.

## Build and analysis tools

Apktool, Android SDK/R8, Zig, Uber APK Signer, pyelftools, Capstone, and Unicorn are external tools, not bundled repository binaries. Obtain them from their upstream projects under their respective licenses.
