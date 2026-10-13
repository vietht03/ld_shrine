from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, Optional


class EffectType(Enum):
    SLOW = auto()
    DOT = auto()
    FREEZE = auto()


@dataclass
class StatusEffect:
    """Represents an active status effect instance."""
    effect_type: EffectType
    duration: float
    slow_factor: float = 0.0      # 0.0 to 1.0 (e.g. 0.4 = 40% speed reduction)
    dot_damage: float = 0.0       # Damage per tick
    dot_interval: float = 0.5     # Seconds between DoT ticks
    dot_timer: float = 0.0        # Accumulator for tick timing


class StatusEffectManager:
    """
    Manages active status effects on an enemy without thread/coroutine overhead.
    Refreshes effect durations cleanly upon re-application.
    """

    def __init__(self) -> None:
        self.effects: Dict[EffectType, StatusEffect] = {}

    def apply_slow(self, slow_factor: float, duration: float) -> None:
        """Applies or refreshes a Slow status effect."""
        existing = self.effects.get(EffectType.SLOW)
        if existing:
            existing.duration = max(existing.duration, duration)
            existing.slow_factor = max(existing.slow_factor, slow_factor)
        else:
            self.effects[EffectType.SLOW] = StatusEffect(
                effect_type=EffectType.SLOW,
                duration=duration,
                slow_factor=slow_factor
            )

    def apply_dot(self, damage_per_tick: float, interval: float, duration: float) -> None:
        """Applies or refreshes a Damage over Time (DoT) status effect."""
        existing = self.effects.get(EffectType.DOT)
        if existing:
            existing.duration = max(existing.duration, duration)
            existing.dot_damage = max(existing.dot_damage, damage_per_tick)
            existing.dot_interval = interval
        else:
            self.effects[EffectType.DOT] = StatusEffect(
                effect_type=EffectType.DOT,
                duration=duration,
                dot_damage=damage_per_tick,
                dot_interval=interval,
                dot_timer=0.0
            )

    def apply_freeze(self, duration: float) -> None:
        """Applies or refreshes a Freeze status effect."""
        existing = self.effects.get(EffectType.FREEZE)
        if existing:
            existing.duration = max(existing.duration, duration)
        else:
            self.effects[EffectType.FREEZE] = StatusEffect(
                effect_type=EffectType.FREEZE,
                duration=duration
            )

    def update(self, dt: float) -> float:
        """
        Updates active effect timers and returns total tick damage to be inflicted.
        Automatically cleans up expired effects.
        """
        total_dot_damage = 0.0
        expired_types = []

        for effect_type, effect in self.effects.items():
            effect.duration -= dt

            if effect_type == EffectType.DOT:
                effect.dot_timer += dt
                while effect.dot_timer >= effect.dot_interval:
                    effect.dot_timer -= effect.dot_interval
                    total_dot_damage += effect.dot_damage

            if effect.duration <= 0:
                expired_types.append(effect_type)

        for et in expired_types:
            del self.effects[et]

        return total_dot_damage

    def get_speed_multiplier(self, slow_resistance: float = 0.0) -> float:
        """
        Calculates current speed multiplier based on active Freeze and Slow effects.
        """
        if EffectType.FREEZE in self.effects:
            return 0.0

        slow_effect = self.effects.get(EffectType.SLOW)
        if slow_effect:
            adjusted_slow = slow_effect.slow_factor * max(0.0, 1.0 - slow_resistance)
            return max(0.0, 1.0 - adjusted_slow)

        return 1.0

    @property
    def is_frozen(self) -> bool:
        return EffectType.FREEZE in self.effects

    @property
    def is_slowed(self) -> bool:
        return EffectType.SLOW in self.effects

    @property
    def is_poisoned(self) -> bool:
        return EffectType.DOT in self.effects
