from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Optional
from core.vec2 import Vec2
from core.enemy import Enemy
from core.projectile import Projectile


class DragonTower(ABC):
    """
    Abstract base class for all Dragon Towers.
    Handles targeting, cooldown management, level upgrades, and selling.
    """

    def __init__(
        self,
        tower_id: int,
        name: str,
        pos: Vec2,
        cost: int,
        attack_range: float,
        fire_interval: float
    ) -> None:
        self.id = tower_id
        self.name = name
        self.pos = pos
        self.cost = cost
        self.base_cost = cost
        self.attack_range = attack_range
        self.fire_interval = fire_interval  # Seconds between shots
        self.cooldown_timer: float = 0.0
        self.target_enemy: Optional[Enemy] = None
        self.level: int = 1
        self.max_level: int = 3

    @property
    def upgrade_cost(self) -> int:
        """Gold cost to upgrade to the next level."""
        return int(self.base_cost * 0.8 * self.level)

    @property
    def sell_value(self) -> int:
        """Gold refund value when selling this tower."""
        return int((self.base_cost + (self.level - 1) * self.upgrade_cost) * 0.7)

    def upgrade(self) -> bool:
        """Upgrades tower stats if below max level."""
        if self.level >= self.max_level:
            return False

        self.level += 1
        self.attack_range *= 1.12
        self.fire_interval *= 0.88  # Fires 12% faster
        return True

    def update(self, dt: float, enemies: List[Enemy]) -> Optional[Projectile]:
        """
        Updates tower cooldown and scans for enemies.
        Returns a fired Projectile instance if ready to attack.
        """
        if self.cooldown_timer > 0:
            self.cooldown_timer -= dt

        # Acquire target if current target is invalid or out of range
        self.target_enemy = self._select_target(enemies)

        if self.target_enemy and self.cooldown_timer <= 0:
            self.cooldown_timer = self.fire_interval
            return self.fire(self.target_enemy)

        return None

    def _select_target(self, enemies: List[Enemy]) -> Optional[Enemy]:
        """
        Selects target enemy within range.
        Prioritizes enemies carrying an egg, or furthest along distance_traveled.
        """
        valid_targets = [
            e for e in enemies
            if e.is_alive and self.pos.distance_to(e.pos) <= self.attack_range
        ]
        if not valid_targets:
            return None

        # Sort: priority to enemies with egg, then furthest traveled
        valid_targets.sort(
            key=lambda e: (e.has_egg, e.follower.distance_traveled),
            reverse=True
        )
        return valid_targets[0]

    @abstractmethod
    def fire(self, target: Enemy) -> Projectile:
        """Constructs and returns specialized Projectile instance."""
        pass


class FireDragon(DragonTower):
    """Fire Dragon tower that deals Area of Effect (AoE) physical damage."""

    def __init__(self, tower_id: int, pos: Vec2) -> None:
        super().__init__(
            tower_id=tower_id,
            name="Fire Dragon",
            pos=pos,
            cost=100,
            attack_range=150.0,
            fire_interval=1.2
        )
        self.damage = 35.0
        self.aoe_radius = 60.0
        self.projectile_speed = 350.0

    def upgrade(self) -> bool:
        if super().upgrade():
            self.damage *= 1.4
            self.aoe_radius *= 1.15
            return True
        return False

    def fire(self, target: Enemy) -> Projectile:
        return Projectile(
            start_pos=self.pos,
            target_enemy=target,
            speed=self.projectile_speed,
            damage=self.damage,
            effect_type="fire",
            aoe_radius=self.aoe_radius
        )


class IceDragon(DragonTower):
    """Ice Dragon tower that deals single-target damage and applies Slow status."""

    def __init__(self, tower_id: int, pos: Vec2) -> None:
        super().__init__(
            tower_id=tower_id,
            name="Ice Dragon",
            pos=pos,
            cost=120,
            attack_range=140.0,
            fire_interval=1.0
        )
        self.damage = 18.0
        self.slow_factor = 0.45    # 45% speed reduction
        self.slow_duration = 2.5   # 2.5 seconds duration
        self.projectile_speed = 400.0

    def upgrade(self) -> bool:
        if super().upgrade():
            self.damage *= 1.35
            self.slow_factor = min(0.70, self.slow_factor + 0.10)
            self.slow_duration += 0.5
            return True
        return False

    def fire(self, target: Enemy) -> Projectile:
        return Projectile(
            start_pos=self.pos,
            target_enemy=target,
            speed=self.projectile_speed,
            damage=self.damage,
            effect_type="ice",
            slow_factor=self.slow_factor,
            slow_duration=self.slow_duration
        )


class PoisonDragon(DragonTower):
    """Poison Dragon tower that inflicts Damage over Time (DoT) status."""

    def __init__(self, tower_id: int, pos: Vec2) -> None:
        super().__init__(
            tower_id=tower_id,
            name="Poison Dragon",
            pos=pos,
            cost=130,
            attack_range=130.0,
            fire_interval=0.9
        )
        self.impact_damage = 10.0
        self.dot_damage = 8.0     # 8 damage per tick
        self.dot_interval = 0.5   # every 0.5s
        self.dot_duration = 3.0   # for 3.0s total
        self.projectile_speed = 320.0

    def upgrade(self) -> bool:
        if super().upgrade():
            self.impact_damage *= 1.3
            self.dot_damage *= 1.4
            self.dot_duration += 0.75
            return True
        return False

    def fire(self, target: Enemy) -> Projectile:
        return Projectile(
            start_pos=self.pos,
            target_enemy=target,
            speed=self.projectile_speed,
            damage=self.impact_damage,
            effect_type="poison",
            dot_damage=self.dot_damage,
            dot_interval=self.dot_interval,
            dot_duration=self.dot_duration
        )
