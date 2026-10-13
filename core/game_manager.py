from __future__ import annotations
from typing import Callable, List, Optional, Dict
from core.vec2 import Vec2
from core.enemy import Enemy, DroppedEgg
from core.tower import DragonTower
from core.projectile import Projectile
from core.wave_spawner import WaveSpawner, WaveConfig


class GameManager:
    """
    Central Game Engine Orchestrator.
    Manages game state, pedestals, dragon towers (upgrades/selling), dragon spells,
    active entities, win/loss conditions, egg theft mechanics, and event logging.
    """

    def __init__(
        self,
        waypoints: List[Vec2],
        starting_eggs: int = 5,
        starting_gold: int = 450,
        logger: Optional[Callable[[str], None]] = None
    ) -> None:
        self.waypoints = waypoints
        self.nest_pos = waypoints[-1] if waypoints else Vec2(0.0, 0.0)
        self.spawn_pos = waypoints[0] if waypoints else Vec2(0.0, 0.0)

        self.player_eggs: int = starting_eggs
        self.nest_eggs: int = starting_eggs
        self.gold: int = starting_gold
        self.score: int = 0

        self.enemies: List[Enemy] = []
        self.towers: List[DragonTower] = []
        self.projectiles: List[Projectile] = []
        self.dropped_eggs: List[DroppedEgg] = []

        # Fixed Pedestals along the pathway curves
        self.pedestals: List[Vec2] = self._generate_default_pedestals(waypoints)

        # Dragon Spells State
        self.spell_cooldowns: Dict[str, float] = {
            "fire_rain": 0.0,
            "ice_freeze": 0.0,
            "poison_storm": 0.0
        }
        self.spell_max_cooldowns: Dict[str, float] = {
            "fire_rain": 15.0,
            "ice_freeze": 20.0,
            "poison_storm": 18.0
        }

        self.is_game_over: bool = False
        self.is_victory: bool = False
        self.total_time: float = 0.0
        self.logger: Optional[Callable[[str], None]] = logger

        # Default wave setup
        default_waves = [
            WaveConfig(enemy_count=4, spawn_interval=1.5, base_hp=70.0, base_speed=42.0, gold_reward=30, enemy_name="Scout Goblin"),
            WaveConfig(enemy_count=6, spawn_interval=1.2, base_hp=110.0, base_speed=48.0, gold_reward=40, enemy_name="Armored Thief"),
            WaveConfig(enemy_count=8, spawn_interval=1.0, base_hp=160.0, base_speed=55.0, gold_reward=50, enemy_name="Dragon Raider"),
        ]
        self.wave_spawner = WaveSpawner(default_waves, inter_wave_delay=3.0)
        self.wave_spawner.start()

    def _generate_default_pedestals(self, waypoints: List[Vec2]) -> List[Vec2]:
        """Generates fixed dragon platforms along the path curves."""
        if not waypoints:
            return []
        return [
            Vec2(150.0, 410.0),
            Vec2(250.0, 420.0),
            Vec2(380.0, 420.0),
            Vec2(480.0, 260.0),
            Vec2(620.0, 420.0),
            Vec2(720.0, 260.0),
            Vec2(820.0, 420.0),
        ]

    def log(self, message: str) -> None:
        """Emits structured log messages if logger callback is set."""
        if self.logger:
            self.logger(f"[{self.total_time:06.2f}s] {message}")

    def add_tower(self, tower: DragonTower) -> bool:
        """Attempts to purchase and place a Dragon Tower."""
        if self.gold >= tower.cost:
            self.gold -= tower.cost
            self.towers.append(tower)
            self.log(f"PLACED {tower.name} (Lvl {tower.level}) at ({tower.pos.x:.1f}, {tower.pos.y:.1f}) for {tower.cost} gold. Gold left: {self.gold}")
            return True
        else:
            self.log(f"FAILED to place {tower.name}: Insufficient gold ({self.gold}/{tower.cost})")
            return False

    def upgrade_tower(self, tower: DragonTower) -> bool:
        """Upgrades a Dragon Tower if player has sufficient gold."""
        cost = tower.upgrade_cost
        if self.gold >= cost:
            if tower.upgrade():
                self.gold -= cost
                self.log(f"UPGRADED {tower.name} to Level {tower.level}! Cost: {cost} gold. Gold left: {self.gold}")
                return True
        self.log(f"FAILED to upgrade {tower.name}: Needs {cost} gold (Have: {self.gold})")
        return False

    def sell_tower(self, tower: DragonTower) -> int:
        """Sells a Dragon Tower and refunds gold."""
        if tower in self.towers:
            refund = tower.sell_value
            self.towers.remove(tower)
            self.gold += refund
            self.log(f"SOLD {tower.name} (Lvl {tower.level}) for {refund} gold refund. Gold total: {self.gold}")
            return refund
        return 0

    def cast_spell(self, spell_type: str) -> bool:
        """Casts one of the 3 Dragon Spells (Fire Rain, Ice Freeze, Poison Storm)."""
        if self.spell_cooldowns.get(spell_type, 0.0) > 0.0:
            self.log(f"SPELL ON COOLDOWN: {spell_type.upper()} ({self.spell_cooldowns[spell_type]:.1f}s remaining)")
            return False

        if not self.enemies:
            self.log(f"SPELL CAST CANCELLED: No active enemies to target with {spell_type.upper()}")
            return False

        if spell_type == "fire_rain":
            for e in self.enemies:
                if e.is_alive:
                    e.take_damage(80.0)
            self.log("SPELL CAST: FIRE RAIN! Inflicted 80 physical damage to all active enemies.")

        elif spell_type == "ice_freeze":
            for e in self.enemies:
                if e.is_alive:
                    e.status_manager.apply_freeze(3.5)
            self.log("SPELL CAST: ICE FREEZE! Frozen all active enemies for 3.5 seconds.")

        elif spell_type == "poison_storm":
            for e in self.enemies:
                if e.is_alive:
                    e.status_manager.apply_dot(damage_per_tick=15.0, interval=0.5, duration=4.0)
            self.log("SPELL CAST: POISON STORM! Applied 15 dmg/tick DoT to all active enemies.")
        else:
            return False

        # Reset cooldown timer
        self.spell_cooldowns[spell_type] = self.spell_max_cooldowns[spell_type]
        return True

    def update(self, dt: float) -> None:
        """Executes one frame tick of game logic."""
        if self.is_game_over or self.is_victory:
            return

        self.total_time += dt

        # Update spell cooldown timers
        for spell in self.spell_cooldowns:
            if self.spell_cooldowns[spell] > 0.0:
                self.spell_cooldowns[spell] = max(0.0, self.spell_cooldowns[spell] - dt)

        # 1. Spawn new enemies
        new_enemy = self.wave_spawner.update(dt, self.waypoints)
        if new_enemy:
            self.enemies.append(new_enemy)
            self.log(f"SPAWNED {new_enemy.name} at Spawn ({new_enemy.pos.x:.1f}, {new_enemy.pos.y:.1f})")

        # 2. Update active enemies
        for enemy in self.enemies[:]:
            if not enemy.is_alive:
                continue

            stole_egg, escaped = enemy.update(dt, self.nest_eggs)

            if stole_egg:
                self.nest_eggs -= 1
                self.log(f"EGG STOLEN! {enemy.name} picked up egg from Dragon Nest. Nest eggs remaining: {self.nest_eggs}")

            if escaped:
                self.player_eggs -= 1
                self.log(f"EGG ESCAPED! {enemy.name} exited Spawn with an egg! Total Player Eggs left: {self.player_eggs}")
                if self.player_eggs <= 0:
                    self.is_game_over = True
                    self.log("GAME OVER: All dragon eggs were stolen!")
                    return

        # 3. Process enemy deaths (Gold & Egg drops)
        for enemy in self.enemies[:]:
            if not enemy.is_alive and not enemy.has_escaped:
                # Enemy died
                self.gold += enemy.gold_reward
                self.score += enemy.gold_reward * 10
                self.log(f"ENEMY SLAIN: {enemy.name} destroyed! +{enemy.gold_reward} Gold (Total Gold: {self.gold})")

                if enemy.has_egg:
                    dropped = DroppedEgg(pos=enemy.pos, start_pos=enemy.pos, timer=3.0, initial_timer=3.0)
                    self.dropped_eggs.append(dropped)
                    self.log(f"EGG DROPPED: {enemy.name} dropped stolen egg at ({enemy.pos.x:.1f}, {enemy.pos.y:.1f})! Added to respawn queue (3.0s).")

                self.enemies.remove(enemy)

        # 4. Update dropped egg timers and respawn queue
        for egg in self.dropped_eggs[:]:
            if not egg.is_returned:
                egg.timer -= dt
                if egg.timer <= 0:
                    egg.is_returned = True
                    self.nest_eggs += 1
                    self.log(f"EGG RETURNED: Dropped egg returned to Dragon Nest! Nest eggs count: {self.nest_eggs}")
                    self.dropped_eggs.remove(egg)

        # 5. Update towers & fire projectiles
        for tower in self.towers:
            projectile = tower.update(dt, self.enemies)
            if projectile:
                self.projectiles.append(projectile)
                target_name = projectile.target_enemy.name if projectile.target_enemy else "Area"
                self.log(f"TOWER FIRED: {tower.name} -> {target_name} with {projectile.effect_type.upper()} payload")

        # 6. Update projectiles & apply impact damage/status effects
        for proj in self.projectiles[:]:
            hit = proj.update(dt, self.enemies)
            if hit:
                if proj.target_enemy and proj.target_enemy.is_alive:
                    t = proj.target_enemy
                    if proj.effect_type == "ice":
                        self.log(f"STATUS EFFECT: Applied SLOW to {t.name} (Speed: {t.speed:.1f}/{t.base_speed:.1f})")
                    elif proj.effect_type == "poison":
                        self.log(f"STATUS EFFECT: Applied DoT (Poison) to {t.name} (HP: {t.hp:.1f}/{t.max_hp:.1f})")
                    elif proj.effect_type == "fire":
                        self.log(f"AOE IMPACT: Fire explosion at ({proj.pos.x:.1f}, {proj.pos.y:.1f}) dealing {proj.damage} AoE damage")

                self.projectiles.remove(proj)

        # 7. Check Victory condition
        if self.wave_spawner.is_finished and len(self.enemies) == 0 and self.player_eggs > 0:
            self.is_victory = True
            self.log("VICTORY! All waves defeated and Dragon Shrine eggs secured!")
