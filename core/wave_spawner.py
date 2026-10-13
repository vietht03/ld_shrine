from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional
from core.vec2 import Vec2
from core.enemy import Enemy


@dataclass
class WaveConfig:
    """Configuration for a single wave of enemies."""
    enemy_count: int
    spawn_interval: float
    base_hp: float
    base_speed: float
    gold_reward: int
    enemy_name: str = "Goblin Thief"


class WaveSpawner:
    """
    Manages timed enemy spawns, wave progress, and health scaling across waves.
    """

    def __init__(self, waves: List[WaveConfig], inter_wave_delay: float = 3.0) -> None:
        self.waves = waves
        self.inter_wave_delay = inter_wave_delay

        self.current_wave_index: int = 0
        self.enemies_spawned_in_wave: int = 0
        self.spawn_timer: float = 0.0
        self.wave_delay_timer: float = 0.0
        self.is_wave_active: bool = False
        self.is_finished: bool = False
        self.total_enemies_spawned: int = 0

    def start(self) -> None:
        """Starts the first wave."""
        if self.waves:
            self.is_wave_active = True
            self.spawn_timer = 0.0

    def update(self, dt: float, waypoints: List[Vec2]) -> Optional[Enemy]:
        """
        Updates spawner timer and returns spawned Enemy if ready.
        """
        if self.is_finished or not self.waves:
            return None

        current_config = self.waves[self.current_wave_index]

        if not self.is_wave_active:
            # Waiting for inter-wave delay
            self.wave_delay_timer -= dt
            if self.wave_delay_timer <= 0:
                self.is_wave_active = True
                self.spawn_timer = 0.0
            return None

        # Wave is active
        self.spawn_timer += dt
        if self.spawn_timer >= current_config.spawn_interval:
            self.spawn_timer = 0.0
            return self._spawn_enemy(current_config, waypoints)

        return None

    def _spawn_enemy(self, config: WaveConfig, waypoints: List[Vec2]) -> Enemy:
        """Helper to instantiate a scaled enemy."""
        self.enemies_spawned_in_wave += 1
        self.total_enemies_spawned += 1

        # Scale HP based on wave index (15% per wave), with a higher base HP floor to match the slower, longer survival gameplay loop.
        hp_scaling = 1.15 ** self.current_wave_index
        scaled_hp = config.base_hp * hp_scaling * 2.0

        enemy_name = config.enemy_name.lower()
        if "thief" in enemy_name or "rogue" in enemy_name:
            enemy_type = "thief"
        elif "knight" in enemy_name or "armored" in enemy_name:
            enemy_type = "knight"
        elif "mage" in enemy_name or "priest" in enemy_name or "wizard" in enemy_name:
            enemy_type = "mage"
        elif "boss" in enemy_name or "king" in enemy_name:
            enemy_type = "boss"
        elif "peasant" in enemy_name or "peasant" in enemy_name:
            enemy_type = "peasant"
        else:
            enemy_type = "footman"

        enemy = Enemy(
            enemy_id=self.total_enemies_spawned,
            name=f"{config.enemy_name} #{self.total_enemies_spawned}",
            start_pos=waypoints[0],
            waypoints=waypoints,
            hp=scaled_hp,
            base_speed=config.base_speed,
            gold_reward=config.gold_reward,
            enemy_type=enemy_type
        )

        # Check if wave spawning completed
        if self.enemies_spawned_in_wave >= config.enemy_count:
            self.is_wave_active = False
            self.enemies_spawned_in_wave = 0
            if self.current_wave_index + 1 < len(self.waves):
                self.current_wave_index += 1
                self.wave_delay_timer = self.inter_wave_delay
            else:
                self.is_finished = True

        return enemy
