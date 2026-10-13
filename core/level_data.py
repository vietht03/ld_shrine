from __future__ import annotations
import os
import json
from dataclasses import dataclass
from typing import List, Dict, Any
from core.vec2 import Vec2
from core.wave_spawner import WaveConfig


@dataclass
class LevelConfig:
    """Configuration data for a single game level."""
    level_id: int
    name: str
    starting_gold: int
    starting_eggs: int
    waypoints: List[Vec2]
    pedestals: List[Vec2]
    waves: List[WaveConfig]


class ProgressManager:
    """
    Manages local JSON file persistence for unlocked levels,
    completed levels, and high scores.
    """

    FILE_PATH = "progress.json"

    @classmethod
    def load_progress(cls) -> Dict[str, Any]:
        """Loads progress dictionary from JSON file."""
        if os.path.exists(cls.FILE_PATH):
            try:
                with open(cls.FILE_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

        # Default initial progress
        return {
            "unlocked_level": 1,
            "completed_levels": [],
            "high_scores": {}
        }

    @classmethod
    def save_progress(cls, unlocked_level: int, level_id: int, score: int) -> None:
        """Saves unlocked level progression and score."""
        progress = cls.load_progress()

        if unlocked_level > progress.get("unlocked_level", 1):
            progress["unlocked_level"] = min(10, unlocked_level)

        completed = set(progress.get("completed_levels", []))
        completed.add(level_id)
        progress["completed_levels"] = list(completed)

        high_scores = progress.get("high_scores", {})
        prev_score = high_scores.get(str(level_id), 0)
        if score > prev_score:
            high_scores[str(level_id)] = score
        progress["high_scores"] = high_scores

        try:
            with open(cls.FILE_PATH, "w", encoding="utf-8") as f:
                json.dump(progress, f, indent=2)
        except Exception:
            pass

    @classmethod
    def unlock_next_level(cls, current_level_id: int, score: int = 0) -> None:
        """Unlocks the next level upon completing the current one."""
        next_lvl = min(10, current_level_id + 1)
        cls.save_progress(unlocked_level=next_lvl, level_id=current_level_id, score=score)


# Helper wave generators
def _make_waves(wave_count: int, base_hp: float, base_speed: float) -> List[WaveConfig]:
    waves = []
    enemy_names = ["Goblin Scout", "Thief Raider", "Armored Bandit", "Dragon Slayer", "Shadow Assassin", "Dragon Boss"]
    for i in range(wave_count):
        count = 3 + i
        hp = base_hp * (1.18 ** i)
        speed = min(120.0, base_speed + i * 4.0)
        gold = 25 + i * 5
        name = enemy_names[min(i, len(enemy_names) - 1)]
        waves.append(
            WaveConfig(
                enemy_count=count,
                spawn_interval=max(0.8, 1.8 - i * 0.1),
                base_hp=hp,
                base_speed=speed,
                gold_reward=gold,
                enemy_name=f"{name} (W{i+1})"
            )
        )
    return waves


def get_level_data(level_id: int) -> LevelConfig:
    """Returns custom configuration data for levels 1 through 10."""
    levels: Dict[int, LevelConfig] = {}

    # --- LEVEL 1: Shrine Entrance (Easy) ---
    levels[1] = LevelConfig(
        level_id=1,
        name="1: Shrine Entrance",
        starting_gold=400,
        starting_eggs=5,
        waypoints=[
            Vec2(50, 350),
            Vec2(300, 350),
            Vec2(600, 350),
            Vec2(900, 350)
        ],
        pedestals=[
            Vec2(200, 430),
            Vec2(450, 270),
            Vec2(700, 430)
        ],
        waves=_make_waves(3, base_hp=65.0, base_speed=40.0)
    )

    # --- LEVEL 2: Whispering Canyon ---
    levels[2] = LevelConfig(
        level_id=2,
        name="2: Whispering Canyon",
        starting_gold=360,
        starting_eggs=5,
        waypoints=[
            Vec2(50, 480),
            Vec2(300, 480),
            Vec2(300, 220),
            Vec2(650, 220),
            Vec2(650, 480),
            Vec2(900, 480)
        ],
        pedestals=[
            Vec2(180, 400),
            Vec2(380, 350),
            Vec2(550, 300),
            Vec2(750, 400)
        ],
        waves=_make_waves(4, base_hp=80.0, base_speed=44.0)
    )

    # --- LEVEL 3: Emerald Pass ---
    levels[3] = LevelConfig(
        level_id=3,
        name="3: Emerald Pass",
        starting_gold=340,
        starting_eggs=5,
        waypoints=[
            Vec2(50, 200),
            Vec2(350, 200),
            Vec2(350, 520),
            Vec2(700, 520),
            Vec2(700, 350),
            Vec2(900, 350)
        ],
        pedestals=[
            Vec2(220, 280),
            Vec2(430, 360),
            Vec2(600, 440),
            Vec2(780, 270)
        ],
        waves=_make_waves(4, base_hp=95.0, base_speed=46.0)
    )

    # --- LEVEL 4: Magma Valley ---
    levels[4] = LevelConfig(
        level_id=4,
        name="4: Magma Valley",
        starting_gold=320,
        starting_eggs=5,
        waypoints=[
            Vec2(50, 550),
            Vec2(250, 550),
            Vec2(250, 200),
            Vec2(550, 200),
            Vec2(550, 550),
            Vec2(800, 550),
            Vec2(900, 350)
        ],
        pedestals=[
            Vec2(150, 460),
            Vec2(350, 350),
            Vec2(450, 350),
            Vec2(680, 460),
            Vec2(800, 270)
        ],
        waves=_make_waves(5, base_hp=110.0, base_speed=50.0)
    )

    # --- LEVEL 5: Frozen Ridge ---
    levels[5] = LevelConfig(
        level_id=5,
        name="5: Frozen Ridge",
        starting_gold=300,
        starting_eggs=5,
        waypoints=[
            Vec2(50, 350),
            Vec2(200, 350),
            Vec2(200, 550),
            Vec2(600, 550),
            Vec2(600, 180),
            Vec2(800, 180),
            Vec2(900, 350)
        ],
        pedestals=[
            Vec2(120, 430),
            Vec2(350, 470),
            Vec2(480, 470),
            Vec2(510, 260),
            Vec2(720, 260)
        ],
        waves=_make_waves(6, base_hp=125.0, base_speed=54.0)
    )

    # --- LEVEL 6: Shadow Gorge ---
    levels[6] = LevelConfig(
        level_id=6,
        name="6: Shadow Gorge",
        starting_gold=280,
        starting_eggs=5,
        waypoints=[
            Vec2(50, 180),
            Vec2(250, 180),
            Vec2(250, 480),
            Vec2(500, 480),
            Vec2(500, 180),
            Vec2(750, 180),
            Vec2(750, 480),
            Vec2(900, 350)
        ],
        pedestals=[
            Vec2(150, 260),
            Vec2(350, 380),
            Vec2(400, 260),
            Vec2(600, 380),
            Vec2(650, 260),
            Vec2(820, 400)
        ],
        waves=_make_waves(6, base_hp=140.0, base_speed=58.0)
    )

    # --- LEVEL 7: Thunder Summit ---
    levels[7] = LevelConfig(
        level_id=7,
        name="7: Thunder Summit",
        starting_gold=270,
        starting_eggs=5,
        waypoints=[
            Vec2(50, 520),
            Vec2(400, 520),
            Vec2(400, 180),
            Vec2(700, 180),
            Vec2(700, 400),
            Vec2(900, 400)
        ],
        pedestals=[
            Vec2(220, 440),
            Vec2(310, 320),
            Vec2(500, 260),
            Vec2(600, 260),
            Vec2(610, 480),
            Vec2(800, 320)
        ],
        waves=_make_waves(7, base_hp=160.0, base_speed=62.0)
    )

    # --- LEVEL 8: Inferno Cavern ---
    levels[8] = LevelConfig(
        level_id=8,
        name="8: Inferno Cavern",
        starting_gold=260,
        starting_eggs=5,
        waypoints=[
            Vec2(50, 250),
            Vec2(200, 250),
            Vec2(200, 500),
            Vec2(450, 500),
            Vec2(450, 200),
            Vec2(700, 200),
            Vec2(700, 500),
            Vec2(900, 350)
        ],
        pedestals=[
            Vec2(120, 330),
            Vec2(320, 420),
            Vec2(360, 280),
            Vec2(580, 280),
            Vec2(600, 420),
            Vec2(780, 420),
            Vec2(820, 260)
        ],
        waves=_make_waves(8, base_hp=180.0, base_speed=66.0)
    )

    # --- LEVEL 9: Abyssal Shrine ---
    levels[9] = LevelConfig(
        level_id=9,
        name="9: Abyssal Shrine",
        starting_gold=250,
        starting_eggs=5,
        waypoints=[
            Vec2(50, 500),
            Vec2(300, 500),
            Vec2(300, 200),
            Vec2(600, 200),
            Vec2(600, 500),
            Vec2(800, 500),
            Vec2(900, 350)
        ],
        pedestals=[
            Vec2(180, 420),
            Vec2(220, 280),
            Vec2(450, 270),
            Vec2(500, 420),
            Vec2(680, 420),
            Vec2(720, 280),
            Vec2(830, 430)
        ],
        waves=_make_waves(9, base_hp=200.0, base_speed=70.0)
    )

    # --- LEVEL 10: Dragon Sanctuary (Boss Level) ---
    levels[10] = LevelConfig(
        level_id=10,
        name="10: Dragon Sanctuary",
        starting_gold=240,
        starting_eggs=5,
        waypoints=[
            Vec2(50, 350),
            Vec2(200, 350),
            Vec2(200, 550),
            Vec2(500, 550),
            Vec2(500, 180),
            Vec2(750, 180),
            Vec2(750, 450),
            Vec2(900, 350)
        ],
        pedestals=[
            Vec2(120, 430),
            Vec2(350, 470),
            Vec2(400, 350),
            Vec2(400, 260),
            Vec2(620, 260),
            Vec2(650, 380),
            Vec2(820, 510),
            Vec2(830, 270)
        ],
        waves=_make_waves(10, base_hp=230.0, base_speed=75.0)
    )

    return levels.get(level_id, levels[1])
