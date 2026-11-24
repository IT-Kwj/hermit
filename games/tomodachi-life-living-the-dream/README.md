# Tomodachi Life: Living the Dream

Title ID `010051F0207B2000`. A **Switch** game: built from your own copy's `.xci` / `.nsp` files with your own `prod.keys` (see [LEGAL.md](../../LEGAL.md)). Version 1.0.0.

Built with [MacNativeGames](https://github.com/ly05010419/MacNativeGames) by ly05010419 (MIT): its [`games/tomodachi`](https://github.com/ly05010419/MacNativeGames/tree/036267eb21fab75b6e32b558cc64f91f3167b0b3/games/tomodachi) port, at the commit `game.json` names, run through that port's own builder as its README describes. Community port, experimental. Base game 1.0.0 (`.nsp` or `.xci`) and your firmware for the system fonts. The app reads the game's data from its build's work folder, so keep that folder after building (Hermit points the app at it, so the app can still be moved to Applications). It has its own runtime, so Hermit's overlay and key-2 settings are not added. Needs Homebrew's `python@3.14`. **Not built through Hermit yet.**

## Build

In the Hermit app: **+ Build game**, choose the game's file, then your `prod.keys`. In Terminal:

```bash
./hermit.py build "<the game's .xci or .nsp, or its folder>" --keys <path of prod.keys>
```

Add `--firmware <your unpacked firmware dump>` for the Switch's system fonts.

## How it runs on players' Macs

[`reports.tsv`](reports.tsv): every report that names the Mac. Tell others how it ran with the [How it ran](https://github.com/azmasm/hermit/issues/new?template=how-it-ran.yml) form.
