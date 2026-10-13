# Lair Defense: Shrine - 2D Tower Defense Engine & State Architecture

A modular, performant, clean Object-Oriented Python 2D Tower Defense game engine inspired by *"Lair Defense: Shrine"*.

Built with Python `arcade` featuring a complete **Scene/State Management Architecture**, **10 Progressive Levels**, and local **JSON Progress Persistence**.

---

## Project Structure

```
ld_shrine/
├── core/
│   ├── __init__.py          # Core package exports
│   ├── vec2.py              # 2D mathematical vector utility
│   ├── status_effects.py    # StatusEffectManager (Slow, DoT, Freeze)
│   ├── enemy.py             # Enemy AI, WaypointFollower & Egg Theft path-reversal
│   ├── projectile.py        # Projectile physics & payload delivery
│   ├── tower.py             # DragonTower ABC (Fire, Ice, Poison) & Upgrades
│   ├── wave_spawner.py      # WaveSpawner & HP scaling per wave
│   ├── game_manager.py      # Central GameManager engine orchestrator
│   └── level_data.py        # 10 Level configurations & ProgressManager JSON
├── gui/
│   ├── __init__.py          # GUI package exports
│   ├── game_view.py         # Gameplay View renderer
│   └── game_views.py        # MainMenuView, LevelSelectView, GameplayView & Modals
├── main.py                  # Main Arcade game launcher
├── main_test.py             # 60-FPS Headless simulation test runner
├── progress.json            # Local level progression & high score save file
└── README.md                # Project documentation
```

---

## Features & Scene Architecture

1. **Main Menu Scene (`MainMenuView`):**
   - Title Header *"LAIR DEFENSE: SHRINE"*.
   - Glowing Dragon Shrine emblem graphic element.
   - Interactive **PLAY** button (transitions to Level Select) and **QUIT** button.

2. **Level Select Scene (`LevelSelectView`):**
   - Grid layout featuring **10 Progressive Levels**.
   - **Level 1** is unlocked by default. **Levels 2 to 10** unlock progressively upon completing the preceding stage.
   - Saves level completion badges and high scores locally in `progress.json`.
   - Hover and click visual responses, plus a **BACK TO MAIN MENU** button.

3. **Gameplay Scene (`GameplayView`):**
   - Loads specific waypoint paths, pedestal layouts, starting gold/eggs, and wave configs for the selected level.
   - **Top Header Status Bar**: Live Gold, Eggs, Wave, Score, and **PAUSE** button.
   - **Dragon Spells Panel**: Fire Rain `[Q]`, Ice Freeze `[W]`, Poison Storm `[E]` with visual cooldown masks.
   - **Fixed Dragon Pedestals**: Click pedestals to open Build Ring / Upgrade & Sell radial menus.
   - **Clean Range Circles**: Displays range circles on hover/selection only.

4. **Overlays & Modals:**
   - **Pause Modal**: Resume, Restart, Level Select buttons.
   - **Victory Modal**: Unlocks next level, displays Gold & High Score, Next Level button.
   - **Game Over Modal**: Displays Defeat text, Retry Level button.

---

## 10 Progressive Levels

- **Levels 1–3 (Tutorial/Easy)**: 3-4 waves, basic thieves, slow speeds, high starting gold (340–400g).
- **Levels 4–7 (Medium)**: 5-7 waves, faster thieves, lower starting gold (270–320g), complex S-curves & zig-zags.
- **Levels 8–10 (Hard/Boss)**: 8-10 waves, high-speed egg thieves, heavy tank bosses, 7-8 dragon pedestals.

---

## How to Run

### 1. Launch Main Arcade Game (GUI & Scene Manager)
```bash
python3 main.py
```

### 2. Run Headless Simulation Test Suite
```bash
python3 main_test.py
```
