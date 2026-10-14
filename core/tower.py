from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Optional
from core.vec2 import Vec2
from core.enemy import Enemy
from core.projectile import Projectile


class DragonTower(ABC):
    """
    Abstract base class for all Dragon Towers.
    Supports 3 levels of upgrades using Gold + Ruby.
    Each level unlocks enhanced abilities.
    """

    def __init__(
        self,
        tower_id: int,
        name: str,
        pos: Vec2,
        gold_cost: int,
        ruby_cost: int,
        attack_range: float,
        fire_interval: float
    ) -> None:
        self.id = tower_id
        self.name = name
        self.pos = pos

        # Dual currency cost system
        self.gold_cost = gold_cost
        self.ruby_cost = ruby_cost          # Ruby required to PLACE this tower
        self.base_gold_cost = gold_cost
        self.base_ruby_cost = ruby_cost

        self.attack_range = attack_range
        self.fire_interval = fire_interval
        self.cooldown_timer: float = 0.0
        self.target_enemy: Optional[Enemy] = None
        self.level: int = 1
        self.max_level: int = 6
        self.silence_timer: float = 0.0

    # ------------------------------------------------------------------
    # Economy
    # ------------------------------------------------------------------
    @property
    def upgrade_gold_cost(self) -> int:
        return int(self.base_gold_cost * 0.85 * self.level)

    @property
    def upgrade_ruby_cost(self) -> int:
        return int(self.base_ruby_cost * 0.5 * self.level)

    @property
    def sell_gold(self) -> int:
        return int(self.base_gold_cost * 0.6)

    @property
    def sell_ruby(self) -> int:
        return int(self.base_ruby_cost * 0.4)

    # ------------------------------------------------------------------
    # Upgrade
    # ------------------------------------------------------------------
    def upgrade(self) -> bool:
        if self.level >= self.max_level:
            return False
        self.level += 1
        self.attack_range *= 1.13
        self.fire_interval *= 0.87
        self._on_upgrade()
        return True

    def _on_upgrade(self) -> None:
        """Called after each level-up. Override to apply per-tower bonuses."""
        pass

    # ------------------------------------------------------------------
    # Update / Target / Fire
    # ------------------------------------------------------------------
    def update(self, dt: float, enemies: List[Enemy]) -> Optional[Projectile]:
        if self.silence_timer > 0:
            self.silence_timer = max(0.0, self.silence_timer - dt)
            return None
        if self.cooldown_timer > 0:
            self.cooldown_timer -= dt
        self.target_enemy = self._select_target(enemies)
        if self.target_enemy and self.cooldown_timer <= 0:
            self.cooldown_timer = self.fire_interval
            return self.fire(self.target_enemy)
        return None

    def _select_target(self, enemies: List[Enemy]) -> Optional[Enemy]:
        valid = [
            e for e in enemies
            if e.is_alive and self.pos.distance_to(e.pos) <= self.attack_range
        ]
        if not valid:
            return None
        valid.sort(
            key=lambda e: (e.has_egg, e.follower.distance_traveled),
            reverse=True
        )
        return valid[0]

    @abstractmethod
    def fire(self, target: Enemy) -> Projectile:
        pass


# ======================================================================
# FIRE DRAGON — Rong Lua (AoE)
# ======================================================================
class FireDragon(DragonTower):
    """Rồng lửa — AoE burst / 360° nova at high levels."""

    def __init__(self, tower_id: int, pos: Vec2) -> None:
        super().__init__(
            tower_id=tower_id,
            name="Fire Dragon",
            pos=pos,
            gold_cost=100,
            ruby_cost=0,
            attack_range=200.0,
            fire_interval=1.2
        )
        self.damage = 25.0          # x2 từ 12.5
        self.aoe_radius = 52.0
        self.projectile_speed = 480.0
        self.burn_damage = 0.0
        self.burn_duration = 0.0
        self.burn_interval = 0.0
        self.critical_chance = 0.0
        self.critical_multiplier = 2.0
        self.rotation_mode = False

    def _on_upgrade(self) -> None:
        if self.level == 2:
            self.damage = 45.0          # x2 từ 22.5
            self.aoe_radius = 60.0
            self.fire_interval = 1.0
            self.attack_range = 225.0
        elif self.level == 3:
            self.damage = 60.0          # x2 từ 30.0
            self.aoe_radius = 90.0
            self.fire_interval = 0.5
            self.attack_range = 200.0
            self.rotation_mode = True
            self.burn_damage = 15.0
            self.burn_duration = 3.0
            self.burn_interval = 1.0
        elif self.level == 4:
            # Lv4-6: fire_aura 360° — đánh tất cả địch xung quanh tháp
            self.damage = 90.0          # x2 từ 45.0
            self.aoe_radius = 200.0     # aura radius = attack_range
            self.fire_interval = 0.4
            self.attack_range = 200.0
            self.burn_damage = 15.0
            self.burn_duration = 3.0
            self.burn_interval = 1.0
        elif self.level == 5:
            self.damage = 160.0         # x2 từ 80.0
            self.aoe_radius = 224.0
            self.fire_interval = 0.35
            self.attack_range = 224.0
            self.critical_chance = 0.20
            self.burn_damage = 15.0
            self.burn_duration = 3.0
            self.burn_interval = 1.0
        elif self.level == 6:
            self.damage = 260.0         # x2 từ 130.0
            self.aoe_radius = 256.0
            self.fire_interval = 0.25
            self.attack_range = 256.0
            self.critical_chance = 0.35
            self.burn_damage = 15.0
            self.burn_duration = 3.0
            self.burn_interval = 1.0

    def fire(self, target: Enemy) -> Projectile:
        if self.level >= 4:
            # Lv4-6: Fire Aura — nổ 360° tức thì từ vị trí tháp
            return Projectile(
                start_pos=self.pos,
                target_enemy=target,
                speed=self.projectile_speed,
                damage=self.damage,
                effect_type="fire_aura",
                aoe_radius=self.aoe_radius,
                dot_damage=self.burn_damage,
                dot_interval=self.burn_interval,
                dot_duration=self.burn_duration,
                critical_chance=self.critical_chance,
                critical_multiplier=self.critical_multiplier,
            )
        elif self.level >= 1:
            # Lv1-3: Fire Ray — tia lửa thẳng tới mục tiêu
            return Projectile(
                start_pos=self.pos,
                target_enemy=target,
                speed=self.projectile_speed,
                damage=self.damage,
                effect_type="fire_ray",
                aoe_radius=0.0,
                dot_damage=self.burn_damage,
                dot_interval=self.burn_interval,
                dot_duration=self.burn_duration,
                critical_chance=self.critical_chance,
                critical_multiplier=self.critical_multiplier,
            )


# ======================================================================
# ICE DRAGON — Rong Bang (Slow/Freeze)
# ======================================================================
class IceDragon(DragonTower):
    """Rồng băng — slow / freeze control."""

    def __init__(self, tower_id: int, pos: Vec2) -> None:
        super().__init__(
            tower_id=tower_id,
            name="Ice Dragon",
            pos=pos,
            gold_cost=100,
            ruby_cost=0,
            attack_range=240.0,
            fire_interval=1.0
        )
        self.damage = 5.0
        self.slow_factor = 0.25
        self.slow_duration = 2.0
        self.projectile_speed = 420.0
        self.freeze_mode = False
        self.freeze_chance = 0.0
        self.freeze_duration = 0.0

    def _on_upgrade(self) -> None:
        if self.level == 2:
            self.damage = 11.0
            self.slow_factor = 0.35
            self.slow_duration = 2.5
            self.fire_interval = 0.9
            self.attack_range = 264.0
        elif self.level == 3:
            self.damage = 17.5
            self.slow_factor = 0.45
            self.slow_duration = 2.0
            self.fire_interval = 0.8
            self.attack_range = 240.0
            self.freeze_mode = True
        elif self.level == 4:
            self.damage = 27.5
            self.slow_factor = 0.60
            self.slow_duration = 2.0
            self.fire_interval = 0.7
            self.attack_range = 280.0
        elif self.level == 5:
            self.damage = 42.5
            self.slow_factor = 0.65
            self.slow_duration = 2.0
            self.fire_interval = 0.6
            self.attack_range = 304.0
            self.freeze_chance = 0.15
            self.freeze_duration = 1.5
        elif self.level == 6:
            self.damage = 70.0
            self.slow_factor = 0.75
            self.slow_duration = 2.0
            self.fire_interval = 0.5
            self.attack_range = 336.0
            self.freeze_chance = 0.30
            self.freeze_duration = 1.5

    def fire(self, target: Enemy) -> Projectile:
        return Projectile(
            start_pos=self.pos,
            target_enemy=target,
            speed=self.projectile_speed,
            damage=self.damage,
            effect_type="freeze" if self.level >= 5 else "ice",
            slow_factor=self.slow_factor,
            slow_duration=self.slow_duration,
            freeze_chance=self.freeze_chance,
            freeze_duration=self.freeze_duration
        )


# ======================================================================
# POISON DRAGON — Rong Doc (DoT + Stun)
# ======================================================================
class PoisonDragon(DragonTower):
    """Rồng độc — poison DoT + armor melt + knockback."""

    def __init__(self, tower_id: int, pos: Vec2) -> None:
        super().__init__(
            tower_id=tower_id,
            name="Poison Dragon",
            pos=pos,
            gold_cost=100,
            ruby_cost=1,
            attack_range=180.0,
            fire_interval=1.2
        )
        self.impact_damage = 7.5
        self.dot_damage = 5.0
        self.dot_interval = 1.0
        self.dot_duration = 3.0
        self.projectile_speed = 330.0
        self.armor_reduction = 0.0
        self.knockback_chance = 0.0
        self.stun_chance = 0.0
        self.stun_duration = 0.0

    def _on_upgrade(self) -> None:
        if self.level == 2:
            self.impact_damage = 15.0
            self.dot_damage = 12.5
            self.dot_duration = 3.0
            self.fire_interval = 1.0
        elif self.level == 3:
            self.impact_damage = 22.5
            self.dot_damage = 22.5
            self.dot_duration = 4.0
            self.fire_interval = 0.9
        elif self.level == 4:
            self.impact_damage = 35.0
            self.dot_damage = 40.0
            self.dot_duration = 4.0
            self.fire_interval = 0.8
            self.armor_reduction = 0.30
            self.knockback_chance = 0.10
        elif self.level == 5:
            self.impact_damage = 55.0
            self.dot_damage = 70.0
            self.dot_duration = 5.0
            self.fire_interval = 0.6
            self.armor_reduction = 0.30
            self.knockback_chance = 0.25
            self.stun_chance = 0.30
            self.stun_duration = 1.2
        elif self.level == 6:
            self.impact_damage = 90.0
            self.dot_damage = 130.0
            self.dot_duration = 5.0
            self.fire_interval = 0.5
            self.armor_reduction = 0.30
            self.knockback_chance = 0.40
            self.stun_chance = 0.30
            self.stun_duration = 1.2

    def fire(self, target: Enemy) -> Projectile:
        return Projectile(
            start_pos=self.pos,
            target_enemy=target,
            speed=self.projectile_speed,
            damage=self.impact_damage,
            effect_type="poison",
            dot_damage=self.dot_damage,
            dot_interval=self.dot_interval,
            dot_duration=self.dot_duration,
            armor_reduction=self.armor_reduction,
            knockback_chance=self.knockback_chance,
            stun_chance=self.stun_chance,
            stun_duration=self.stun_duration
        )
