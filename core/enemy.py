from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
from core.vec2 import Vec2
from core.status_effects import StatusEffectManager


class WaypointFollower:
    """
    Handles path navigation along a sequence of waypoints.
    Supports forward traversal to Nest and reverse traversal back to Spawn.
    """

    def __init__(self, waypoints: List[Vec2], base_speed: float) -> None:
        self.waypoints = waypoints
        self.current_target_index: int = 1 if len(waypoints) > 1 else 0
        self.is_returning: bool = False
        self.distance_traveled: float = 0.0

    def get_current_target(self) -> Vec2:
        return self.waypoints[self.current_target_index]

    def update_position(self, current_pos: Vec2, effective_speed: float, dt: float) -> tuple[Vec2, bool, bool]:
        """
        Moves pos towards target waypoint.
        Returns tuple: (new_pos, reached_nest, reached_spawn)
        """
        if not self.waypoints:
            return current_pos, False, False

        reached_nest = False
        reached_spawn = False

        target_pos = self.waypoints[self.current_target_index]
        direction = (target_pos - current_pos)
        dist_to_target = direction.length()

        move_distance = effective_speed * dt
        self.distance_traveled += move_distance

        if move_distance >= dist_to_target and dist_to_target > 0:
            # Arrived at waypoint
            current_pos = target_pos

            if not self.is_returning:
                # Moving towards Nest
                if self.current_target_index == len(self.waypoints) - 1:
                    reached_nest = True
                else:
                    self.current_target_index += 1
            else:
                # Returning towards Spawn
                if self.current_target_index == 0:
                    reached_spawn = True
                else:
                    self.current_target_index -= 1
        else:
            if dist_to_target > 0:
                current_pos = current_pos + direction.normalized() * move_distance

        return current_pos, reached_nest, reached_spawn

    def reverse_path(self) -> None:
        """Reverses navigation direction back toward Spawn."""
        self.is_returning = True
        if self.current_target_index > 0:
            self.current_target_index -= 1


@dataclass
class DroppedEgg:
    """Represents an egg dropped by an enemy upon death."""
    pos: Vec2
    start_pos: Vec2 = field(default_factory=lambda: Vec2(0, 0))
    timer: float = 3.0   # Respawn timer in seconds
    initial_timer: float = 3.0
    is_returned: bool = False

    def get_interpolated_pos(self, nest_pos: Vec2) -> Vec2:
        """Returns visual interpolated position from death location back to Dragon Nest."""
        if self.initial_timer <= 0:
            return nest_pos
        t = max(0.0, min(1.0, 1.0 - (self.timer / self.initial_timer)))
        # Smoothstep easing curve
        t_smooth = t * t * (3.0 - 2.0 * t)
        return self.start_pos * (1.0 - t_smooth) + nest_pos * t_smooth


class Enemy:
    """
    Represents an enemy unit with waypoint movement, egg theft AI,
    and a StatusEffectManager for debuffs.
    """

    def __init__(
        self,
        enemy_id: int,
        name: str,
        start_pos: Vec2,
        waypoints: List[Vec2],
        hp: float,
        base_speed: float,
        gold_reward: int
    ) -> None:
        self.id = enemy_id
        self.name = name
        self.pos = start_pos
        self.max_hp = hp
        self.hp = hp
        self.base_speed = base_speed
        self.gold_reward = gold_reward
        self.has_egg: bool = False
        self.is_alive: bool = True
        self.has_escaped: bool = False

        self.follower = WaypointFollower(waypoints, base_speed)
        self.status_manager = StatusEffectManager()

    def update(self, dt: float, nest_eggs_count: int) -> tuple[bool, bool]:
        """
        Updates status effects, HP, and position.
        Returns tuple: (stole_egg_this_tick, escaped_with_egg_this_tick)
        """
        if not self.is_alive:
            return False, False

        # 1. Update status effects and apply DoT
        dot_damage = self.status_manager.update(dt)
        if dot_damage > 0:
            self.take_damage(dot_damage)
            if not self.is_alive:
                return False, False

        # 2. Calculate movement based on status multipliers
        speed_mult = self.status_manager.get_speed_multiplier()
        effective_speed = self.base_speed * speed_mult

        # 3. Update waypoint position
        self.pos, reached_nest, reached_spawn = self.follower.update_position(
            self.pos, effective_speed, dt
        )

        stole_egg = False
        escaped = False

        if reached_nest and not self.follower.is_returning:
            if nest_eggs_count > 0:
                self.has_egg = True
                stole_egg = True
                self.follower.reverse_path()

        if reached_spawn and self.follower.is_returning:
            if self.has_egg:
                escaped = True
                self.has_escaped = True
                self.is_alive = False

        return stole_egg, escaped

    def take_damage(self, damage: float) -> None:
        """Inflicts damage on enemy and updates alive status."""
        self.hp -= damage
        if self.hp <= 0:
            self.hp = 0.0
            self.is_alive = False

    @property
    def speed(self) -> float:
        return self.base_speed * self.status_manager.get_speed_multiplier()
