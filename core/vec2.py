from __future__ import annotations
import math
from dataclasses import dataclass


@dataclass(slots=True)
class Vec2:
    """A 2D mathematical vector for positions, directions, and movement."""
    x: float
    y: float

    def distance_to(self, other: Vec2) -> float:
        return math.hypot(self.x - other.x, self.y - other.y)

    def __add__(self, other: Vec2) -> Vec2:
        return Vec2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Vec2) -> Vec2:
        return Vec2(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> Vec2:
        return Vec2(self.x * scalar, self.y * scalar)

    def __rmul__(self, scalar: float) -> Vec2:
        return self.__mul__(scalar)

    def length(self) -> float:
        return math.hypot(self.x, self.y)

    def normalized(self) -> Vec2:
        len_val = self.length()
        if len_val == 0.0:
            return Vec2(0.0, 0.0)
        return Vec2(self.x / len_val, self.y / len_val)

    def to_tuple(self) -> tuple[float, float]:
        return (self.x, self.y)
