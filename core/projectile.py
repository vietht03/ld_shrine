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
        stun_duration: float = 0.0,
        critical_chance: float = 0.0,
        critical_multiplier: float = 2.0,
        freeze_chance: float = 0.0,
        freeze_duration: float = 0.0,
        armor_reduction: float = 0.0,
        knockback_chance: float = 0.0
    ) -> None:
        self.start_pos = Vec2(start_pos.x, start_pos.y)
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
        self.critical_chance = critical_chance
        self.critical_multiplier = critical_multiplier
        self.freeze_chance = freeze_chance
        self.freeze_duration = freeze_duration
        self.armor_reduction = armor_reduction
        self.knockback_chance = knockback_chance
        self.has_hit: bool = False

    def update(self, dt: float, enemies: List[Enemy]) -> bool:
        if self.has_hit:
            return True

        if self.effect_type == "fire_nova":
            self.pos = self.start_pos
            self._on_impact(enemies)
            self.has_hit = True
            return True

        if self.effect_type == "fire_aura":
            # Nổ 360° tức thì từ vị trí tháp (start_pos)
            self.pos = self.start_pos
            self._on_impact(enemies)
            self.has_hit = True
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
        if self.effect_type in ("fire_nova", "fire_aura"):
            # Nổ từ vị trí tháp, đánh tất cả địch trong bán kính
            impact_center = self.start_pos
            impacted = [
                enemy for enemy in enemies
                if enemy.is_alive and enemy.pos.distance_to(impact_center) <= self.aoe_radius
            ]
            for enemy in impacted:
                is_primary = (enemy is self.target_enemy)
                self._apply_payload(enemy, is_primary=is_primary)
            return

        impact_center = self.pos
        if self.aoe_radius > 0.0:
            impacted = [
                enemy for enemy in enemies
                if enemy.is_alive and enemy.pos.distance_to(impact_center) <= self.aoe_radius
            ]
            if self.target_enemy and self.target_enemy.is_alive and self.target_enemy in impacted:
                self._apply_payload(self.target_enemy, is_primary=True)
            for enemy in impacted:
                if enemy is not self.target_enemy:
                    self._apply_payload(enemy, is_primary=False)
        else:
            if self.target_enemy and self.target_enemy.is_alive:
                self._apply_payload(self.target_enemy, is_primary=True)

    def _calculate_damage(self, base_damage: float, is_primary: bool) -> float:
        damage = base_damage
        if self.effect_type in ("fire", "fire_ray", "fire_aura") and self.critical_chance > 0 and random.random() < self.critical_chance:
            damage *= self.critical_multiplier
        if self.aoe_radius > 0.0 and not is_primary:
            damage *= 0.8
        return damage

    def _resolve_dot_damage(self, enemy: Enemy) -> float:
        if self.dot_damage <= 0:
            return 0.0
        if self.dot_damage < 1.0:
            return enemy.max_hp * self.dot_damage
        return self.dot_damage

    def _apply_payload(self, enemy: Enemy, is_primary: bool = True) -> None:
        if self.aoe_radius <= 0 and enemy.evasion_chance > 0 and random.random() < enemy.evasion_chance:
            return

        enemy.take_damage(self._calculate_damage(self.damage, is_primary))

        if self.effect_type in ("ice", "freeze"):
            if self.effect_type == "freeze":
                if self.freeze_chance > 0 and random.random() < self.freeze_chance and not enemy.immune_to_freeze:
                    enemy.status_manager.apply_freeze(self.freeze_duration or self.slow_duration)
            elif self.slow_factor > 0:
                enemy.status_manager.apply_slow(self.slow_factor, self.slow_duration)

        elif self.effect_type == "poison":
            if self.dot_damage > 0:
                enemy.status_manager.apply_dot(self._resolve_dot_damage(enemy), self.dot_interval, self.dot_duration)
            if self.armor_reduction > 0:
                enemy.armor = min(0.85, getattr(enemy, "armor", 0.0) + self.armor_reduction)
            if self.stun_chance > 0 and random.random() < self.stun_chance and not enemy.immune_to_freeze:
                enemy.status_manager.apply_freeze(self.stun_duration)
            if self.knockback_chance > 0 and random.random() < self.knockback_chance and not enemy.immune_to_knockback and hasattr(enemy, "follower"):
                enemy.follower.reverse_path()

        elif self.effect_type in ("fire", "fire_ray", "fire_aura", "fire_nova"):
            if self.dot_damage > 0:
                enemy.status_manager.apply_dot(self._resolve_dot_damage(enemy), self.dot_interval, self.dot_duration)

        # Spell types handled the same way via aoe_radius
