from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional
from core.vec2 import Vec2
from core.enemy import Enemy


class Projectile:
    """
    Represents a projectile in flight released by a Dragon Tower.
    Handles movement, collision detection, AoE damage, and status effect payload delivery.
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
        dot_duration: float = 0.0
    ) -> None:
        self.pos = start_pos
        self.target_enemy = target_enemy
        self.target_pos = target_enemy.pos
        self.speed = speed
        self.damage = damage
        self.effect_type = effect_type
        self.aoe_radius = aoe_radius
        self.slow_factor = slow_factor
        self.slow_duration = slow_duration
        self.dot_damage = dot_damage
        self.dot_interval = dot_interval
        self.dot_duration = dot_duration
        self.has_hit: bool = False

    def update(self, dt: float, enemies: List[Enemy]) -> bool:
        """
        Moves projectile toward target. Upon hit, applies damage and effects.
        Returns True if projectile hit target/destination.
        """
        if self.has_hit:
            return True

        # Update target_pos if enemy is alive
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
        """Applies damage and status effects to enemy or area."""
        if self.aoe_radius > 0.0:
            # Area of Effect impact
            for enemy in enemies:
                if enemy.is_alive and enemy.pos.distance_to(self.pos) <= self.aoe_radius:
                    self._apply_payload(enemy)
        else:
            # Single-target impact
            if self.target_enemy and self.target_enemy.is_alive:
                self._apply_payload(self.target_enemy)

    def _apply_payload(self, enemy: Enemy) -> None:
        """Inflicts base damage and attaches status effects to target enemy."""
        enemy.take_damage(self.damage)

        if self.effect_type == "ice" and self.slow_factor > 0:
            enemy.status_manager.apply_slow(self.slow_factor, self.slow_duration)
        elif self.effect_type == "poison" and self.dot_damage > 0:
            enemy.status_manager.apply_dot(self.dot_damage, self.dot_interval, self.dot_duration)
