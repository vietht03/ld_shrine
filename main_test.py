#!/usr/bin/env python3
"""
Headless Automated Execution & Verification Script for Lair Defense: Shrine.

Runs a 60-FPS tick simulation for 15.0 seconds of game time (900 ticks).
Verifies all core game mechanics:
- Enemy spawning & path-following
- Tower targeting & projectile physics
- Status effects (Slow, DoT ticks)
- Dragon egg theft AI & path reversal
- Enemy death, gold rewards, egg dropping, and egg return queue
"""

from __future__ import annotations
import sys
from typing import Dict
from core.vec2 import Vec2
from core.game_manager import GameManager
from core.tower import FireDragon, IceDragon, PoisonDragon
from core.wave_spawner import WaveSpawner, WaveConfig


def run_simulation() -> bool:
    print("=" * 80)
    print("STARTING LAIR DEFENSE: SHRINE - HEADLESS SIMULATION (60 FPS, 15 SECONDS)")
    print("=" * 80)

    # Waypoints: Spawn -> Path -> Dragon Nest
    waypoints = [
        Vec2(50.0, 300.0),
        Vec2(200.0, 300.0),
        Vec2(350.0, 300.0),
        Vec2(500.0, 300.0),
        Vec2(650.0, 300.0)   # Dragon Nest position
    ]

    event_tracker: Dict[str, int] = {
        "enemy_spawn": 0,
        "tower_fire": 0,
        "status_applied": 0,
        "egg_stolen": 0,
        "enemy_slain": 0,
        "egg_dropped": 0,
        "egg_returned": 0
    }

    def simulation_logger(msg: str) -> None:
        print(msg)
        if "SPAWNED" in msg:
            event_tracker["enemy_spawn"] += 1
        elif "TOWER FIRED" in msg:
            event_tracker["tower_fire"] += 1
        elif "STATUS EFFECT" in msg:
            event_tracker["status_applied"] += 1
        elif "EGG STOLEN" in msg:
            event_tracker["egg_stolen"] += 1
        elif "ENEMY SLAIN" in msg:
            event_tracker["enemy_slain"] += 1
        elif "EGG DROPPED" in msg:
            event_tracker["egg_dropped"] += 1
        elif "EGG RETURNED" in msg:
            event_tracker["egg_returned"] += 1

    # Initialize GameManager with test wave setup
    game = GameManager(
        waypoints=waypoints,
        starting_eggs=5,
        starting_gold=500,
        logger=simulation_logger
    )

    # Configure wave stats to ensure enemies reach nest, steal egg, reverse, and get slain on return
    test_waves = [
        WaveConfig(
            enemy_count=3,
            spawn_interval=1.0,
            base_hp=240.0,        # Allows enemy to reach nest (x=650), then die to towers on return path
            base_speed=115.0,     # Reaches nest at ~5.2s, reverses path, dies on return at ~7.0s
            gold_reward=50,
            enemy_name="Swift Thief"
        )
    ]
    game.wave_spawner = WaveSpawner(test_waves, inter_wave_delay=1.0)
    game.wave_spawner.start()

    # Place defensive towers along path
    game.add_tower(FireDragon(tower_id=1, pos=Vec2(200.0, 360.0)))
    game.add_tower(IceDragon(tower_id=2, pos=Vec2(350.0, 360.0)))
    game.add_tower(PoisonDragon(tower_id=3, pos=Vec2(500.0, 360.0)))

    # Run 60 FPS headless simulation loop for 15.0 seconds (900 ticks)
    fps = 60
    dt = 1.0 / fps
    total_seconds = 15.0
    total_ticks = int(total_seconds * fps)

    print(f"\n--- Running {total_ticks} Ticks of Game Loop (dt = {dt:.4f}s) ---\n")

    for tick in range(total_ticks):
        game.update(dt)

    print("\n" + "=" * 80)
    print("SIMULATION SUMMARY & EVENT STATS:")
    print("=" * 80)
    for event, count in event_tracker.items():
        print(f" - {event.replace('_', ' ').title()}: {count} occurrences")

    print(f" - Final Gold: {game.gold}")
    print(f" - Final Player Eggs: {game.player_eggs}")
    print(f" - Final Nest Eggs: {game.nest_eggs}")
    print(f" - Remaining Active Enemies: {len(game.enemies)}")
    print(f" - Remaining Dropped Eggs: {len(game.dropped_eggs)}")
    print("=" * 80)

    # State Assertions
    assertions_passed = True

    if event_tracker["enemy_spawn"] == 0:
        print("FAIL ASSERTION: No enemies were spawned!")
        assertions_passed = False

    if event_tracker["tower_fire"] == 0:
        print("FAIL ASSERTION: Towers failed to target and fire projectiles!")
        assertions_passed = False

    if event_tracker["status_applied"] == 0:
        print("FAIL ASSERTION: No status effects (Slow/DoT) were applied!")
        assertions_passed = False

    if event_tracker["egg_stolen"] == 0:
        print("FAIL ASSERTION: Enemy failed to reach Dragon Nest and steal egg!")
        assertions_passed = False

    if event_tracker["enemy_slain"] == 0:
        print("FAIL ASSERTION: Enemies were not slain by towers!")
        assertions_passed = False

    if event_tracker["egg_dropped"] == 0:
        print("FAIL ASSERTION: Slain enemy did not drop stolen egg!")
        assertions_passed = False

    if event_tracker["egg_returned"] == 0:
        print("FAIL ASSERTION: Dropped egg timer queue did not return egg to nest!")
        assertions_passed = False

    if assertions_passed:
        print("\n[SIMULATION SUCCESSFUL]\n")
        return True
    else:
        print("\n[SIMULATION FAILED - ONE OR MORE ASSERTIONS FAILED]\n")
        return False


if __name__ == "__main__":
    success = run_simulation()
    sys.exit(0 if success else 1)
