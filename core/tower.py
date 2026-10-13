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
        self.max_level: int = 3

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
    """
    Rong Lua – Phun lua thieu dot ke dich.
    Lv1: AoE damage vung nho
    Lv2: AoE lon hon, sat thuong cao
    Lv3: Phun lua lien tuc, cong them hieu ung dot chay (DoT)
    """

    def __init__(self, tower_id: int, pos: Vec2) -> None:
        super().__init__(
            tower_id=tower_id,
            name="Fire Dragon",
            pos=pos,
            gold_cost=120,
            ruby_cost=0,
            attack_range=155.0,
            fire_interval=1.1
        )
        self.damage = 40.0
        self.aoe_radius = 55.0
        self.projectile_speed = 360.0
        # Level 3 unlocks burn DoT
        self.burn_damage: float = 0.0
        self.burn_duration: float = 0.0

    def _on_upgrade(self) -> None:
        self.damage *= 1.45
        self.aoe_radius *= 1.20
        if self.level == 3:
            # Lv3: unlock burn (DoT)
            self.burn_damage = 12.0
            self.burn_duration = 2.5

    def fire(self, target: Enemy) -> Projectile:
        return Projectile(
            start_pos=self.pos,
            target_enemy=target,
            speed=self.projectile_speed,
            damage=self.damage,
            effect_type="fire",
            aoe_radius=self.aoe_radius,
            dot_damage=self.burn_damage,
            dot_interval=0.5,
            dot_duration=self.burn_duration
        )


# ======================================================================
# ICE DRAGON — Rong Bang (Slow/Freeze)
# ======================================================================
class IceDragon(DragonTower):
    """
    Rong Bang – Lam cham / dong bang ke dich.
    Lv1: Lam cham 40%
    Lv2: Lam cham 60%, tam danh lon hon
    Lv3: Dong bang hoan toan trong 2 giay
    """

    def __init__(self, tower_id: int, pos: Vec2) -> None:
        super().__init__(
            tower_id=tower_id,
            name="Ice Dragon",
            pos=pos,
            gold_cost=140,
            ruby_cost=1,
            attack_range=145.0,
            fire_interval=1.0
        )
        self.damage = 20.0
        self.slow_factor = 0.40
        self.slow_duration = 2.0
        self.projectile_speed = 420.0
        self.freeze_mode: bool = False      # Lv3: full freeze

    def _on_upgrade(self) -> None:
        self.damage *= 1.30
        if self.level == 2:
            self.slow_factor = 0.60
            self.slow_duration = 2.8
        elif self.level == 3:
            self.freeze_mode = True         # Now fires freeze shots
            self.slow_factor = 1.0
            self.slow_duration = 2.2

    def fire(self, target: Enemy) -> Projectile:
        return Projectile(
            start_pos=self.pos,
            target_enemy=target,
            speed=self.projectile_speed,
            damage=self.damage,
            effect_type="freeze" if self.freeze_mode else "ice",
            slow_factor=self.slow_factor,
            slow_duration=self.slow_duration
        )


# ======================================================================
# POISON DRAGON — Rong Doc (DoT + Stun)
# ======================================================================
class PoisonDragon(DragonTower):
    """
    Rong Doc – Gay sat thuong theo thoi gian (DoT) va lam choan.
    Lv1: Doc gay 8 dame/0.5s trong 3 giay
    Lv2: Doc manh hon, toc do ban nhanh hon
    Lv3: Mo khoa Stun – moi lan ban co 30% danh choan ke dich 1.2 giay
    """

    def __init__(self, tower_id: int, pos: Vec2) -> None:
        super().__init__(
            tower_id=tower_id,
            name="Poison Dragon",
            pos=pos,
            gold_cost=130,
            ruby_cost=1,
            attack_range=135.0,
            fire_interval=0.9
        )
        self.impact_damage = 12.0
        self.dot_damage = 8.0
        self.dot_interval = 0.5
        self.dot_duration = 3.0
        self.projectile_speed = 330.0
        self.stun_chance: float = 0.0       # Lv3: 30% stun
        self.stun_duration: float = 0.0

    def _on_upgrade(self) -> None:
        self.impact_damage *= 1.35
        self.dot_damage *= 1.45
        self.dot_duration += 0.8
        if self.level == 3:
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
            stun_chance=self.stun_chance,
            stun_duration=self.stun_duration
        )
