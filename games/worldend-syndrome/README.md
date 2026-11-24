# WORLDEND SYNDROME

Title ID `010048900CF64000`. A **Switch** game: built from your own copy's `.xci` / `.nsp` files with your own `prod.keys` (see [LEGAL.md](../../LEGAL.md)). Version 1.0.0.

Built with [MacNativeGames](https://github.com/ly05010419/MacNativeGames) by ly05010419 (MIT): its [`games/worldend`](https://github.com/ly05010419/MacNativeGames/tree/51202d4e1887f51e2e5c6631271240d9efc80487/games/worldend) port, at the commit `game.json` names, run through that port's own builder as its README describes. Community port, experimental. Base game 1.0.0 (`.nsp` or `.xci`) only. Its builder fetches the tools it needs (.NET, SPIRV-Cross, zstd, LibHac, libvpx) and needs Xcode with the macOS 26 SDK or later. It has its own runtime, so Hermit's overlay and key-2 settings are not added. Needs Homebrew's `python@3.14`. **Not built through Hermit yet.**

## Build

In the Hermit app: **+ Build game**, choose the game's file, then your `prod.keys`. In Terminal:

```bash
./hermit.py build "<the game's .xci or .nsp, or its folder>" --keys <path of prod.keys>
```

## How it runs on players' Macs

[`reports.tsv`](reports.tsv): every report that names the Mac. Tell others how it ran with the [How it ran](https://github.com/azmasm/hermit/issues/new?template=how-it-ran.yml) form.
