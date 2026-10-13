from __future__ import annotations
from typing import Callable, List, Optional, Dict
from core.vec2 import Vec2
from core.enemy import Enemy, DroppedEgg
from core.tower import DragonTower, FireDragon, IceDragon, PoisonDragon
from core.projectile import Projectile
from core.wave_spawner import WaveSpawner, WaveConfig


class GameManager:
    """
    Central Game Engine Orchestrator.
    Manages: Gold + Ruby currency, Mana system, dragon towers, spells,
    active entities, win/loss conditions, and egg theft mechanics.

    RESOURCES:
      - Gold  : earned by killing enemies, used to buy/upgrade towers
      - Ruby  : rare drop from enemies, unlocks advanced towers & upgrades
      - Mana  : regenerates over time, spent to cast spells

    SPELLS (cost Mana):
      - Fireball    : AoE projectile launched at targeted area
      - Frost Blast : Freeze all enemies on screen briefly
    """

    # Mana config
    MAX_MANA: int = 100
    MANA_REGEN_PER_SEC: float = 6.0    # Mana per second

    # Spell costs
    SPELL_MANA_COST: Dict[str, int] = {
        "fireball":   35,
        "frost_blast": 50,
    }

    # Spell effects
    FIREBALL_DAMAGE: float = 120.0
    FIREBALL_AOE: float = 80.0
    FROST_BLAST_DURATION: float = 2.5

    def __init__(
        self,
        waypoints: List[Vec2],
        starting_eggs: int = 5,
        starting_gold: int = 400,
        starting_ruby: int = 0,
        logger: Optional[Callable[[str], None]] = None
    ) -> None:
        self.waypoints = waypoints
        self.nest_pos = waypoints[-1] if waypoints else Vec2(0.0, 0.0)
        self.spawn_pos = waypoints[0] if waypoints else Vec2(0.0, 0.0)

        # Resources
        self.player_eggs: int = starting_eggs
        self.nest_eggs: int = starting_eggs
        self.gold: int = starting_gold
        self.ruby: int = starting_ruby
        self.score: int = 0

        # Mana
        self.mana: float = float(self.MAX_MANA)

        # Entities
        self.enemies: List[Enemy] = []
        self.towers: List[DragonTower] = []
        self.projectiles: List[Projectile] = []
        self.dropped_eggs: List[DroppedEgg] = []

        # Pedestals
        self.pedestals: List[Vec2] = self._generate_default_pedestals(waypoints)

        # State flags
        self.is_game_over: bool = False
        self.is_victory: bool = False
        self.total_time: float = 0.0
        self.logger: Optional[Callable[[str], None]] = logger

        # Game speed multiplier
        self.game_speed: int = 1

        # Active spell visual effects (for rendering)
        self.spell_effects: List[Dict] = []   # [{type, pos, radius, timer}]

        # Default wave setup
        default_waves = [
            WaveConfig(enemy_count=4,  spawn_interval=1.5, base_hp=70.0,  base_speed=42.0, gold_reward=30, enemy_name="Scout Goblin"),
            WaveConfig(enemy_count=6,  spawn_interval=1.2, base_hp=110.0, base_speed=48.0, gold_reward=40, enemy_name="Armored Thief"),
            WaveConfig(enemy_count=8,  spawn_interval=1.0, base_hp=160.0, base_speed=55.0, gold_reward=50, enemy_name="Dragon Raider"),
        ]
        self.wave_spawner = WaveSpawner(default_waves, inter_wave_delay=3.0)
        self.wave_spawner.start()

    # ------------------------------------------------------------------
    # Pedestal generation
    # ------------------------------------------------------------------
    def _generate_default_pedestals(self, waypoints: List[Vec2]) -> List[Vec2]:
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

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------
    def log(self, message: str) -> None:
        if self.logger:
            self.logger(f"[{self.total_time:06.2f}s] {message}")

    # ------------------------------------------------------------------
    # Tower management
    # ------------------------------------------------------------------
    def can_afford_tower(self, tower: DragonTower) -> bool:
        return self.gold >= tower.gold_cost and self.ruby >= tower.ruby_cost

    def add_tower(self, tower: DragonTower) -> bool:
        if self.can_afford_tower(tower):
            self.gold -= tower.gold_cost
            self.ruby -= tower.ruby_cost
            self.towers.append(tower)
            self.log(f"PLACED {tower.name} Lv{tower.level} at ({tower.pos.x:.0f},{tower.pos.y:.0f}) | Gold:{self.gold} Ruby:{self.ruby}")
            return True
        self.log(f"FAILED place {tower.name}: need {tower.gold_cost}g/{tower.ruby_cost}R (have {self.gold}g/{self.ruby}R)")
        return False

    def can_afford_upgrade(self, tower: DragonTower) -> bool:
        return (
            tower.level < tower.max_level
            and self.gold >= tower.upgrade_gold_cost
            and self.ruby >= tower.upgrade_ruby_cost
        )

    def upgrade_tower(self, tower: DragonTower) -> bool:
        if self.can_afford_upgrade(tower):
            g_cost = tower.upgrade_gold_cost
            r_cost = tower.upgrade_ruby_cost
            if tower.upgrade():
                self.gold -= g_cost
                self.ruby -= r_cost
                self.log(f"UPGRADED {tower.name} to Lv{tower.level}! -{g_cost}g -{r_cost}R")
                return True
        self.log(f"FAILED upgrade {tower.name}")
        return False

    def sell_tower(self, tower: DragonTower) -> None:
        if tower in self.towers:
            self.gold += tower.sell_gold
            self.ruby += tower.sell_ruby
            self.towers.remove(tower)
            self.log(f"SOLD {tower.name} Lv{tower.level} | +{tower.sell_gold}g +{tower.sell_ruby}R")

    # ------------------------------------------------------------------
    # Mana
    # ------------------------------------------------------------------
    def add_mana(self, amount: float) -> None:
        self.mana = min(float(self.MAX_MANA), self.mana + amount)

    def spend_mana(self, amount: int) -> bool:
        if self.mana >= amount:
            self.mana -= amount
            return True
        return False

    # ------------------------------------------------------------------
    # Spells
    # ------------------------------------------------------------------
    def cast_fireball(self, target_pos: Vec2) -> bool:
        """
        Fireball: Cost 35 Mana. Launch AoE fire projectile at target_pos.
        Hits all enemies in 80-unit radius for 120 damage.
        """
        if not self.spend_mana(self.SPELL_MANA_COST["fireball"]):
            self.log("FIREBALL: Not enough Mana!")
            return False

        # Apply AoE damage directly (no travel time for spells)
        hit_count = 0
        for e in self.enemies:
            if e.is_alive and e.pos.distance_to(target_pos) <= self.FIREBALL_AOE:
                e.take_damage(self.FIREBALL_DAMAGE)
                hit_count += 1

        # Visual effect marker
        self.spell_effects.append({
            "type": "fireball",
            "pos": Vec2(target_pos.x, target_pos.y),
            "radius": self.FIREBALL_AOE,
            "timer": 0.6
        })
        self.log(f"SPELL: Fireball at ({target_pos.x:.0f},{target_pos.y:.0f}) hit {hit_count} enemies!")
        return True

    def cast_frost_blast(self) -> bool:
        """
        Frost Blast: Cost 50 Mana. Freeze ALL active enemies for 2.5 seconds.
        """
        if not self.spend_mana(self.SPELL_MANA_COST["frost_blast"]):
            self.log("FROST BLAST: Not enough Mana!")
            return False

        for e in self.enemies:
            if e.is_alive:
                e.status_manager.apply_freeze(self.FROST_BLAST_DURATION)

        # Full-screen frost effect
        self.spell_effects.append({
            "type": "frost_blast",
            "pos": Vec2(500, 350),
            "radius": 0,
            "timer": 0.8
        })
        self.log(f"SPELL: Frost Blast! All {len(self.enemies)} enemies frozen for {self.FROST_BLAST_DURATION}s")
        return True

    # ------------------------------------------------------------------
    # Main update loop
    # ------------------------------------------------------------------
    def update(self, dt: float) -> None:
        """One frame tick — applies game_speed multiplier."""
        if self.is_game_over or self.is_victory:
            return

        dt = dt * self.game_speed
        self.total_time += dt

        # 1. Mana regen
        self.add_mana(self.MANA_REGEN_PER_SEC * dt)

        # 2. Spawn new enemies
        new_enemy = self.wave_spawner.update(dt, self.waypoints)
        if new_enemy:
            self.enemies.append(new_enemy)

        # 3. Update spell visual effects
        for eff in self.spell_effects[:]:
            eff["timer"] -= dt
            if eff["timer"] <= 0:
                self.spell_effects.remove(eff)

        # 4. Update enemies
        for enemy in self.enemies[:]:
            if not enemy.is_alive:
                continue

            stole_egg, escaped = enemy.update(dt, self.nest_eggs)

            if stole_egg:
                self.nest_eggs -= 1

            if escaped:
                self.player_eggs -= 1
                if self.player_eggs <= 0:
                    self.is_game_over = True
                    return

        # 5. Process enemy deaths
        for enemy in self.enemies[:]:
            if not enemy.is_alive and not enemy.has_escaped:
                self.gold += enemy.gold_reward
                self.score += enemy.gold_reward * 10

                # Ruby drop: 20% chance per kill
                import random
                if random.random() < 0.20:
                    self.ruby += 1
                    self.log(f"RUBY DROP! +1 Ruby from {enemy.name} (Total: {self.ruby})")

                # Mana from kills
                self.add_mana(8.0)

                if enemy.has_egg:
                    dropped = DroppedEgg(pos=enemy.pos, start_pos=enemy.pos, timer=3.0, initial_timer=3.0)
                    self.dropped_eggs.append(dropped)

                self.enemies.remove(enemy)

        # 6. Update dropped egg timers
        for egg in self.dropped_eggs[:]:
            if not egg.is_returned:
                egg.timer -= dt
                if egg.timer <= 0:
                    egg.is_returned = True
                    self.nest_eggs += 1
                    self.dropped_eggs.remove(egg)

        # 7. Update towers & fire projectiles
        for tower in self.towers:
            projectile = tower.update(dt, self.enemies)
            if projectile:
                self.projectiles.append(projectile)

        # 8. Update projectiles
        for proj in self.projectiles[:]:
            hit = proj.update(dt, self.enemies)
            if hit:
                self.projectiles.remove(proj)

        # 9. Victory check
        if self.wave_spawner.is_finished and len(self.enemies) == 0 and self.player_eggs > 0:
            self.is_victory = True
