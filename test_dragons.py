from core.game_manager import GameManager
from core.tower import FireDragon, IceDragon, PoisonDragon
from core.vec2 import Vec2
from core.enemy import Enemy, DroppedEgg


def test_game_start_and_dropped_egg_intercept_rules():
    waypoints = [Vec2(0, 300), Vec2(200, 300), Vec2(500, 300)]
    game = GameManager(waypoints=waypoints, starting_eggs=5, starting_gold=500)

    assert game.gold == 500

    egg = DroppedEgg(pos=Vec2(200, 300), start_pos=Vec2(200, 300), timer=6.0, initial_timer=6.0)
    enemy = Enemy(1, "Raider", Vec2(200, 300), waypoints, 100.0, 80.0, 10, enemy_type="thief")
    game.dropped_eggs.append(egg)

    game._intercept_dropped_egg(enemy)
    assert enemy.has_egg is True
    assert len(game.dropped_eggs) == 0


def test_fire_dragon_matches_requested_balance():
    dragon = FireDragon(1, Vec2(0, 0))

    assert dragon.level == 1
    assert dragon.fire_interval == 1.2
    assert dragon.damage == 12.5
    assert dragon.aoe_radius == 52.0

    for _ in range(2):
        dragon.upgrade()

    assert dragon.level == 3
    assert dragon.fire_interval == 0.5
    assert dragon.damage == 30.0
    assert dragon.burn_duration == 3.0
    assert dragon.aoe_radius >= 90.0

    for _ in range(3):
        dragon.upgrade()

    assert dragon.level == 6
    assert dragon.critical_chance == 0.35
    assert dragon.damage == 130.0


def test_ice_dragon_matches_requested_balance():
    dragon = IceDragon(2, Vec2(0, 0))

    assert dragon.level == 1
    assert dragon.fire_interval == 1.0
    assert dragon.damage == 5.0
    assert dragon.slow_factor == 0.25
    assert dragon.slow_duration == 2.0

    for _ in range(4):
        dragon.upgrade()

    assert dragon.level == 5
    assert dragon.fire_interval == 0.6
    assert dragon.slow_factor == 0.65
    assert dragon.freeze_chance == 0.15
    assert dragon.freeze_duration == 1.5

    dragon.upgrade()
    assert dragon.level == 6
    assert dragon.damage == 70.0
    assert dragon.freeze_chance == 0.30


def test_poison_dragon_matches_requested_balance():
    dragon = PoisonDragon(3, Vec2(0, 0))

    assert dragon.level == 1
    assert dragon.fire_interval == 1.2
    assert dragon.impact_damage == 7.5
    assert dragon.dot_damage == 5.0
    assert dragon.dot_duration == 3.0

    for _ in range(3):
        dragon.upgrade()

    assert dragon.level == 4
    assert dragon.armor_reduction == 0.30
    assert dragon.knockback_chance == 0.10

    for _ in range(2):
        dragon.upgrade()

    assert dragon.level == 6
    assert dragon.impact_damage == 90.0
    assert dragon.knockback_chance == 0.40
