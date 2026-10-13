from __future__ import annotations
import arcade
import math
from typing import Optional, List
from core.vec2 import Vec2
from core.game_manager import GameManager
from core.tower import FireDragon, IceDragon, PoisonDragon, DragonTower


SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
SCREEN_TITLE = "Lair Defense: Shrine - Tower Defense"


class GameView(arcade.View):
    """
    Refactored Arcade GUI View matching the battle layout of Lair Defense: Shrine.
    Features:
    - Fixed Dragon Pedestals (towers cannot be placed on empty space)
    - Interactive Radial Build & Upgrade/Sell Menus
    - Top Header Status HUD (Gold, Eggs, Wave, Score)
    - Bottom Spell/Skill Panel with cooldown masks (Fire Rain [Q], Ice Freeze [W], Poison Storm [E])
    - Clean Range Visuals (hover/selection only)
    - Styled Path, Dragon Nest Altar, and Gliding Dropped Egg Animations
    """

    def __init__(self, waypoints: List[Vec2]) -> None:
        super().__init__()
        self.waypoints = waypoints
        self.game = GameManager(waypoints=waypoints, starting_eggs=5, starting_gold=450)

        # Place initial demo towers on fixed pedestals
        if len(self.game.pedestals) >= 3:
            self.game.add_tower(FireDragon(tower_id=1, pos=self.game.pedestals[0]))
            self.game.add_tower(IceDragon(tower_id=2, pos=self.game.pedestals[1]))
            self.game.add_tower(PoisonDragon(tower_id=3, pos=self.game.pedestals[2]))

        self.selected_pedestal_idx: Optional[int] = None
        self.hovered_pedestal_idx: Optional[int] = None
        self.mouse_pos: Vec2 = Vec2(0.0, 0.0)

    def on_draw(self) -> None:
        """Render the complete game screen."""
        self.clear()
        arcade.set_background_color(arcade.color.DARK_SLATE_GRAY)

        # 1. Draw Map & Waypoint Path
        self._draw_path()

        # 2. Draw Dragon Nest Altar & Eggs
        self._draw_nest()

        # 3. Draw Fixed Dragon Pedestals
        self._draw_pedestals()

        # 4. Draw Towers
        self._draw_towers()

        # 5. Draw Enemies & Health Bars
        self._draw_enemies()

        # 6. Draw Projectiles
        self._draw_projectiles()

        # 7. Draw Returning Dropped Eggs
        self._draw_dropped_eggs()

        # 8. Draw Range Overlay (Only when hovered or selected)
        self._draw_range_overlay()

        # 9. Draw Pedestal Radial / Modal Selection Menu
        self._draw_pedestal_menu()

        # 10. Draw Top Header HUD Bar
        self._draw_top_hud()

        # 11. Draw Bottom Spell Panel
        self._draw_spell_panel()

        # 12. Draw Game Over / Victory Overlays
        self._draw_game_state_overlay()

    def _draw_path(self) -> None:
        """Renders styled path geometry."""
        for i in range(len(self.waypoints) - 1):
            p1 = self.waypoints[i]
            p2 = self.waypoints[i + 1]
            # Outer border
            arcade.draw_line(p1.x, p1.y, p2.x, p2.y, arcade.color.DARK_BROWN, 44)
            # Inner dirt path
            arcade.draw_line(p1.x, p1.y, p2.x, p2.y, arcade.color.SAND, 32)
            arcade.draw_line(p1.x, p1.y, p2.x, p2.y, arcade.color.DIRT, 24)

        # Draw Spawn Altar
        spawn = self.waypoints[0]
        arcade.draw_circle_filled(spawn.x, spawn.y, 28, arcade.color.DARK_RED)
        arcade.draw_circle_outline(spawn.x, spawn.y, 28, arcade.color.BLACK, 3)
        arcade.draw_text("SPAWN", spawn.x - 22, spawn.y - 5, arcade.color.WHITE, 10, bold=True)

    def _draw_nest(self) -> None:
        """Renders the Dragon Nest Altar with physical egg shapes."""
        nest = self.game.nest_pos
        # Altar base
        arcade.draw_circle_filled(nest.x, nest.y, 38, arcade.color.GOLDENROD)
        arcade.draw_circle_filled(nest.x, nest.y, 32, arcade.color.GOLD)
        arcade.draw_circle_outline(nest.x, nest.y, 38, arcade.color.DARK_RED, 3)
        arcade.draw_text("DRAGON NEST", nest.x - 38, nest.y - 48, arcade.color.GOLD, 10, bold=True)

        # Draw eggs in nest
        for i in range(self.game.nest_eggs):
            angle = (i * (360 / max(1, self.game.nest_eggs))) * (math.pi / 180)
            radius = 14
            egg_x = nest.x + radius * math.cos(angle)
            egg_y = nest.y + radius * math.sin(angle)
            arcade.draw_ellipse_filled(egg_x, egg_y, 10, 14, arcade.color.WHITE)
            arcade.draw_ellipse_outline(egg_x, egg_y, 10, 14, arcade.color.GOLDENROD, 1.5)

    def _draw_pedestals(self) -> None:
        """Renders fixed dragon platforms along the path."""
        for idx, pos in enumerate(self.game.pedestals):
            is_hovered = (idx == self.hovered_pedestal_idx)
            is_selected = (idx == self.selected_pedestal_idx)

            # Check if occupied
            occupied_tower = self._get_tower_at_pedestal(idx)

            # Platform base
            base_color = arcade.color.GOLDENROD if is_selected else (arcade.color.LIGHT_GRAY if is_hovered else arcade.color.DARK_SLATE_GRAY)
            arcade.draw_circle_filled(pos.x, pos.y, 25, base_color)
            arcade.draw_circle_filled(pos.x, pos.y, 20, arcade.color.CHARCOAL)

            rim_color = arcade.color.YELLOW if (is_selected or is_hovered) else arcade.color.GOLDENROD
            arcade.draw_circle_outline(pos.x, pos.y, 25, rim_color, 3)

            if not occupied_tower:
                # Plus icon for empty pedestal
                arcade.draw_line(pos.x - 8, pos.y, pos.x + 8, pos.y, arcade.color.GRAY, 3)
                arcade.draw_line(pos.x, pos.y - 8, pos.x, pos.y + 8, arcade.color.GRAY, 3)

    def _draw_towers(self) -> None:
        """Renders dragon towers placed on pedestals."""
        for tower in self.game.towers:
            if isinstance(tower, FireDragon):
                color = arcade.color.ORANGE_RED
                symbol = "F"
            elif isinstance(tower, IceDragon):
                color = arcade.color.CYAN
                symbol = "I"
            elif isinstance(tower, PoisonDragon):
                color = arcade.color.LIME_GREEN
                symbol = "P"
            else:
                color = arcade.color.WHITE
                symbol = "D"

            # Tower Body
            arcade.draw_circle_filled(tower.pos.x, tower.pos.y, 18, color)
            arcade.draw_circle_outline(tower.pos.x, tower.pos.y, 18, arcade.color.WHITE, 2)
            arcade.draw_text(symbol, tower.pos.x - 5, tower.pos.y - 6, arcade.color.BLACK, 12, bold=True)

            # Level Badge
            arcade.draw_circle_filled(tower.pos.x + 14, tower.pos.y + 14, 8, arcade.color.GOLD)
            arcade.draw_text(str(tower.level), tower.pos.x + 11, tower.pos.y + 9, arcade.color.BLACK, 9, bold=True)

    def _draw_enemies(self) -> None:
        """Renders active enemies, health bars, and stolen eggs."""
        for enemy in self.game.enemies:
            if not enemy.is_alive:
                continue

            # Body
            color = arcade.color.CRIMSON if not enemy.follower.is_returning else arcade.color.PURPLE
            arcade.draw_circle_filled(enemy.pos.x, enemy.pos.y, 14, color)

            # Stolen egg
            if enemy.has_egg:
                arcade.draw_ellipse_filled(enemy.pos.x, enemy.pos.y - 6, 8, 12, arcade.color.GOLD)
                arcade.draw_ellipse_outline(enemy.pos.x, enemy.pos.y - 6, 8, 12, arcade.color.WHITE, 1)

            # Health bar
            hp_ratio = enemy.hp / enemy.max_hp
            bar_width = 30.0
            arcade.draw_rect_filled(
                arcade.XYWH(enemy.pos.x, enemy.pos.y + 20, bar_width, 6),
                arcade.color.BLACK
            )
            arcade.draw_rect_filled(
                arcade.XYWH(
                    enemy.pos.x - (bar_width * (1.0 - hp_ratio)) / 2.0,
                    enemy.pos.y + 20,
                    bar_width * hp_ratio,
                    4
                ),
                arcade.color.GREEN
            )

            # Status badges
            if enemy.status_manager.is_slowed:
                arcade.draw_circle_filled(enemy.pos.x - 10, enemy.pos.y + 28, 4, arcade.color.CYAN)
            if enemy.status_manager.is_poisoned:
                arcade.draw_circle_filled(enemy.pos.x + 10, enemy.pos.y + 28, 4, arcade.color.LIME_GREEN)
            if enemy.status_manager.is_frozen:
                arcade.draw_circle_filled(enemy.pos.x, enemy.pos.y + 28, 5, arcade.color.WHITE)

    def _draw_projectiles(self) -> None:
        """Renders in-flight projectiles."""
        for proj in self.game.projectiles:
            p_color = (
                arcade.color.ORANGE_RED if proj.effect_type == "fire"
                else arcade.color.CYAN if proj.effect_type == "ice"
                else arcade.color.LIME_GREEN if proj.effect_type == "poison"
                else arcade.color.YELLOW
            )
            arcade.draw_circle_filled(proj.pos.x, proj.pos.y, 6, p_color)

    def _draw_dropped_eggs(self) -> None:
        """Renders dropped eggs smoothly gliding back to the Dragon Nest."""
        for egg in self.game.dropped_eggs:
            if not egg.is_returned:
                visual_pos = egg.get_interpolated_pos(self.game.nest_pos)
                arcade.draw_ellipse_filled(visual_pos.x, visual_pos.y, 10, 14, arcade.color.GOLD)
                arcade.draw_ellipse_outline(visual_pos.x, visual_pos.y, 10, 14, arcade.color.WHITE, 1.5)

    def _draw_range_overlay(self) -> None:
        """Renders tower attack range circle ONLY when hovered or selected."""
        target_idx = self.selected_pedestal_idx if self.selected_pedestal_idx is not None else self.hovered_pedestal_idx
        if target_idx is not None:
            tower = self._get_tower_at_pedestal(target_idx)
            if tower:
                arcade.draw_circle_outline(tower.pos.x, tower.pos.y, tower.attack_range, arcade.color.WHITE, 2)
                # Subtle filled range mask
                arcade.draw_circle_filled(tower.pos.x, tower.pos.y, tower.attack_range, (255, 255, 255, 25))

    def _draw_pedestal_menu(self) -> None:
        """Renders radial modal menu for building or upgrading/selling towers."""
        if self.selected_pedestal_idx is None:
            return

        ped_pos = self.game.pedestals[self.selected_pedestal_idx]
        occupied_tower = self._get_tower_at_pedestal(self.selected_pedestal_idx)

        if not occupied_tower:
            # --- BUILD MENU (3 Dragon Options) ---
            # Background ring panel
            arcade.draw_rect_filled(arcade.XYWH(ped_pos.x, ped_pos.y - 65, 260, 50), arcade.color.CHARCOAL)
            arcade.draw_rect_outline(arcade.XYWH(ped_pos.x, ped_pos.y - 65, 260, 50), arcade.color.GOLD, 2)

            options = [
                ("1: Fire", 100, arcade.color.ORANGE_RED, ped_pos.x - 85),
                ("2: Ice", 120, arcade.color.CYAN, ped_pos.x),
                ("3: Poison", 130, arcade.color.LIME_GREEN, ped_pos.x + 85),
            ]

            for name, cost, color, bx in options:
                is_affordable = self.game.gold >= cost
                btn_color = color if is_affordable else arcade.color.GRAY
                arcade.draw_circle_filled(bx, ped_pos.y - 65, 18, btn_color)
                arcade.draw_text(name, bx - 22, ped_pos.y - 55, arcade.color.WHITE, 9, bold=True)
                arcade.draw_text(f"{cost}g", bx - 12, ped_pos.y - 82, arcade.color.GOLD, 9, bold=True)

        else:
            # --- UPGRADE / SELL MENU ---
            tower = occupied_tower
            arcade.draw_rect_filled(arcade.XYWH(ped_pos.x, ped_pos.y - 65, 220, 50), arcade.color.CHARCOAL)
            arcade.draw_rect_outline(arcade.XYWH(ped_pos.x, ped_pos.y - 65, 220, 50), arcade.color.GOLD, 2)

            # Upgrade Button
            can_upgrade = (tower.level < tower.max_level) and (self.game.gold >= tower.upgrade_cost)
            upg_color = arcade.color.GREEN if can_upgrade else arcade.color.GRAY
            arcade.draw_rect_filled(arcade.XYWH(ped_pos.x - 50, ped_pos.y - 65, 95, 36), upg_color)
            upg_text = f"UPG ({tower.upgrade_cost}g)" if tower.level < tower.max_level else "MAX LVL"
            arcade.draw_text(upg_text, ped_pos.x - 90, ped_pos.y - 70, arcade.color.WHITE, 9, bold=True)

            # Sell Button
            arcade.draw_rect_filled(arcade.XYWH(ped_pos.x + 50, ped_pos.y - 65, 80, 36), arcade.color.RED)
            arcade.draw_text(f"SELL ({tower.sell_value}g)", ped_pos.x + 15, ped_pos.y - 70, arcade.color.WHITE, 9, bold=True)

    def _draw_top_hud(self) -> None:
        """Renders standard top header status bar."""
        bar_height = 55.0
        bar_y = SCREEN_HEIGHT - bar_height / 2.0
        arcade.draw_rect_filled(arcade.XYWH(SCREEN_WIDTH / 2.0, bar_y, SCREEN_WIDTH, bar_height), arcade.color.CHARCOAL)
        arcade.draw_line(0, SCREEN_HEIGHT - bar_height, SCREEN_WIDTH, SCREEN_HEIGHT - bar_height, arcade.color.GOLD, 2)

        # Gold
        arcade.draw_circle_filled(35, bar_y, 14, arcade.color.GOLD)
        arcade.draw_text(f"Gold: {self.game.gold}", 58, bar_y - 7, arcade.color.GOLD, 14, bold=True)

        # Eggs
        arcade.draw_ellipse_filled(240, bar_y, 10, 14, arcade.color.WHITE)
        arcade.draw_text(f"Eggs: {self.game.player_eggs}/5", 258, bar_y - 7, arcade.color.WHITE, 14, bold=True)

        # Wave Progress
        spawner = self.game.wave_spawner
        wave_str = f"Wave {spawner.current_wave_index + 1}/{len(spawner.waves)}"
        arcade.draw_text(wave_str, 450, bar_y - 7, arcade.color.CYAN, 14, bold=True)

        # Score
        arcade.draw_text(f"Score: {self.game.score}", 680, bar_y - 7, arcade.color.YELLOW, 14, bold=True)

        # Instruction hint
        arcade.draw_text("Click Pedestals to build | Q, W, E Spells", 810, bar_y - 6, arcade.color.LIGHT_GRAY, 9)

    def _draw_spell_panel(self) -> None:
        """Renders bottom Dragon Spell panel with cooldown overlays."""
        panel_y = 40.0
        panel_width = 380.0
        panel_height = 55.0
        center_x = SCREEN_WIDTH / 2.0

        arcade.draw_rect_filled(arcade.XYWH(center_x, panel_y, panel_width, panel_height), arcade.color.CHARCOAL)
        arcade.draw_rect_outline(arcade.XYWH(center_x, panel_y, panel_width, panel_height), arcade.color.GOLDENROD, 2)

        spells = [
            ("fire_rain", "Fire Rain [Q]", arcade.color.ORANGE_RED, center_x - 110),
            ("ice_freeze", "Ice Freeze [W]", arcade.color.CYAN, center_x),
            ("poison_storm", "Poison Storm [E]", arcade.color.LIME_GREEN, center_x + 110),
        ]

        for key, name, color, sx in spells:
            cd = self.game.spell_cooldowns[key]
            max_cd = self.game.spell_max_cooldowns[key]

            # Card background
            card_color = color if cd == 0.0 else arcade.color.DARK_GRAY
            arcade.draw_rect_filled(arcade.XYWH(sx, panel_y, 100, 42), card_color)
            arcade.draw_rect_outline(arcade.XYWH(sx, panel_y, 100, 42), arcade.color.WHITE, 1)

            # Cooldown mask overlay
            if cd > 0.0:
                cd_ratio = cd / max_cd
                arcade.draw_rect_filled(arcade.XYWH(sx, panel_y, 100, 42 * cd_ratio), (0, 0, 0, 180))
                arcade.draw_text(f"{cd:.1f}s", sx - 16, panel_y - 6, arcade.color.YELLOW, 11, bold=True)
            else:
                arcade.draw_text(name, sx - 42, panel_y - 6, arcade.color.BLACK if color == arcade.color.CYAN else arcade.color.WHITE, 9, bold=True)

    def _draw_game_state_overlay(self) -> None:
        """Draw Game Over or Victory screens."""
        if self.game.is_game_over:
            arcade.draw_rect_filled(arcade.XYWH(SCREEN_WIDTH / 2.0, SCREEN_HEIGHT / 2.0, 400, 150), (0, 0, 0, 220))
            arcade.draw_rect_outline(arcade.XYWH(SCREEN_WIDTH / 2.0, SCREEN_HEIGHT / 2.0, 400, 150), arcade.color.RED, 3)
            arcade.draw_text("GAME OVER", SCREEN_WIDTH // 2 - 110, SCREEN_HEIGHT // 2 + 10, arcade.color.RED, 32, bold=True)
            arcade.draw_text("All Dragon Eggs were stolen!", SCREEN_WIDTH // 2 - 120, SCREEN_HEIGHT // 2 - 25, arcade.color.WHITE, 13)

        elif self.game.is_victory:
            arcade.draw_rect_filled(arcade.XYWH(SCREEN_WIDTH / 2.0, SCREEN_HEIGHT / 2.0, 400, 150), (0, 0, 0, 220))
            arcade.draw_rect_outline(arcade.XYWH(SCREEN_WIDTH / 2.0, SCREEN_HEIGHT / 2.0, 400, 150), arcade.color.GOLD, 3)
            arcade.draw_text("VICTORY!", SCREEN_WIDTH // 2 - 80, SCREEN_HEIGHT // 2 + 10, arcade.color.GOLD, 32, bold=True)
            arcade.draw_text("All Dragon Shrine eggs secured!", SCREEN_WIDTH // 2 - 120, SCREEN_HEIGHT // 2 - 25, arcade.color.WHITE, 13)

    def _get_tower_at_pedestal(self, ped_idx: int) -> Optional[DragonTower]:
        """Returns tower located at given pedestal index if any."""
        if 0 <= ped_idx < len(self.game.pedestals):
            ped_pos = self.game.pedestals[ped_idx]
            for tower in self.game.towers:
                if tower.pos.distance_to(ped_pos) < 5.0:
                    return tower
        return None

    def on_update(self, delta_time: float) -> None:
        """Update engine logic frame tick."""
        self.game.update(delta_time)

    def on_mouse_motion(self, x: float, y: float, dx: float, dy: float) -> None:
        """Track mouse movement for pedestal hovering."""
        self.mouse_pos = Vec2(x, y)
        self.hovered_pedestal_idx = None
        for idx, ped_pos in enumerate(self.game.pedestals):
            if ped_pos.distance_to(self.mouse_pos) <= 28.0:
                self.hovered_pedestal_idx = idx
                break

    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int) -> None:
        """Handles pedestal selection, building, upgrading, and selling."""
        click_pos = Vec2(x, y)

        # Check if clicked on a pedestal
        clicked_ped_idx = None
        for idx, ped_pos in enumerate(self.game.pedestals):
            if ped_pos.distance_to(click_pos) <= 28.0:
                clicked_ped_idx = idx
                break

        if clicked_ped_idx is not None:
            self.selected_pedestal_idx = clicked_ped_idx
            return

        # Handle menu button clicks if a pedestal is currently selected
        if self.selected_pedestal_idx is not None:
            ped_pos = self.game.pedestals[self.selected_pedestal_idx]
            occupied_tower = self._get_tower_at_pedestal(self.selected_pedestal_idx)

            if not occupied_tower:
                # Clicked build options
                if abs(y - (ped_pos.y - 65)) <= 25:
                    if abs(x - (ped_pos.x - 85)) <= 35:
                        self.game.add_tower(FireDragon(len(self.game.towers) + 1, ped_pos))
                    elif abs(x - ped_pos.x) <= 35:
                        self.game.add_tower(IceDragon(len(self.game.towers) + 1, ped_pos))
                    elif abs(x - (ped_pos.x + 85)) <= 35:
                        self.game.add_tower(PoisonDragon(len(self.game.towers) + 1, ped_pos))
            else:
                # Clicked Upgrade or Sell
                if abs(y - (ped_pos.y - 65)) <= 20:
                    if abs(x - (ped_pos.x - 50)) <= 45:
                        self.game.upgrade_tower(occupied_tower)
                    elif abs(x - (ped_pos.x + 50)) <= 40:
                        self.game.sell_tower(occupied_tower)

            # Deselect pedestal after action
            self.selected_pedestal_idx = None

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        """Key shortcuts for Dragon Spells (Q, W, E)."""
        if symbol == arcade.key.Q:
            self.game.cast_spell("fire_rain")
        elif symbol == arcade.key.W:
            self.game.cast_spell("ice_freeze")
        elif symbol == arcade.key.E:
            self.game.cast_spell("poison_storm")
