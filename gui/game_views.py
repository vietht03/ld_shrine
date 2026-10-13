from __future__ import annotations
import arcade
import math
from typing import Optional, List, Dict
from core.vec2 import Vec2
from core.game_manager import GameManager
from core.tower import FireDragon, IceDragon, PoisonDragon, DragonTower
from core.level_data import LevelConfig, ProgressManager, get_level_data

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
SCREEN_TITLE = "Lair Defense: Shrine - Tower Defense"


# ==============================================================================
# 1. MAIN MENU VIEW
# ==============================================================================
class MainMenuView(arcade.View):
    """
    Main Menu View featuring title graphic, dragon artwork element,
    Play button, and Quit button.
    """

    def __init__(self) -> None:
        super().__init__()
        self.mouse_pos = Vec2(0, 0)

    def on_draw(self) -> None:
        self.clear()
        arcade.set_background_color(arcade.color.DARK_SLATE_GRAY)

        # Decorative background dragon shrine altar symbol
        cx, cy = SCREEN_WIDTH / 2.0, SCREEN_HEIGHT / 2.0 + 30
        arcade.draw_circle_filled(cx, cy, 140, (30, 40, 50, 200))
        arcade.draw_circle_outline(cx, cy, 140, arcade.color.GOLD, 4)
        arcade.draw_circle_outline(cx, cy, 110, arcade.color.DARK_RED, 3)

        # Dragon Head Emblem shape
        arcade.draw_triangle_filled(cx, cy + 60, cx - 40, cy - 30, cx + 40, cy - 30, arcade.color.GOLD)
        arcade.draw_triangle_filled(cx, cy + 80, cx - 20, cy + 30, cx + 20, cy + 30, arcade.color.ORANGE_RED)

        # Game Title Header
        arcade.draw_text("LAIR DEFENSE", SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT - 120, arcade.color.GOLD, 44, bold=True)
        arcade.draw_text("S H R I N E", SCREEN_WIDTH // 2 - 90, SCREEN_HEIGHT - 165, arcade.color.FIREBRICK, 28, bold=True)
        arcade.draw_text("Protect the Sacred Dragon Eggs from Thieves!", SCREEN_WIDTH // 2 - 180, SCREEN_HEIGHT - 200, arcade.color.LIGHT_GRAY, 13)

        # Play Button
        play_rect = arcade.XYWH(cx, 160, 220, 55)
        is_play_hovered = self.mouse_pos.to_tuple() in play_rect
        play_color = arcade.color.GOLDENROD if is_play_hovered else arcade.color.DARK_RED

        arcade.draw_rect_filled(play_rect, play_color)
        arcade.draw_rect_outline(play_rect, arcade.color.GOLD, 3)
        arcade.draw_text("PLAY GAME", cx - 75, 148, arcade.color.WHITE, 20, bold=True)

        # Quit Button
        quit_rect = arcade.XYWH(cx, 85, 160, 40)
        is_quit_hovered = self.mouse_pos.to_tuple() in quit_rect
        quit_color = arcade.color.GRAY if is_quit_hovered else arcade.color.CHARCOAL

        arcade.draw_rect_filled(quit_rect, quit_color)
        arcade.draw_rect_outline(quit_rect, arcade.color.WHITE, 1.5)
        arcade.draw_text("QUIT", cx - 25, 76, arcade.color.WHITE, 14, bold=True)

    def on_mouse_motion(self, x: float, y: float, dx: float, dy: float) -> None:
        self.mouse_pos = Vec2(x, y)

    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int) -> None:
        cx = SCREEN_WIDTH / 2.0
        # Check Play Button click
        if (x, y) in arcade.XYWH(cx, 160, 220, 55):
            level_select = LevelSelectView()
            self.window.show_view(level_select)

        # Check Quit Button click
        elif (x, y) in arcade.XYWH(cx, 85, 160, 40):
            arcade.exit()


# ==============================================================================
# 2. LEVEL SELECT VIEW
# ==============================================================================
class LevelSelectView(arcade.View):
    """
    Level Selection View displaying a grid of 10 levels with status tracking.
    Levels 2-10 unlock progressively upon completing preceding levels.
    """

    def __init__(self) -> None:
        super().__init__()
        self.mouse_pos = Vec2(0, 0)
        self.progress = ProgressManager.load_progress()

    def on_draw(self) -> None:
        self.clear()
        arcade.set_background_color(arcade.color.DARK_SLATE_GRAY)

        # Refresh progress
        self.progress = ProgressManager.load_progress()
        unlocked_max = self.progress.get("unlocked_level", 1)
        completed_set = set(self.progress.get("completed_levels", []))
        high_scores = self.progress.get("high_scores", {})

        # Header Title
        arcade.draw_text("SELECT LEVEL", SCREEN_WIDTH // 2 - 140, SCREEN_HEIGHT - 70, arcade.color.GOLD, 32, bold=True)
        arcade.draw_text("Choose a stage to defend the Dragon Shrine", SCREEN_WIDTH // 2 - 160, SCREEN_HEIGHT - 100, arcade.color.LIGHT_GRAY, 12)

        # Render 10 Level Buttons in a 2x5 Grid
        cols = 5
        rows = 2
        grid_start_x = 140
        grid_start_y = SCREEN_HEIGHT - 220
        col_spacing = 180
        row_spacing = 180

        for lvl in range(1, 11):
            r = (lvl - 1) // cols
            c = (lvl - 1) % cols

            bx = grid_start_x + c * col_spacing
            by = grid_start_y - r * row_spacing
            rect = arcade.XYWH(bx, by, 140, 130)

            is_unlocked = (lvl <= unlocked_max)
            is_completed = (lvl in completed_set)
            is_hovered = (self.mouse_pos.to_tuple() in rect) and is_unlocked

            # Card background color
            if not is_unlocked:
                bg_color = (40, 40, 45)
                border_color = arcade.color.DARK_GRAY
            elif is_completed:
                bg_color = (20, 70, 30) if not is_hovered else (30, 95, 40)
                border_color = arcade.color.GOLD
            else:
                bg_color = (60, 50, 20) if not is_hovered else (90, 75, 25)
                border_color = arcade.color.YELLOW

            arcade.draw_rect_filled(rect, bg_color)
            arcade.draw_rect_outline(rect, border_color, 2.5 if is_hovered else 1.5)

            # Level Number Header
            arcade.draw_text(f"LEVEL {lvl}", bx - 45, by + 30, arcade.color.GOLD if is_unlocked else arcade.color.GRAY, 16, bold=True)

            if is_unlocked:
                lvl_config = get_level_data(lvl)
                short_name = lvl_config.name.split(":")[-1].strip()
                arcade.draw_text(short_name, bx - 60, by + 5, arcade.color.WHITE, 10, align="center", width=120)

                # Completed status badge / High score
                score = high_scores.get(str(lvl), 0)
                if is_completed:
                    arcade.draw_text("★ PASSED ★", bx - 42, by - 25, arcade.color.YELLOW, 10, bold=True)
                    arcade.draw_text(f"Score: {score}", bx - 40, by - 45, arcade.color.GOLD, 9)
                else:
                    arcade.draw_text("UNLOCKED", bx - 40, by - 35, arcade.color.GREEN, 10, bold=True)
            else:
                # Locked symbol
                arcade.draw_text("🔒 LOCKED", bx - 42, by - 15, (255, 100, 100), 12, bold=True)

        # Back to Main Menu Button
        back_rect = arcade.XYWH(SCREEN_WIDTH / 2.0, 70, 240, 45)
        is_back_hovered = self.mouse_pos.to_tuple() in back_rect
        back_color = arcade.color.DARK_RED if is_back_hovered else arcade.color.CHARCOAL

        arcade.draw_rect_filled(back_rect, back_color)
        arcade.draw_rect_outline(back_rect, arcade.color.GOLD, 2)
        arcade.draw_text("BACK TO MAIN MENU", SCREEN_WIDTH // 2 - 95, 60, arcade.color.WHITE, 13, bold=True)

    def on_mouse_motion(self, x: float, y: float, dx: float, dy: float) -> None:
        self.mouse_pos = Vec2(x, y)

    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int) -> None:
        cols = 5
        grid_start_x = 140
        grid_start_y = SCREEN_HEIGHT - 220
        col_spacing = 180
        row_spacing = 180

        unlocked_max = self.progress.get("unlocked_level", 1)

        # Check Level grid clicks
        for lvl in range(1, 11):
            r = (lvl - 1) // cols
            c = (lvl - 1) % cols
            bx = grid_start_x + c * col_spacing
            by = grid_start_y - r * row_spacing
            rect = arcade.XYWH(bx, by, 140, 130)

            if ((x, y) in rect) and lvl <= unlocked_max:
                gameplay_view = GameplayView(level_id=lvl)
                self.window.show_view(gameplay_view)
                return

        # Check Back Button click
        back_rect = arcade.XYWH(SCREEN_WIDTH / 2.0, 70, 240, 45)
        if (x, y) in back_rect:
            main_menu = MainMenuView()
            self.window.show_view(main_menu)


# ==============================================================================
# 3. GAMEPLAY VIEW
# ==============================================================================
class GameplayView(arcade.View):
    """
    Main Gameplay View. Loads level configurations, renders path, towers,
    enemies, status effects, Top HUD, Spell panel, and Pause/Victory/Game Over modals.
    """

    def __init__(self, level_id: int) -> None:
        super().__init__()
        self.level_id = level_id
        self.level_config: LevelConfig = get_level_data(level_id)

        # Initialize GameManager with level config parameters
        self.game = GameManager(
            waypoints=self.level_config.waypoints,
            starting_eggs=self.level_config.starting_eggs,
            starting_gold=self.level_config.starting_gold
        )
        self.game.pedestals = self.level_config.pedestals
        self.game.wave_spawner.waves = self.level_config.waves
        self.game.wave_spawner.start()

        self.is_paused: bool = False
        self.selected_pedestal_idx: Optional[int] = None
        self.hovered_pedestal_idx: Optional[int] = None
        self.mouse_pos: Vec2 = Vec2(0.0, 0.0)

    def on_draw(self) -> None:
        self.clear()
        arcade.set_background_color(arcade.color.DARK_SLATE_GRAY)

        # 1. Path & Nest Altar
        self._draw_path()
        self._draw_nest()

        # 2. Pedestals & Towers
        self._draw_pedestals()
        self._draw_towers()

        # 3. Enemies, Health Bars, Projectiles & Gliding Eggs
        self._draw_enemies()
        self._draw_projectiles()
        self._draw_dropped_eggs()

        # 4. Range Overlay & Build/Upgrade Pedestal Menu
        self._draw_range_overlay()
        self._draw_pedestal_menu()

        # 5. Top Header HUD & Bottom Spell Panel
        self._draw_top_hud()
        self._draw_spell_panel()

        # 6. Pause / Victory / Game Over Modals
        if self.is_paused:
            self._draw_pause_modal()
        elif self.game.is_game_over:
            self._draw_game_over_modal()
        elif self.game.is_victory:
            self._draw_victory_modal()

    def _draw_path(self) -> None:
        waypoints = self.game.waypoints
        for i in range(len(waypoints) - 1):
            p1 = waypoints[i]
            p2 = waypoints[i + 1]
            arcade.draw_line(p1.x, p1.y, p2.x, p2.y, arcade.color.DARK_BROWN, 44)
            arcade.draw_line(p1.x, p1.y, p2.x, p2.y, arcade.color.SAND, 32)
            arcade.draw_line(p1.x, p1.y, p2.x, p2.y, arcade.color.DIRT, 24)

        spawn = waypoints[0]
        arcade.draw_circle_filled(spawn.x, spawn.y, 28, arcade.color.DARK_RED)
        arcade.draw_circle_outline(spawn.x, spawn.y, 28, arcade.color.BLACK, 3)
        arcade.draw_text("SPAWN", spawn.x - 22, spawn.y - 5, arcade.color.WHITE, 10, bold=True)

    def _draw_nest(self) -> None:
        nest = self.game.nest_pos
        arcade.draw_circle_filled(nest.x, nest.y, 38, arcade.color.GOLDENROD)
        arcade.draw_circle_filled(nest.x, nest.y, 32, arcade.color.GOLD)
        arcade.draw_circle_outline(nest.x, nest.y, 38, arcade.color.DARK_RED, 3)
        arcade.draw_text("DRAGON NEST", nest.x - 38, nest.y - 48, arcade.color.GOLD, 10, bold=True)

        for i in range(self.game.nest_eggs):
            angle = (i * (360 / max(1, self.game.nest_eggs))) * (math.pi / 180)
            radius = 14
            egg_x = nest.x + radius * math.cos(angle)
            egg_y = nest.y + radius * math.sin(angle)
            arcade.draw_ellipse_filled(egg_x, egg_y, 10, 14, arcade.color.WHITE)
            arcade.draw_ellipse_outline(egg_x, egg_y, 10, 14, arcade.color.GOLDENROD, 1.5)

    def _draw_pedestals(self) -> None:
        for idx, pos in enumerate(self.game.pedestals):
            is_hovered = (idx == self.hovered_pedestal_idx)
            is_selected = (idx == self.selected_pedestal_idx)
            occupied_tower = self._get_tower_at_pedestal(idx)

            base_color = arcade.color.GOLDENROD if is_selected else (arcade.color.LIGHT_GRAY if is_hovered else arcade.color.DARK_SLATE_GRAY)
            arcade.draw_circle_filled(pos.x, pos.y, 25, base_color)
            arcade.draw_circle_filled(pos.x, pos.y, 20, arcade.color.CHARCOAL)

            rim_color = arcade.color.YELLOW if (is_selected or is_hovered) else arcade.color.GOLDENROD
            arcade.draw_circle_outline(pos.x, pos.y, 25, rim_color, 3)

            if not occupied_tower:
                arcade.draw_line(pos.x - 8, pos.y, pos.x + 8, pos.y, arcade.color.GRAY, 3)
                arcade.draw_line(pos.x, pos.y - 8, pos.x, pos.y + 8, arcade.color.GRAY, 3)

    def _draw_towers(self) -> None:
        for tower in self.game.towers:
            if isinstance(tower, FireDragon):
                color, symbol = arcade.color.ORANGE_RED, "F"
            elif isinstance(tower, IceDragon):
                color, symbol = arcade.color.CYAN, "I"
            elif isinstance(tower, PoisonDragon):
                color, symbol = arcade.color.LIME_GREEN, "P"
            else:
                color, symbol = arcade.color.WHITE, "D"

            arcade.draw_circle_filled(tower.pos.x, tower.pos.y, 18, color)
            arcade.draw_circle_outline(tower.pos.x, tower.pos.y, 18, arcade.color.WHITE, 2)
            arcade.draw_text(symbol, tower.pos.x - 5, tower.pos.y - 6, arcade.color.BLACK, 12, bold=True)

            arcade.draw_circle_filled(tower.pos.x + 14, tower.pos.y + 14, 8, arcade.color.GOLD)
            arcade.draw_text(str(tower.level), tower.pos.x + 11, tower.pos.y + 9, arcade.color.BLACK, 9, bold=True)

    def _draw_enemies(self) -> None:
        for enemy in self.game.enemies:
            if not enemy.is_alive:
                continue

            color = arcade.color.CRIMSON if not enemy.follower.is_returning else arcade.color.PURPLE
            arcade.draw_circle_filled(enemy.pos.x, enemy.pos.y, 14, color)

            if enemy.has_egg:
                arcade.draw_ellipse_filled(enemy.pos.x, enemy.pos.y - 6, 8, 12, arcade.color.GOLD)

            hp_ratio = enemy.hp / enemy.max_hp
            bar_width = 30.0
            arcade.draw_rect_filled(arcade.XYWH(enemy.pos.x, enemy.pos.y + 20, bar_width, 6), arcade.color.BLACK)
            arcade.draw_rect_filled(
                arcade.XYWH(enemy.pos.x - (bar_width * (1.0 - hp_ratio)) / 2.0, enemy.pos.y + 20, bar_width * hp_ratio, 4),
                arcade.color.GREEN
            )

            if enemy.status_manager.is_slowed:
                arcade.draw_circle_filled(enemy.pos.x - 10, enemy.pos.y + 28, 4, arcade.color.CYAN)
            if enemy.status_manager.is_poisoned:
                arcade.draw_circle_filled(enemy.pos.x + 10, enemy.pos.y + 28, 4, arcade.color.LIME_GREEN)
            if enemy.status_manager.is_frozen:
                arcade.draw_circle_filled(enemy.pos.x, enemy.pos.y + 28, 5, arcade.color.WHITE)

    def _draw_projectiles(self) -> None:
        for proj in self.game.projectiles:
            p_color = (
                arcade.color.ORANGE_RED if proj.effect_type == "fire"
                else arcade.color.CYAN if proj.effect_type == "ice"
                else arcade.color.LIME_GREEN if proj.effect_type == "poison"
                else arcade.color.YELLOW
            )
            arcade.draw_circle_filled(proj.pos.x, proj.pos.y, 6, p_color)

    def _draw_dropped_eggs(self) -> None:
        for egg in self.game.dropped_eggs:
            if not egg.is_returned:
                visual_pos = egg.get_interpolated_pos(self.game.nest_pos)
                arcade.draw_ellipse_filled(visual_pos.x, visual_pos.y, 10, 14, arcade.color.GOLD)
                arcade.draw_ellipse_outline(visual_pos.x, visual_pos.y, 10, 14, arcade.color.WHITE, 1.5)

    def _draw_range_overlay(self) -> None:
        target_idx = self.selected_pedestal_idx if self.selected_pedestal_idx is not None else self.hovered_pedestal_idx
        if target_idx is not None:
            tower = self._get_tower_at_pedestal(target_idx)
            if tower:
                arcade.draw_circle_outline(tower.pos.x, tower.pos.y, tower.attack_range, arcade.color.WHITE, 2)
                arcade.draw_circle_filled(tower.pos.x, tower.pos.y, tower.attack_range, (255, 255, 255, 25))

    def _draw_pedestal_menu(self) -> None:
        if self.selected_pedestal_idx is None:
            return

        ped_pos = self.game.pedestals[self.selected_pedestal_idx]
        occupied_tower = self._get_tower_at_pedestal(self.selected_pedestal_idx)

        if not occupied_tower:
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
            tower = occupied_tower
            arcade.draw_rect_filled(arcade.XYWH(ped_pos.x, ped_pos.y - 65, 220, 50), arcade.color.CHARCOAL)
            arcade.draw_rect_outline(arcade.XYWH(ped_pos.x, ped_pos.y - 65, 220, 50), arcade.color.GOLD, 2)

            can_upgrade = (tower.level < tower.max_level) and (self.game.gold >= tower.upgrade_cost)
            upg_color = arcade.color.GREEN if can_upgrade else arcade.color.GRAY
            arcade.draw_rect_filled(arcade.XYWH(ped_pos.x - 50, ped_pos.y - 65, 95, 36), upg_color)
            upg_text = f"UPG ({tower.upgrade_cost}g)" if tower.level < tower.max_level else "MAX LVL"
            arcade.draw_text(upg_text, ped_pos.x - 90, ped_pos.y - 70, arcade.color.WHITE, 9, bold=True)

            arcade.draw_rect_filled(arcade.XYWH(ped_pos.x + 50, ped_pos.y - 65, 80, 36), arcade.color.RED)
            arcade.draw_text(f"SELL ({tower.sell_value}g)", ped_pos.x + 15, ped_pos.y - 70, arcade.color.WHITE, 9, bold=True)

    def _draw_top_hud(self) -> None:
        bar_height = 55.0
        bar_y = SCREEN_HEIGHT - bar_height / 2.0
        arcade.draw_rect_filled(arcade.XYWH(SCREEN_WIDTH / 2.0, bar_y, SCREEN_WIDTH, bar_height), arcade.color.CHARCOAL)
        arcade.draw_line(0, SCREEN_HEIGHT - bar_height, SCREEN_WIDTH, SCREEN_HEIGHT - bar_height, arcade.color.GOLD, 2)

        # Level Name
        arcade.draw_text(self.level_config.name, 15, bar_y - 7, arcade.color.GOLD, 14, bold=True)

        # Gold
        arcade.draw_circle_filled(230, bar_y, 12, arcade.color.GOLD)
        arcade.draw_text(f"Gold: {self.game.gold}", 248, bar_y - 7, arcade.color.GOLD, 13, bold=True)

        # Eggs
        arcade.draw_ellipse_filled(390, bar_y, 10, 14, arcade.color.WHITE)
        arcade.draw_text(f"Eggs: {self.game.player_eggs}/5", 408, bar_y - 7, arcade.color.WHITE, 13, bold=True)

        # Wave
        spawner = self.game.wave_spawner
        arcade.draw_text(f"Wave {spawner.current_wave_index + 1}/{len(spawner.waves)}", 560, bar_y - 7, arcade.color.CYAN, 13, bold=True)

        # Score
        arcade.draw_text(f"Score: {self.game.score}", 720, bar_y - 7, arcade.color.YELLOW, 13, bold=True)

        # Pause Button
        pause_rect = arcade.XYWH(940, bar_y, 75, 34)
        is_pause_hovered = self.mouse_pos.to_tuple() in pause_rect
        p_color = arcade.color.ORANGE_RED if is_pause_hovered else arcade.color.DARK_RED

        arcade.draw_rect_filled(pause_rect, p_color)
        arcade.draw_rect_outline(pause_rect, arcade.color.WHITE, 1.5)
        arcade.draw_text("PAUSE", 915, bar_y - 6, arcade.color.WHITE, 10, bold=True)

    def _draw_spell_panel(self) -> None:
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

            card_color = color if cd == 0.0 else arcade.color.DARK_GRAY
            arcade.draw_rect_filled(arcade.XYWH(sx, panel_y, 100, 42), card_color)
            arcade.draw_rect_outline(arcade.XYWH(sx, panel_y, 100, 42), arcade.color.WHITE, 1)

            if cd > 0.0:
                cd_ratio = cd / max_cd
                arcade.draw_rect_filled(arcade.XYWH(sx, panel_y, 100, 42 * cd_ratio), (0, 0, 0, 180))
                arcade.draw_text(f"{cd:.1f}s", sx - 16, panel_y - 6, arcade.color.YELLOW, 11, bold=True)
            else:
                arcade.draw_text(name, sx - 42, panel_y - 6, arcade.color.BLACK if color == arcade.color.CYAN else arcade.color.WHITE, 9, bold=True)

    # --- MODAL OVERLAYS ---
    def _draw_pause_modal(self) -> None:
        cx, cy = SCREEN_WIDTH / 2.0, SCREEN_HEIGHT / 2.0
        arcade.draw_rect_filled(arcade.XYWH(cx, cy, 320, 260), (0, 0, 0, 230))
        arcade.draw_rect_outline(arcade.XYWH(cx, cy, 320, 260), arcade.color.GOLD, 3)

        arcade.draw_text("GAME PAUSED", cx - 95, cy + 80, arcade.color.GOLD, 20, bold=True)

        buttons = [
            ("RESUME", cy + 30, arcade.color.GREEN),
            ("RESTART", cy - 15, arcade.color.ORANGE),
            ("SELECT LEVEL", cy - 60, arcade.color.DARK_RED),
        ]

        for text, by, color in buttons:
            rect = arcade.XYWH(cx, by, 180, 36)
            is_h = self.mouse_pos.to_tuple() in rect
            arcade.draw_rect_filled(rect, color if is_h else arcade.color.CHARCOAL)
            arcade.draw_rect_outline(rect, color, 2)
            arcade.draw_text(text, cx - 45, by - 6, arcade.color.WHITE, 11, bold=True)

    def _draw_victory_modal(self) -> None:
        # Save progression
        ProgressManager.unlock_next_level(self.level_id, self.game.score)

        cx, cy = SCREEN_WIDTH / 2.0, SCREEN_HEIGHT / 2.0
        arcade.draw_rect_filled(arcade.XYWH(cx, cy, 380, 280), (0, 0, 0, 235))
        arcade.draw_rect_outline(arcade.XYWH(cx, cy, 380, 280), arcade.color.GOLD, 3.5)

        arcade.draw_text("VICTORY!", cx - 80, cy + 90, arcade.color.GOLD, 28, bold=True)
        arcade.draw_text("All Dragon Shrine Eggs Secured!", cx - 120, cy + 60, arcade.color.WHITE, 12)
        arcade.draw_text(f"Final Score: {self.game.score}", cx - 60, cy + 30, arcade.color.YELLOW, 13, bold=True)

        buttons = []
        if self.level_id < 10:
            buttons.append(("NEXT LEVEL", cy - 15, arcade.color.GREEN))
            buttons.append(("SELECT LEVEL", cy - 65, arcade.color.DARK_RED))
        else:
            buttons.append(("CONGRATS! ALL LEVELS CLEARED", cy - 15, arcade.color.GOLD))
            buttons.append(("SELECT LEVEL", cy - 65, arcade.color.DARK_RED))

        for text, by, color in buttons:
            rect = arcade.XYWH(cx, by, 240, 38)
            is_h = self.mouse_pos.to_tuple() in rect
            arcade.draw_rect_filled(rect, color if is_h else arcade.color.CHARCOAL)
            arcade.draw_rect_outline(rect, color, 2)
            arcade.draw_text(text, cx - 85, by - 6, arcade.color.WHITE, 11, bold=True)

    def _draw_game_over_modal(self) -> None:
        cx, cy = SCREEN_WIDTH / 2.0, SCREEN_HEIGHT / 2.0
        arcade.draw_rect_filled(arcade.XYWH(cx, cy, 360, 260), (0, 0, 0, 235))
        arcade.draw_rect_outline(arcade.XYWH(cx, cy, 360, 260), arcade.color.RED, 3.5)

        arcade.draw_text("DEFEAT!", cx - 70, cy + 80, arcade.color.RED, 28, bold=True)
        arcade.draw_text("All Dragon Eggs Were Stolen!", cx - 110, cy + 48, arcade.color.WHITE, 12)

        buttons = [
            ("RETRY LEVEL", cy - 10, arcade.color.ORANGE),
            ("SELECT LEVEL", cy - 60, arcade.color.DARK_RED),
        ]

        for text, by, color in buttons:
            rect = arcade.XYWH(cx, by, 200, 38)
            is_h = self.mouse_pos.to_tuple() in rect
            arcade.draw_rect_filled(rect, color if is_h else arcade.color.CHARCOAL)
            arcade.draw_rect_outline(rect, color, 2)
            arcade.draw_text(text, cx - 60, by - 6, arcade.color.WHITE, 11, bold=True)

    def _get_tower_at_pedestal(self, ped_idx: int) -> Optional[DragonTower]:
        if 0 <= ped_idx < len(self.game.pedestals):
            ped_pos = self.game.pedestals[ped_idx]
            for tower in self.game.towers:
                if tower.pos.distance_to(ped_pos) < 5.0:
                    return tower
        return None

    def on_update(self, delta_time: float) -> None:
        if not self.is_paused and not self.game.is_game_over and not self.game.is_victory:
            self.game.update(delta_time)

    def on_mouse_motion(self, x: float, y: float, dx: float, dy: float) -> None:
        self.mouse_pos = Vec2(x, y)
        self.hovered_pedestal_idx = None
        for idx, ped_pos in enumerate(self.game.pedestals):
            if ped_pos.distance_to(self.mouse_pos) <= 28.0:
                self.hovered_pedestal_idx = idx
                break

    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int) -> None:
        click_pos = Vec2(x, y)
        cx, cy = SCREEN_WIDTH / 2.0, SCREEN_HEIGHT / 2.0

        # 1. Handle Pause Modal interactions
        if self.is_paused:
            if (x, y) in arcade.XYWH(cx, cy + 30, 180, 36):
                self.is_paused = False  # Resume
            elif (x, y) in arcade.XYWH(cx, cy - 15, 180, 36):
                self.window.show_view(GameplayView(self.level_id))  # Restart
            elif (x, y) in arcade.XYWH(cx, cy - 60, 180, 36):
                self.window.show_view(LevelSelectView())  # Level Select
            return

        # 2. Handle Victory Modal interactions
        if self.game.is_victory:
            if self.level_id < 10 and ((x, y) in arcade.XYWH(cx, cy - 15, 240, 38)):
                self.window.show_view(GameplayView(self.level_id + 1))  # Next Level
            elif (x, y) in arcade.XYWH(cx, cy - 65, 240, 38):
                self.window.show_view(LevelSelectView())  # Level Select
            return

        # 3. Handle Game Over Modal interactions
        if self.game.is_game_over:
            if (x, y) in arcade.XYWH(cx, cy - 10, 200, 38):
                self.window.show_view(GameplayView(self.level_id))  # Retry
            elif (x, y) in arcade.XYWH(cx, cy - 60, 200, 38):
                self.window.show_view(LevelSelectView())  # Level Select
            return

        # 4. Check Header Pause Button click
        bar_y = SCREEN_HEIGHT - 55.0 / 2.0
        if (x, y) in arcade.XYWH(940, bar_y, 75, 34):
            self.is_paused = True
            return

        # 5. Check Pedestal selection & building
        clicked_ped_idx = None
        for idx, ped_pos in enumerate(self.game.pedestals):
            if ped_pos.distance_to(click_pos) <= 28.0:
                clicked_ped_idx = idx
                break

        if clicked_ped_idx is not None:
            self.selected_pedestal_idx = clicked_ped_idx
            return

        # 6. Handle Build / Upgrade / Sell Ring Menu action clicks
        if self.selected_pedestal_idx is not None:
            ped_pos = self.game.pedestals[self.selected_pedestal_idx]
            occupied_tower = self._get_tower_at_pedestal(self.selected_pedestal_idx)

            if not occupied_tower:
                if abs(y - (ped_pos.y - 65)) <= 25:
                    if abs(x - (ped_pos.x - 85)) <= 35:
                        self.game.add_tower(FireDragon(len(self.game.towers) + 1, ped_pos))
                    elif abs(x - ped_pos.x) <= 35:
                        self.game.add_tower(IceDragon(len(self.game.towers) + 1, ped_pos))
                    elif abs(x - (ped_pos.x + 85)) <= 35:
                        self.game.add_tower(PoisonDragon(len(self.game.towers) + 1, ped_pos))
            else:
                if abs(y - (ped_pos.y - 65)) <= 20:
                    if abs(x - (ped_pos.x - 50)) <= 45:
                        self.game.upgrade_tower(occupied_tower)
                    elif abs(x - (ped_pos.x + 50)) <= 40:
                        self.game.sell_tower(occupied_tower)

            self.selected_pedestal_idx = None

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        if symbol in (arcade.key.ESCAPE, arcade.key.P):
            self.is_paused = not self.is_paused
        elif not self.is_paused:
            if symbol == arcade.key.Q:
                self.game.cast_spell("fire_rain")
            elif symbol == arcade.key.W:
                self.game.cast_spell("ice_freeze")
            elif symbol == arcade.key.E:
                self.game.cast_spell("poison_storm")
