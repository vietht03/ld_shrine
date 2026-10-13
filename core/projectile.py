from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional
import random
from core.vec2 import Vec2
from core.enemy import Enemy


class Projectile:
    """
    Projectile fired by a Dragon Tower.
    Supports: fire (AoE + optional burn DoT), ice (slow), freeze (full stop),
    poison (DoT + stun chance), fireball spell (AoE), frost spell (area freeze).
    """

    def __init__(
        self,
        start_pos: Vec2,
        target_enemy: Enemy,
        speed: float = 300.0,
        damage: float = 20.0,
        effect_type: str = "physical",
        aoe_radius: float = 0.0,
        slow_factor: float = 0.0,
        slow_duration: float = 0.0,
        dot_damage: float = 0.0,
        dot_interval: float = 0.5,
        dot_duration: float = 0.0,
        stun_chance: float = 0.0,
        stun_duration: float = 0.0
    ) -> None:
        self.pos = Vec2(start_pos.x, start_pos.y)
        self.target_enemy = target_enemy
        self.target_pos = Vec2(target_enemy.pos.x, target_enemy.pos.y)
        self.speed = speed
        self.damage = damage
        self.effect_type = effect_type
        self.aoe_radius = aoe_radius
        self.slow_factor = slow_factor
        self.slow_duration = slow_duration
        self.dot_damage = dot_damage
        self.dot_interval = dot_interval
        self.dot_duration = dot_duration
        self.stun_chance = stun_chance
        self.stun_duration = stun_duration
        self.has_hit: bool = False

    def update(self, dt: float, enemies: List[Enemy]) -> bool:
        if self.has_hit:
            return True

        # Track target if alive
        if self.target_enemy and self.target_enemy.is_alive:
            self.target_pos = self.target_enemy.pos

        direction = self.target_pos - self.pos
        distance = direction.length()
        move_dist = self.speed * dt

        if move_dist >= distance or distance == 0:
            self.pos = self.target_pos
            self._on_impact(enemies)
            self.has_hit = True
            return True
        else:
            self.pos = self.pos + direction.normalized() * move_dist
            return False

    def _on_impact(self, enemies: List[Enemy]) -> None:
        if self.aoe_radius > 0.0:
            for enemy in enemies:
                if enemy.is_alive and enemy.pos.distance_to(self.pos) <= self.aoe_radius:
                    self._apply_payload(enemy)
        else:
            if self.target_enemy and self.target_enemy.is_alive:
                self._apply_payload(self.target_enemy)

    def _apply_payload(self, enemy: Enemy) -> None:
        enemy.take_damage(self.damage)

        if self.effect_type in ("ice", "freeze"):
            if self.effect_type == "freeze":
                enemy.status_manager.apply_freeze(self.slow_duration)
            elif self.slow_factor > 0:
                enemy.status_manager.apply_slow(self.slow_factor, self.slow_duration)

        elif self.effect_type == "poison":
            if self.dot_damage > 0:
                enemy.status_manager.apply_dot(self.dot_damage, self.dot_interval, self.dot_duration)
            # Stun check
            if self.stun_chance > 0 and random.random() < self.stun_chance:
                enemy.status_manager.apply_freeze(self.stun_duration)

        elif self.effect_type == "fire":
            # Burn DoT (Lv3 Fire Dragon)
            if self.dot_damage > 0:
                enemy.status_manager.apply_dot(self.dot_damage, self.dot_interval, self.dot_duration)

        # Spell types handled the same way via aoe_radius
