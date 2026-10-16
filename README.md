# SHADOW LEGENDS: NEON WAR — VIP 3D Edition

**Created by Chishti Bro Computers & Developers | Founder: Moinuddin Chishti**

A Python/Panda3D third-person neon-city action game. The city, buildings, road grid, player, hover vehicle, enemies, pickups and weapon effects are generated from Panda3D primitives, so the source project does not depend on missing external art files.

## Implemented gameplay

- Procedurally generated neon city with colored tower accents and fog/lighting.
- Third-person camera and WASD movement with mouse heading control.
- Plasma shooting with three weapon profiles (keys `1`, `2`, `3`), ammo and reload (`R`).
- Enemy chase/attack AI, damage, kills, score, credits, XP and level progression.
- Titan Sentinel boss that appears after four eliminations, with a large health pool.
- Health, armor and ammo supply drops; press `F` nearby to collect.
- Dash (`Q`), sprint (`Shift`) and a nearby hover vehicle (`V`).
- Pause (`Esc`), restart, mission objective, HUD and local high-score/progress file.
- GitHub Actions workflow for a Windows folder build packaged as a ZIP artifact.

## Controls

- `W A S D` — move
- Mouse — turn/aim horizontally
- Left mouse button or `Space` — fire
- `1`, `2`, `3` — select weapon profile
- `R` — refill plasma ammo
- `Shift` — sprint
- `Q` — dash
- `V` — enter/exit the hover vehicle when nearby
- `F` — collect a nearby supply drop
- Mouse wheel — camera zoom
- `Esc` — pause/resume

## Run locally

Python 3.11 is recommended.

```bash
python -m pip install -r requirements.txt
python shadow_legends_neon_war.py
```

## Build on GitHub from mobile

1. Upload the project files to the repository root, preserving `.github/workflows/main.yml` and the `tests/` folder.
2. The main file must be named exactly `shadow_legends_neon_war.py`.
3. Commit to `main` or `master`, or run the workflow manually from the **Actions** tab.
4. Download the `Shadow-Legends-Neon-War-Windows` artifact after the workflow succeeds. It contains the packaged Windows build ZIP; extract it and run `ShadowLegendsNeonWar.exe` from its folder.

## Validation status

The Python source is syntax-checked and the repository includes dependency-free structural tests that run in GitHub Actions before packaging. The actual Panda3D window/gameplay and packaged Windows executable still need to be run on a compatible machine; this workspace does not have Panda3D installed and cannot perform that visual runtime test here. The game is designed as a procedural 3D prototype, not a photorealistic AAA asset-heavy production.
