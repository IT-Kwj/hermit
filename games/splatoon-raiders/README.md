# Splatoon Raiders

Title ID `0400380020056000`, update v65536. **nxnative reports it plays on an M4 Pro** (the opening, character creation, the first level's beach, inking and the first Salmonids, at 60 fps).

Built with [upstream nxnative](https://github.com/seedds/nxnative)'s own builder at the commit `game.json` names (fetched once into `./engines`), with Hermit's front end added (`tools/engine/patch.py`), so it plays like the Mario Kart World port:

- the game starts at once: no settings window first
- **key 1**: the performance overlay in the top right (compact FPS and resolution → detailed graph, GPU, frame time, CPU, memory → off)
- **key 2**: the settings nxnative's own launch window offers for this game, in the Mario Kart style; most apply at the next launch

| What | |
|---|---|
| Profile and notes | [nxnative `dm/games/0400380020056000`](https://github.com/seedds/nxnative/tree/ef8b25d2c5a8a37588ebc1bf1785a56468900688/dm/games/0400380020056000) |
| Dump folder | `base/` and `updates/65536/` (the update RomFS is 13 GB) |
| Shaders | about 27,000 |
| Verified by nxnative | on an M4 Pro: about 4.5 minutes in the last session with no crash; median frame 16.6-16.9 ms (60 fps), about 15 ms of GPU on the beach |
| Known | 16 GB Macs: memory grows past 14 GB and macOS starts swapping, down to about 1 fps (open, seedds/nxnative#1281). Turn MetalFX upscaling off if colours look washed out |

## Host mods

For the exact update `v65536` main build `663c2e087a083f05307f229dfc4042d5`, Hermit's `2` key settings panel has a **金手指** section:

- 无限墨水
- 快速射击
- 飞行 / 穿墙
- 任意地点游泳
- 武器切换, including **恢复原始武器**

These are host-side state hooks adapted from [kirakira-dev/OunceNative](https://github.com/kirakira-dev/OunceNative) at `c8785eb835a0` (MIT), not a generic Atmosphère `.txt`. Flight, swimming and weapon changes need the live player, camera and equipment objects, so a static cheat file cannot implement them reliably. The hooks verify the local player's object types before writing and do nothing if the build or one of the four observation gates does not match. The implementation and maintenance notes are in [`docs/splatoon-raiders-mods.md`](../../docs/splatoon-raiders-mods.md).

Use them only in offline single-player. Disable every row to restore normal movement and equipment behaviour. The launch switches `DM_RAIDERS_MODS=ink,rapid,fly,swim` and `DM_RAIDERS_WEAPON=<row name>` remain available for diagnosis.

## Shared shader list

[`shader_list.tsv`](shader_list.tsv): this game's own list of shaders and pipelines players have met, for this engine version only (its first line says which). It starts empty: when you close the game, the app offers to send what it built (every 100 new rows), as described in the main README's Contributing section.

## How it runs on players' Macs

[`reports.tsv`](reports.tsv): every report that names the Mac (nxnative's own playtests and GitHub issues), with the fps and memory where given, and whether it was fixed. Hermit has not test-built this game: what is known comes from these reports.

## Build

In the Hermit app: choose your dump folder on the **Builds** page and press **Build**. In Terminal:

```bash
./hermit.py build "<your dump folder>"
```

Then `./hermit.py install`. `refresh` and `run` are for Mario Kart World only.
