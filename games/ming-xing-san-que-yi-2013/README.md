# 明星三缺一 2013

Title ID `01004D4A53510000`. A **Switch** game: built from your own copy's `.xci` / `.nsp` files with your own `prod.keys` (see [LEGAL.md](../../LEGAL.md)). Version 1.0.0.

Built with [MacNativeGames](https://github.com/ly05010419/MacNativeGames) by ly05010419 (MIT): its [`games/mj2013`](https://github.com/ly05010419/MacNativeGames/tree/17416fee1a8ab3e74042fb15cbca765cda609d88/games/mj2013) port, at the commit `game.json` names, run through that port's own builder as its README describes. Early. The base game (`.nsp`). It draws in software (no GPU shaders); the mouse is the touch screen. It has its own runtime, so Hermit's overlay and key-2 settings are not added. Needs Homebrew's `python@3.14`. **Not built through Hermit yet.**

## Build

In the Hermit app: **+ Build game**, choose the game's file, then your `prod.keys`. In Terminal:

```bash
./hermit.py build "<the game's .xci or .nsp, or its folder>" --keys <path of prod.keys>
```

## How it runs on players' Macs

[`reports.tsv`](reports.tsv): every report that names the Mac. Tell others how it ran with the [How it ran](https://github.com/azmasm/hermit/issues/new?template=how-it-ran.yml) form.
