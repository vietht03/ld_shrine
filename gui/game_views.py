from __future__ import annotations
import arcade
import math
from typing import Optional, List, Dict, Tuple
from core.vec2 import Vec2
from core.game_manager import GameManager
from core.tower import FireDragon, IceDragon, PoisonDragon, DragonTower
from core.level_data import LevelConfig, ProgressManager, get_level_data

SCREEN_WIDTH  = 1000
SCREEN_HEIGHT = 700
SCREEN_TITLE  = "Lair Defense: Shrine - Tower Defense"

# ──────────────────────────────────────────────────────────────────────
# Layout constants
# ──────────────────────────────────────────────────────────────────────
TOP_HUD_H   = 58      # Top bar height
BOT_PANEL_H = 110     # Bottom panel height (shop + spell bar)
PLAY_TOP    = SCREEN_HEIGHT - TOP_HUD_H   # y where play area starts
PLAY_BOT    = BOT_PANEL_H                 # y where play area ends
PLAY_H      = PLAY_TOP - PLAY_BOT        # usable game height

# Dragon shop card layout (left section of bottom panel)
CARD_W, CARD_H = 130, 90
CARD_GAP = 8

# Dragon definitions for shop panel
DRAGON_CATALOG = [
    dict(key="fire",   label="Fire Dragon",   sublabel="AoE · Đốt cháy",  gold=120, ruby=0,  symbol="🔥", color=(230,100,20),  cls=FireDragon,   tip="Lv3: burn DoT"),
    dict(key="ice",    label="Ice Dragon",    sublabel="Làm chậm · Đóng băng", gold=140, ruby=1, symbol="❄", color=(60,190,240), cls=IceDragon,   tip="Lv3: full freeze"),
    dict(key="poison", label="Poison Dragon", sublabel="DoT · Làm choáng", gold=130, ruby=1, symbol="☠", color=(100,210,80),  cls=PoisonDragon, tip="Lv3: 30% stun"),
]

# Tower visual metadata
TOWER_META: Dict[type, Dict] = {
    FireDragon:   dict(body=(230,100,20),  glow=(255,200,80,70),  label="F"),
    IceDragon:    dict(body=(60,190,240),  glow=(150,240,255,70), label="I"),
    PoisonDragon: dict(body=(100,210,80),  glow=(180,255,140,70), label="P"),
}

PROJ_COLORS: Dict[str, tuple] = {
    "fire":      (255,120,30),
    "fire_ray":  (255,180,50),
    "fire_aura": (255,60,0),
    "fire_nova": (255,80,0),
    "ice":       (100,220,255),
    "freeze":    (200,240,255),
    "poison":    (130,255,90),
    "fireball":  (255,60,0),
}


def _lerp_color(c1: tuple, c2: tuple, t: float) -> tuple:
    return tuple(int(a + (b-a)*t) for a,b in zip(c1,c2))


# ======================================================================
# 1. MAIN MENU VIEW
# ======================================================================
class MainMenuView(arcade.View):
    def __init__(self) -> None:
        super().__init__()
        self.mouse_pos = Vec2(0, 0)
        self.anim_t: float = 0.0

    def on_update(self, dt: float) -> None:
        self.anim_t += dt

    def on_draw(self) -> None:
        self.clear()
        arcade.set_background_color((12, 18, 24))

        cx, cy = SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2

        # Animated shrine rings
        for ring in range(5):
            r = 90 + ring * 28
            pulse = abs(math.sin(self.anim_t * 0.8 + ring * 0.6))
            alpha = int(40 + 60 * pulse)
            color = (200, 160, 30, alpha)
            arcade.draw_circle_outline(cx, cy + 20, r, color, 2)

        # Dragon emblem
        arcade.draw_circle_filled(cx, cy + 20, 85, (22, 30, 38))
        arcade.draw_circle_outline(cx, cy + 20, 85, (200, 150, 20), 3)
        arcade.draw_triangle_filled(cx, cy+75, cx-40, cy-15, cx+40, cy-15, (220,120,20))
        arcade.draw_triangle_filled(cx, cy+90, cx-20, cy+35, cx+20, cy+35, (200,60,10))

        # Title
        arcade.draw_text("LAIR  DEFENSE",    cx-230, cy+150, (255,210,40), 46, bold=True)
        arcade.draw_text("S H R I N E",       cx-100, cy+105, (180,40,40),  30, bold=True)
        arcade.draw_text("Bảo vệ trứng rồng thiêng khỏi những tên trộm!", cx-210, cy+78, (170,170,170), 12)

        # Buttons
        for label, by, base_c, hover_c in [
            ("CHƠI GAME",     cy-55, (160,20,20), (220,60,30)),
            ("THOÁT",         cy-115, (40,40,50),  (80,80,90)),
        ]:
            rect = arcade.XYWH(cx, by, 220, 48)
            hovered = self.mouse_pos.to_tuple() in rect
            arcade.draw_rect_filled(rect, hover_c if hovered else base_c)
            arcade.draw_rect_outline(rect, (220,180,30) if hovered else (100,80,20), 2)
            arcade.draw_text(label, cx-55, by-8, (255,255,255), 15, bold=True)

    def on_mouse_motion(self, x, y, dx, dy):
        self.mouse_pos = Vec2(x, y)

    def on_mouse_press(self, x, y, button, modifiers):
        cx = SCREEN_WIDTH / 2
        cy = SCREEN_HEIGHT / 2
        if (x,y) in arcade.XYWH(cx, cy-55, 220, 48):
            self.window.show_view(LevelSelectView())
        elif (x,y) in arcade.XYWH(cx, cy-115, 220, 48):
            arcade.exit()


# ======================================================================
# 2. LEVEL SELECT VIEW
# ======================================================================
class LevelSelectView(arcade.View):
    def __init__(self) -> None:
        super().__init__()
        self.mouse_pos = Vec2(0, 0)
        self.progress = ProgressManager.load_progress()

    def on_draw(self) -> None:
        self.clear()
        arcade.set_background_color((14, 20, 28))
        self.progress = ProgressManager.load_progress()
        unlocked_max  = self.progress.get("unlocked_level", 1)
        completed_set = set(self.progress.get("completed_levels", []))
        high_scores   = self.progress.get("high_scores", {})

        arcade.draw_text("CHỌN MÀN CHƠI", SCREEN_WIDTH//2-160, SCREEN_HEIGHT-68, (220,180,30), 32, bold=True)
        arcade.draw_text("Bảo vệ đền rồng thiêng – chọn giai đoạn để bắt đầu", SCREEN_WIDTH//2-200, SCREEN_HEIGHT-95, (150,150,160), 12)

        cols, col_spacing = 5, 180
        grid_start_x, grid_start_y = 140, SCREEN_HEIGHT-200
        row_spacing = 170

        for lvl in range(1, 11):
            r = (lvl-1)//cols
            c = (lvl-1)%cols
            bx = grid_start_x + c*col_spacing
            by = grid_start_y - r*row_spacing
            rect = arcade.XYWH(bx, by, 148, 128)

            is_unlocked  = lvl <= unlocked_max
            is_completed = lvl in completed_set
            is_hovered   = (self.mouse_pos.to_tuple() in rect) and is_unlocked

            if not is_unlocked:
                bg, border = (28,32,38), (60,60,70)
            elif is_completed:
                bg     = (18,65,30) if not is_hovered else (24,85,38)
                border = (200,160,30)
            else:
                bg     = (55,45,15) if not is_hovered else (80,65,20)
                border = (200,200,30)

            arcade.draw_rect_filled(rect, bg)
            arcade.draw_rect_outline(rect, border, 2.5 if is_hovered else 1.5)
            arcade.draw_text(f"LVL {lvl}", bx-40, by+30, (220,180,30) if is_unlocked else (90,90,90), 16, bold=True)

            if is_unlocked:
                cfg = get_level_data(lvl)
                short = cfg.name.split(":")[-1].strip()
                arcade.draw_text(short, bx-60, by+6, (220,220,220), 9, align="center", width=120)
                score = high_scores.get(str(lvl), 0)
                if is_completed:
                    arcade.draw_text("★ HOÀN THÀNH", bx-52, by-24, (255,220,30), 9, bold=True)
                    arcade.draw_text(f"Score:{score}", bx-38, by-42, (200,170,30), 8)
                else:
                    arcade.draw_text("MỞ KHÓA", bx-34, by-32, (60,200,80), 10, bold=True)
            else:
                arcade.draw_text("🔒 KHÓA", bx-32, by-14, (200,80,80), 11, bold=True)

        back_rect = arcade.XYWH(SCREEN_WIDTH//2, 55, 240, 42)
        back_hov  = self.mouse_pos.to_tuple() in back_rect
        arcade.draw_rect_filled(back_rect, (140,20,20) if back_hov else (40,40,50))
        arcade.draw_rect_outline(back_rect, (220,180,30), 2)
        arcade.draw_text("← MENU CHÍNH", SCREEN_WIDTH//2-70, 46, (255,255,255), 13, bold=True)

    def on_mouse_motion(self, x, y, dx, dy):
        self.mouse_pos = Vec2(x, y)

    def on_mouse_press(self, x, y, button, modifiers):
        unlocked_max = self.progress.get("unlocked_level", 1)
        cols, col_spacing = 5, 180
        gsx, gsy, rsp = 140, SCREEN_HEIGHT-200, 170
        for lvl in range(1, 11):
            r = (lvl-1)//cols; c = (lvl-1)%cols
            bx = gsx + c*col_spacing; by = gsy - r*rsp
            if (x,y) in arcade.XYWH(bx, by, 148, 128) and lvl <= unlocked_max:
                self.window.show_view(GameplayView(level_id=lvl)); return
        if (x,y) in arcade.XYWH(SCREEN_WIDTH//2, 55, 240, 42):
            self.window.show_view(MainMenuView())


# ======================================================================
# 3. GAMEPLAY VIEW
# ======================================================================
class GameplayView(arcade.View):
    """
    Full gameplay screen featuring:
    - Drag-and-drop dragon shop (bottom left)
    - Spell bar with Fireball / Frost Blast (bottom right)
    - Mana bar, Ruby counter, Gold, Eggs in top HUD
    - Speed x1/x2/x3 buttons
    - Tower upgrade / sell popup
    - Spell targeting mode (click to aim Fireball)
    """

    def __init__(self, level_id: int) -> None:
        super().__init__()
        self.level_id = level_id
        self.level_config: LevelConfig = get_level_data(level_id)

        self.game = GameManager(
            waypoints=self.level_config.waypoints,
            starting_eggs=self.level_config.starting_eggs,
            starting_gold=self.level_config.starting_gold,
        )
        self.game.pedestals = self.level_config.pedestals
        self.game.wave_spawner.waves = self.level_config.waves
        self.game.wave_spawner.start()

        self.is_paused: bool = False
        self.mouse_pos: Vec2 = Vec2(0, 0)

        # Pedestal interaction
        self.selected_ped_idx: Optional[int] = None
        self.hovered_ped_idx:  Optional[int] = None

        # Drag state
        self.dragging_key:  Optional[str] = None
        self.drag_pos:      Vec2 = Vec2(0, 0)

        # Spell targeting
        self.spell_targeting: Optional[str] = None   # "fireball" when aiming

        # Shop scroll offset (future use)
        self.anim_t: float = 0.0

    # ──────────────────────────────────────────────────────────────────
    # UPDATE
    # ──────────────────────────────────────────────────────────────────
    def on_update(self, dt: float) -> None:
        self.anim_t += dt
        if not self.is_paused and not self.game.is_game_over and not self.game.is_victory:
            self.game.update(dt)

    # ──────────────────────────────────────────────────────────────────
    # MAIN DRAW
    # ──────────────────────────────────────────────────────────────────
    def on_draw(self) -> None:
        self.clear()
        arcade.set_background_color((16, 26, 22))

        self._draw_path()
        self._draw_nest()
        self._draw_spell_effects()
        self._draw_pedestals()
        self._draw_towers()
        self._draw_enemies()
        self._draw_projectiles()
        self._draw_dropped_eggs()
        self._draw_range_overlay()
        self._draw_upgrade_menu()

        self._draw_top_hud()
        self._draw_bottom_panel()

        if self.dragging_key:
            self._draw_drag_ghost()

        # Spell targeting crosshair
        if self.spell_targeting == "fireball":
            self._draw_fireball_aim()

        if self.is_paused:
            self._draw_pause_modal()
        elif self.game.is_game_over:
            self._draw_game_over_modal()
        elif self.game.is_victory:
            self._draw_victory_modal()

    # ──────────────────────────────────────────────────────────────────
    # PATH / NEST
    # ──────────────────────────────────────────────────────────────────
    def _world_y(self, y: float) -> float:
        """Convert game-logic y (based from 0) to screen y (offset by bottom panel)."""
        return y + BOT_PANEL_H

    def _draw_path(self) -> None:
        wps = self.game.waypoints
        for i in range(len(wps)-1):
            p1, p2 = wps[i], wps[i+1]
            y1, y2 = self._world_y(p1.y), self._world_y(p2.y)
            arcade.draw_line(p1.x, y1, p2.x, y2, (60,42,22), 46)
            arcade.draw_line(p1.x, y1, p2.x, y2, (140,100,55), 30)
            arcade.draw_line(p1.x, y1, p2.x, y2, (170,125,70), 20)

        sp = wps[0]; sy = self._world_y(sp.y)
        arcade.draw_circle_filled(sp.x, sy, 28, (150,20,20))
        arcade.draw_circle_outline(sp.x, sy, 28, (0,0,0), 3)
        arcade.draw_text("SPAWN", sp.x-24, sy-6, (255,255,255), 9, bold=True)

    def _draw_nest(self) -> None:
        n = self.game.nest_pos; ny = self._world_y(n.y)
        arcade.draw_circle_filled(n.x, ny, 40, (160,120,10))
        arcade.draw_circle_filled(n.x, ny, 33, (220,180,30))
        arcade.draw_circle_outline(n.x, ny, 40, (180,40,20), 3)
        arcade.draw_text("DRAGON NEST", n.x-42, ny-52, (220,180,30), 9, bold=True)
        for i in range(self.game.nest_eggs):
            a = (i*(360/max(1, self.game.nest_eggs)))*(math.pi/180)
            ex, ey = n.x+15*math.cos(a), ny+15*math.sin(a)
            arcade.draw_ellipse_filled(ex, ey, 10, 14, (255,255,255))
            arcade.draw_ellipse_outline(ex, ey, 10, 14, (220,180,30), 1.5)

    # ──────────────────────────────────────────────────────────────────
    # SPELL VISUALS
    # ──────────────────────────────────────────────────────────────────
    def _draw_spell_effects(self) -> None:
        for eff in self.game.spell_effects:
            t = eff["timer"]
            if eff["type"] == "fireball":
                alpha = int(min(255, t * 400))
                ey = self._world_y(eff["pos"].y)
                arcade.draw_circle_filled(eff["pos"].x, ey, eff["radius"], (255,100,20,alpha))
                arcade.draw_circle_outline(eff["pos"].x, ey, eff["radius"], (255,200,50,alpha), 3)
            elif eff["type"] == "frost_blast":
                alpha = int(min(220, t * 280))
                arcade.draw_rect_filled(
                    arcade.XYWH(SCREEN_WIDTH//2, SCREEN_HEIGHT//2, SCREEN_WIDTH, SCREEN_HEIGHT),
                    (100, 200, 255, alpha)
                )
            elif eff["type"] == "fire_aura":
                # Vòng nova lửa 360° — mở rộng dần, mờ dần
                ratio = 1.0 - (t / 0.35)   # 0→1 khi effect kết thúc
                r = eff["radius"] * (0.4 + 0.6 * ratio)  # bán kính nở dần
                alpha = int(255 * (1.0 - ratio))
                ey = self._world_y(eff["pos"].y)
                # Vòng lửa ngoài
                arcade.draw_circle_filled(eff["pos"].x, ey, r, (255, 80, 10, min(180, alpha)))
                arcade.draw_circle_outline(eff["pos"].x, ey, r, (255, 220, 50, alpha), 4)
                # Vòng lửa trong (nhỏ hơn, sáng hơn)
                arcade.draw_circle_filled(eff["pos"].x, ey, r * 0.55, (255, 180, 50, min(120, alpha)))

    # ──────────────────────────────────────────────────────────────────
    # PEDESTALS & TOWERS
    # ──────────────────────────────────────────────────────────────────
    def _draw_pedestals(self) -> None:
        for idx, pos in enumerate(self.game.pedestals):
            py = self._world_y(pos.y)
            sel  = idx == self.selected_ped_idx
            hov  = idx == self.hovered_ped_idx
            occ  = self._tower_at(idx)

            # Drag-hover highlight
            drag_near = False
            if self.dragging_key:
                dist = math.hypot(self.drag_pos.x - pos.x, self.drag_pos.y - py)
                drag_near = dist <= 38

            ring_c  = (255,220,30) if (sel or drag_near) else ((200,200,200) if hov else (120,100,40))
            fill_c  = (55,50,30) if occ else (30,35,28)
            outline = 3.5 if (sel or drag_near or hov) else 2

            arcade.draw_circle_filled(pos.x, py, 26, fill_c)
            arcade.draw_circle_outline(pos.x, py, 26, ring_c, outline)

            if not occ:
                # "+" marker
                arcade.draw_line(pos.x-9, py, pos.x+9, py, (130,130,100), 3)
                arcade.draw_line(pos.x, py-9, pos.x, py+9, (130,130,100), 3)

    def _draw_towers(self) -> None:
        for tower in self.game.towers:
            meta = TOWER_META.get(type(tower), dict(body=(200,200,200), glow=(200,200,200,50), label="?"))
            body, glow, lbl = meta["body"], meta["glow"], meta["label"]
            tx, ty = tower.pos.x, self._world_y(tower.pos.y)

            # Glow ring pulsed
            pulse = 0.7 + 0.3 * math.sin(self.anim_t * 2.5)
            gr, gg, gb, ga = glow
            arcade.draw_circle_filled(tx, ty, 24, (gr, gg, gb, int(ga*pulse)))
            arcade.draw_circle_filled(tx, ty, 18, body)
            arcade.draw_circle_outline(tx, ty, 18, (255,255,255), 2)
            arcade.draw_text(lbl, tx-7, ty-8, (20,20,20), 13, bold=True)

            # Level badge
            lvl_colors = [
                (200, 180, 30),
                (100, 180, 255),
                (255, 80, 80),
                (180, 110, 255),
                (100, 220, 120),
                (255, 165, 80),
            ]
            lc = lvl_colors[min(tower.level - 1, len(lvl_colors) - 1)]
            arcade.draw_circle_filled(tx + 15, ty + 15, 9, lc)
            arcade.draw_text(str(tower.level), tx + 11, ty + 9, (20, 20, 20), 9, bold=True)

            # Lv3 special ability indicator
            if tower.level == 3:
                arcade.draw_circle_outline(tx, ty, 20, (255,220,30), 2)

    # ──────────────────────────────────────────────────────────────────
    # ENEMIES / PROJECTILES / EGGS
    # ──────────────────────────────────────────────────────────────────
    def _draw_enemies(self) -> None:
        for e in self.game.enemies:
            if not e.is_alive:
                continue
            ey = self._world_y(e.pos.y)
            body_c = (200,30,30) if not e.follower.is_returning else (150,30,160)

            # Frozen? draw icy shell
            if e.status_manager.is_frozen:
                arcade.draw_circle_filled(e.pos.x, ey, 17, (160,220,255,180))

            arcade.draw_circle_filled(e.pos.x, ey, 14, body_c)
            arcade.draw_circle_outline(e.pos.x, ey, 14, (255,255,255), 1.5)

            if e.has_egg:
                arcade.draw_ellipse_filled(e.pos.x, ey-5, 8, 12, (255,220,30))

            # HP bar
            hp_r = e.hp / e.max_hp
            bw = 30
            arcade.draw_rect_filled(arcade.XYWH(e.pos.x, ey+22, bw, 5), (40,40,40))
            hp_color = (30,200,40) if hp_r > 0.5 else ((255,180,0) if hp_r > 0.25 else (220,40,40))
            arcade.draw_rect_filled(
                arcade.XYWH(e.pos.x - (bw*(1-hp_r))/2, ey+22, bw*hp_r, 4),
                hp_color
            )

            # Status icons
            if e.status_manager.is_slowed:
                arcade.draw_circle_filled(e.pos.x-11, ey+30, 4, (60,200,240))
            if e.status_manager.is_poisoned:
                arcade.draw_circle_filled(e.pos.x+11, ey+30, 4, (100,220,60))

    def _draw_projectiles(self) -> None:
        for proj in self.game.projectiles:
            color = PROJ_COLORS.get(proj.effect_type, (255,255,100))
            py = self._world_y(proj.pos.y)

            if proj.effect_type == "fire_ray":
                # Vẽ tia lửa thẳng từ tháp tới mục tiêu
                sy = self._world_y(proj.start_pos.y)
                ty_screen = self._world_y(proj.target_pos.y)
                # Lõi sáng
                arcade.draw_line(proj.start_pos.x, sy, proj.target_pos.x, ty_screen,
                                 (255, 255, 180, 220), 3)
                # Lớp ngoài màu cam
                arcade.draw_line(proj.start_pos.x, sy, proj.target_pos.x, ty_screen,
                                 (255, 120, 20, 120), 6)
                # Đầu tia (quầng sáng nhỏ ở vị trí hiện tại)
                arcade.draw_circle_filled(proj.pos.x, py, 5, (255, 220, 100))
                arcade.draw_circle_filled(proj.pos.x, py, 9, (255, 120, 20, 80))
            elif proj.effect_type in ("fire_aura", "fire_nova"):
                # Đã được xử lý tức thì, chỉ hiện thị effect
                pass
            else:
                size = 7 if proj.effect_type in ("fireball", "fire") else 5
                arcade.draw_circle_filled(proj.pos.x, py, size, color)
                # Trail glow
                arcade.draw_circle_filled(proj.pos.x, py, size+3, (*color, 60))

    def _draw_dropped_eggs(self) -> None:
        for egg in self.game.dropped_eggs:
            if not egg.is_returned:
                vp = egg.get_interpolated_pos(self.game.nest_pos)
                vy = self._world_y(vp.y)
                arcade.draw_ellipse_filled(vp.x, vy, 10, 14, (255,220,30))
                arcade.draw_ellipse_outline(vp.x, vy, 10, 14, (255,255,255), 1.5)

    # ──────────────────────────────────────────────────────────────────
    # RANGE OVERLAY + UPGRADE MENU
    # ──────────────────────────────────────────────────────────────────
    def _draw_range_overlay(self) -> None:
        idx = self.selected_ped_idx if self.selected_ped_idx is not None else self.hovered_ped_idx
        if idx is None:
            return
        tower = self._tower_at(idx)
        if tower:
            tx, ty = tower.pos.x, self._world_y(tower.pos.y)
            arcade.draw_circle_filled(tx, ty, tower.attack_range, (255,255,255,18))
            arcade.draw_circle_outline(tx, ty, tower.attack_range, (255,255,255,160), 1.5)

    def _draw_upgrade_menu(self) -> None:
        if self.selected_ped_idx is None:
            return

        ped = self.game.pedestals[self.selected_ped_idx]
        tower = self._tower_at(self.selected_ped_idx)
        px, py = ped.x, self._world_y(ped.y)

        if not tower:
            # Hint: drag from shop
            arcade.draw_rect_filled(arcade.XYWH(px, py-52, 230, 36), (20,25,32,220))
            arcade.draw_rect_outline(arcade.XYWH(px, py-52, 230, 36), (200,170,30), 1.5)
            arcade.draw_text("← Kéo rồng vào đây từ shop bên dưới", px-105, py-60, (220,200,80), 9)
        else:
            # Upgrade & Sell panel
            panel_w, panel_h = 260, 62
            arcade.draw_rect_filled(arcade.XYWH(px, py-56, panel_w, panel_h), (18,22,30,235))
            arcade.draw_rect_outline(arcade.XYWH(px, py-56, panel_w, panel_h), (200,170,30), 2)

            # Tower info line
            arcade.draw_text(
                f"{tower.name}  Lv{tower.level}",
                px - panel_w//2 + 8, py-44, (220,200,60), 10, bold=True
            )

            if tower.level == 3:
                ability_text = {
                    FireDragon:   "🔥 Lv3: Burn DoT ACTIVE",
                    IceDragon:    "❄ Lv3: Full Freeze ACTIVE",
                    PoisonDragon: "☠ Lv3: 30% Stun ACTIVE",
                }.get(type(tower), "")
                arcade.draw_text(ability_text, px - panel_w//2 + 8, py-58, (255,220,80), 8)

            # UPG button
            can_upg = self.game.can_afford_upgrade(tower)
            upg_rect = arcade.XYWH(px-65, py-72, 115, 28)
            arcade.draw_rect_filled(upg_rect, (30,120,50) if can_upg else (50,50,55))
            arcade.draw_rect_outline(upg_rect, (60,220,80) if can_upg else (80,80,80), 1.5)
            if tower.level < tower.max_level:
                arcade.draw_text(
                    f"UPG {tower.upgrade_gold_cost}g+{tower.upgrade_ruby_cost}R",
                    px-115, py-78, (255,255,255), 8, bold=True
                )
            else:
                arcade.draw_text("MAX LVL", px-90, py-78, (220,220,80), 9, bold=True)

            # SELL button
            sell_rect = arcade.XYWH(px+65, py-72, 105, 28)
            arcade.draw_rect_filled(sell_rect, (120,30,30))
            arcade.draw_rect_outline(sell_rect, (220,60,60), 1.5)
            arcade.draw_text(
                f"SELL +{tower.sell_gold}g +{tower.sell_ruby}R",
                px+18, py-78, (255,200,200), 8, bold=True
            )

    # ──────────────────────────────────────────────────────────────────
    # TOP HUD
    # ──────────────────────────────────────────────────────────────────
    def _draw_top_hud(self) -> None:
        bar_y = SCREEN_HEIGHT - TOP_HUD_H / 2
        arcade.draw_rect_filled(arcade.XYWH(SCREEN_WIDTH//2, bar_y, SCREEN_WIDTH, TOP_HUD_H), (14,18,26))
        arcade.draw_line(0, SCREEN_HEIGHT-TOP_HUD_H, SCREEN_WIDTH, SCREEN_HEIGHT-TOP_HUD_H, (200,160,30), 2)

        # Level name
        arcade.draw_text(self.level_config.name, 10, bar_y-7, (220,180,30), 12, bold=True)

        # Gold
        arcade.draw_circle_filled(200, bar_y, 10, (220,190,30))
        arcade.draw_text(f"{self.game.gold}g", 215, bar_y-7, (220,190,30), 12, bold=True)

        # Ruby
        arcade.draw_circle_filled(285, bar_y, 9, (220,40,80))
        arcade.draw_text(f"{self.game.ruby}R", 298, bar_y-7, (220,80,120), 12, bold=True)

        # Eggs
        arcade.draw_ellipse_filled(375, bar_y, 10, 14, (255,255,255))
        arcade.draw_text(f"Trứng: {self.game.player_eggs}/5", 388, bar_y-7, (255,255,255), 11, bold=True)

        # Wave
        sp = self.game.wave_spawner
        arcade.draw_text(f"Sóng {sp.current_wave_index+1}/{len(sp.waves)}", 510, bar_y-7, (80,220,220), 11, bold=True)

        # Score
        arcade.draw_text(f"Score: {self.game.score}", 640, bar_y-7, (255,220,60), 11, bold=True)

        # Mana bar (compact, right side of HUD)
        mx, my = 750, bar_y
        mana_ratio = self.game.mana / GameManager.MAX_MANA
        arcade.draw_rect_filled(arcade.XYWH(mx, my, 90, 14), (20,20,40))
        arcade.draw_rect_filled(arcade.XYWH(mx - 45*(1-mana_ratio), my, 90*mana_ratio, 12), (60,80,240))
        arcade.draw_rect_outline(arcade.XYWH(mx, my, 90, 14), (100,120,255), 1.5)
        arcade.draw_text(f"Mana {int(self.game.mana)}", mx-36, my-7, (160,180,255), 9, bold=True)

        # Speed buttons x1 x2 x3
        for i, (lbl, val) in enumerate([("x1",1),("x2",2),("x3",3)]):
            bx = 840 + i*36
            active = self.game.game_speed == val
            arcade.draw_rect_filled(arcade.XYWH(bx, bar_y, 30, 24), (220,170,0) if active else (35,38,50))
            arcade.draw_rect_outline(arcade.XYWH(bx, bar_y, 30, 24), (220,170,0) if active else (80,80,90), 1.5)
            arcade.draw_text(lbl, bx-11, bar_y-7, (20,20,20) if active else (200,200,200), 10, bold=True)

        # Pause button
        pr = arcade.XYWH(960, bar_y, 62, 30)
        ph = self.mouse_pos.to_tuple() in pr
        arcade.draw_rect_filled(pr, (200,50,20) if ph else (120,30,10))
        arcade.draw_rect_outline(pr, (255,255,255), 1.5)
        arcade.draw_text("⏸ DỪNG" if not self.is_paused else "▶ TIẾP", 933, bar_y-7, (255,255,255), 9, bold=True)

    # ──────────────────────────────────────────────────────────────────
    # BOTTOM PANEL: Dragon shop (left) + Spell bar (right)
    # ──────────────────────────────────────────────────────────────────
    def _draw_bottom_panel(self) -> None:
        # Panel background
        arcade.draw_rect_filled(arcade.XYWH(SCREEN_WIDTH//2, BOT_PANEL_H//2, SCREEN_WIDTH, BOT_PANEL_H), (14,18,24))
        arcade.draw_line(0, BOT_PANEL_H, SCREEN_WIDTH, BOT_PANEL_H, (200,160,30), 2)

        # ── Dragon Shop Cards ──────────────────────────────────────────
        shop_label_x = 10
        arcade.draw_text("🐉 RỒNG", shop_label_x, BOT_PANEL_H-14, (180,140,30), 9, bold=True)

        card_start_x = 12
        for idx, d in enumerate(DRAGON_CATALOG):
            cx = card_start_x + idx*(CARD_W+CARD_GAP) + CARD_W//2
            cy = BOT_PANEL_H//2 - 4
            rect = arcade.XYWH(cx, cy, CARD_W, CARD_H)

            affordable = self.game.gold >= d["gold"] and self.game.ruby >= d["ruby"]
            hov = (
                self.mouse_pos.x >= cx-CARD_W//2 and self.mouse_pos.x <= cx+CARD_W//2 and
                self.mouse_pos.y >= cy-CARD_H//2 and self.mouse_pos.y <= cy+CARD_H//2 and
                self.mouse_pos.y <= BOT_PANEL_H
            )

            r,g,b = d["color"]
            bg = (r,g,b,190) if affordable else (r//4,g//4,b//4,140)
            arcade.draw_rect_filled(rect, bg)
            border = d["color"] if affordable else (70,70,70)
            arcade.draw_rect_outline(rect, border, 2.5 if hov else 1.5)

            # Icon
            arcade.draw_circle_filled(cx-38, cy+2, 20, d["color"] if affordable else (60,60,60))
            arcade.draw_text(d["symbol"], cx-46, cy-9, (255,255,255), 14)

            # Labels
            lc = (255,255,255) if affordable else (100,100,100)
            arcade.draw_text(d["label"],    cx-8, cy+18, lc, 9,  bold=True)
            arcade.draw_text(d["sublabel"], cx-8, cy+5,  (200,200,200) if affordable else (80,80,80), 7)
            arcade.draw_text(d["tip"],      cx-8, cy-8,  (180,220,180) if affordable else (70,90,70), 7)

            # Cost
            cost_c = (220,190,30) if affordable else (100,80,20)
            arcade.draw_text(f"{d['gold']}g", cx-8, cy-22, cost_c, 9, bold=True)
            if d["ruby"] > 0:
                arcade.draw_text(f"+{d['ruby']}R", cx+22, cy-22, (220,60,80) if affordable else (100,40,50), 9, bold=True)

            if not affordable:
                arcade.draw_text("THIẾU TÀI NGUYÊN", cx-42, cy-34, (180,60,60), 7)

        # ── Spell Bar (right side) ─────────────────────────────────────
        spell_x = SCREEN_WIDTH - 340
        arcade.draw_line(spell_x-10, 0, spell_x-10, BOT_PANEL_H, (60,55,35), 2)
        arcade.draw_text("⚡ PHÉP THUẬT", spell_x, BOT_PANEL_H-14, (180,140,30), 9, bold=True)

        spells = [
            dict(key="fireball",   label="Cầu Lửa",    cost=35, color=(230,80,20),  key_hint="[Q]",
                 desc="120 DMG AoE", icon="🔥"),
            dict(key="frost_blast", label="Băng Lạnh",  cost=50, color=(60,180,240), key_hint="[W]",
                 desc="Đóng băng TẤT CẢ", icon="❄"),
        ]

        spell_card_w = 148
        for i, sp_def in enumerate(spells):
            scx = spell_x + i*(spell_card_w+8) + spell_card_w//2
            scy = BOT_PANEL_H//2 - 4
            srect = arcade.XYWH(scx, scy, spell_card_w, 88)

            can_cast = self.game.mana >= sp_def["cost"]
            targeting_this = self.spell_targeting == sp_def["key"]

            r,g,b = sp_def["color"]
            bg_a = 200 if can_cast else 80
            arcade.draw_rect_filled(srect, (r,g,b,bg_a))
            border_c = (255,255,60) if targeting_this else (sp_def["color"] if can_cast else (60,60,60))
            arcade.draw_rect_outline(srect, border_c, 3 if targeting_this else 1.5)

            arcade.draw_text(sp_def["icon"],  scx-62, scy-6, (255,255,255), 18)
            arcade.draw_text(sp_def["label"], scx-12, scy+22, (255,255,255) if can_cast else (120,120,120), 10, bold=True)
            arcade.draw_text(sp_def["desc"],  scx-12, scy+8,  (220,220,200) if can_cast else (80,80,80), 8)
            arcade.draw_text(f"Mana: {sp_def['cost']}", scx-12, scy-6, (160,180,255) if can_cast else (80,80,100), 8)
            arcade.draw_text(sp_def["key_hint"], scx-12, scy-22, (220,220,80) if can_cast else (80,80,50), 9, bold=True)

            if not can_cast:
                arcade.draw_text("THIẾU MANA", scx-32, scy-34, (200,60,60), 8)
            if targeting_this:
                arcade.draw_text("ĐANG NHẮM...", scx-40, scy-34, (255,240,30), 8, bold=True)

        # Mana bar across bottom of spell area
        mb_x = spell_x; mb_w = spell_card_w*2 + 8
        mana_r = self.game.mana / GameManager.MAX_MANA
        arcade.draw_rect_filled(arcade.XYWH(mb_x + mb_w//2, 8, mb_w, 10), (20,20,45))
        arcade.draw_rect_filled(arcade.XYWH(mb_x + mb_w*mana_r/2, 8, mb_w*mana_r, 8), (80,100,255))
        arcade.draw_rect_outline(arcade.XYWH(mb_x + mb_w//2, 8, mb_w, 10), (120,140,255), 1)
        arcade.draw_text(f"MANA: {int(self.game.mana)}/{GameManager.MAX_MANA}", mb_x+mb_w//2-40, 2, (140,160,255), 8)

    # ──────────────────────────────────────────────────────────────────
    # DRAG GHOST
    # ──────────────────────────────────────────────────────────────────
    def _draw_drag_ghost(self) -> None:
        d = next((x for x in DRAGON_CATALOG if x["key"] == self.dragging_key), None)
        if not d:
            return
        r,g,b = d["color"]
        dx, dy = self.drag_pos.x, self.drag_pos.y
        arcade.draw_circle_filled(dx, dy, 24, (r,g,b,150))
        arcade.draw_circle_outline(dx, dy, 24, (255,255,255), 2)
        arcade.draw_text(d["symbol"], dx-10, dy-10, (255,255,255), 16)

        # Snap ring if near pedestal
        for pos in self.game.pedestals:
            py = self._world_y(pos.y)
            if math.hypot(dx-pos.x, dy-py) <= 42:
                arcade.draw_circle_outline(pos.x, py, 32, (255,220,30), 3)

    # ──────────────────────────────────────────────────────────────────
    # FIREBALL AIM CROSSHAIR
    # ──────────────────────────────────────────────────────────────────
    def _draw_fireball_aim(self) -> None:
        mx, my = self.mouse_pos.x, self.mouse_pos.y
        aoe = GameManager.FIREBALL_AOE
        t = self.anim_t
        pulse_r = aoe + 4*math.sin(t*5)
        arcade.draw_circle_outline(mx, my, pulse_r, (255,100,20,200), 2)
        arcade.draw_circle_filled(mx, my, aoe, (255,80,10,35))
        arcade.draw_line(mx-aoe-10, my, mx+aoe+10, my, (255,120,30,180), 1)
        arcade.draw_line(mx, my-aoe-10, mx, my+aoe+10, (255,120,30,180), 1)
        arcade.draw_text("🔥 NHẤP ĐỂ PHÓNG", mx-55, my-aoe-18, (255,200,50), 9)

    # ──────────────────────────────────────────────────────────────────
    # MODALS
    # ──────────────────────────────────────────────────────────────────
    def _draw_pause_modal(self) -> None:
        cx, cy = SCREEN_WIDTH/2, SCREEN_HEIGHT/2
        arcade.draw_rect_filled(arcade.XYWH(cx,cy,340,280), (0,0,0,240))
        arcade.draw_rect_outline(arcade.XYWH(cx,cy,340,280), (200,160,30), 3)
        arcade.draw_text("⏸ TẠM DỪNG", cx-80, cy+88, (220,180,30), 22, bold=True)

        for label, by, c in [("▶ TIẾP TỤC", cy+35, (30,140,50)), ("↺ CHƠI LẠI", cy-15, (180,100,20)), ("☰ CHỌN MÀN", cy-65, (140,20,20))]:
            rect = arcade.XYWH(cx, by, 200, 38)
            hov  = self.mouse_pos.to_tuple() in rect
            arcade.draw_rect_filled(rect, c if hov else (35,38,48))
            arcade.draw_rect_outline(rect, c, 2)
            arcade.draw_text(label, cx-55, by-7, (255,255,255), 12, bold=True)

    def _draw_victory_modal(self) -> None:
        ProgressManager.unlock_next_level(self.level_id, self.game.score)
        cx, cy = SCREEN_WIDTH/2, SCREEN_HEIGHT/2
        arcade.draw_rect_filled(arcade.XYWH(cx,cy,400,300), (0,0,0,240))
        arcade.draw_rect_outline(arcade.XYWH(cx,cy,400,300), (200,160,30), 3.5)
        arcade.draw_text("🏆 CHIẾN THẮNG!", cx-110, cy+100, (220,180,30), 28, bold=True)
        arcade.draw_text("Trứng rồng đã được bảo vệ thành công!", cx-145, cy+65, (255,255,255), 12)
        arcade.draw_text(f"Score: {self.game.score}", cx-55, cy+35, (255,220,50), 14, bold=True)
        arcade.draw_text(f"Gold: {self.game.gold}    Ruby: {self.game.ruby}", cx-80, cy+10, (200,180,30), 11)

        btns = []
        if self.level_id < 10:
            btns.append(("→ MÀN SAU", cy-35, (30,130,50)))
        btns.append(("☰ CHỌN MÀN", cy-80, (140,20,20)))

        for label, by, c in btns:
            rect = arcade.XYWH(cx, by, 220, 38)
            hov  = self.mouse_pos.to_tuple() in rect
            arcade.draw_rect_filled(rect, c if hov else (35,38,48))
            arcade.draw_rect_outline(rect, c, 2)
            arcade.draw_text(label, cx-60, by-7, (255,255,255), 12, bold=True)

    def _draw_game_over_modal(self) -> None:
        cx, cy = SCREEN_WIDTH/2, SCREEN_HEIGHT/2
        arcade.draw_rect_filled(arcade.XYWH(cx,cy,380,270), (0,0,0,240))
        arcade.draw_rect_outline(arcade.XYWH(cx,cy,380,270), (200,30,30), 3.5)
        arcade.draw_text("💀 THẤT BẠI!", cx-85, cy+86, (220,40,40), 26, bold=True)
        arcade.draw_text("Tất cả trứng rồng đã bị đánh cắp!", cx-140, cy+52, (255,255,255), 12)

        for label, by, c in [("↺ CHƠI LẠI", cy-15, (180,80,20)), ("☰ CHỌN MÀN", cy-60, (140,20,20))]:
            rect = arcade.XYWH(cx, by, 200, 38)
            hov  = self.mouse_pos.to_tuple() in rect
            arcade.draw_rect_filled(rect, c if hov else (35,38,48))
            arcade.draw_rect_outline(rect, c, 2)
            arcade.draw_text(label, cx-50, by-7, (255,255,255), 12, bold=True)

    # ──────────────────────────────────────────────────────────────────
    # HELPERS
    # ──────────────────────────────────────────────────────────────────
    def _tower_at(self, ped_idx: int) -> Optional[DragonTower]:
        if 0 <= ped_idx < len(self.game.pedestals):
            pp = self.game.pedestals[ped_idx]
            for t in self.game.towers:
                if t.pos.distance_to(pp) < 5.0:
                    return t
        return None

    def _ped_near(self, sx: float, sy: float) -> Optional[int]:
        """Find pedestal near screen-coordinate (sx, sy)."""
        game_y = sy - BOT_PANEL_H
        for idx, pp in enumerate(self.game.pedestals):
            if math.hypot(sx - pp.x, game_y - pp.y) <= 36:
                return idx
        return None

    def _card_at(self, x: float, y: float) -> Optional[str]:
        if y > BOT_PANEL_H:
            return None
        card_start_x = 12
        for idx, d in enumerate(DRAGON_CATALOG):
            cx = card_start_x + idx*(CARD_W+CARD_GAP) + CARD_W//2
            cy = BOT_PANEL_H//2 - 4
            if abs(x-cx) <= CARD_W//2 and abs(y-cy) <= CARD_H//2:
                return d["key"]
        return None

    def _spell_card_at(self, x: float, y: float) -> Optional[str]:
        if y > BOT_PANEL_H:
            return None
        spell_x = SCREEN_WIDTH - 340
        spell_card_w = 148
        spells = ["fireball", "frost_blast"]
        for i, key in enumerate(spells):
            scx = spell_x + i*(spell_card_w+8) + spell_card_w//2
            scy = BOT_PANEL_H//2 - 4
            if abs(x-scx) <= spell_card_w//2 and abs(y-scy) <= 44:
                return key
        return None

    # ──────────────────────────────────────────────────────────────────
    # MOUSE INPUT
    # ──────────────────────────────────────────────────────────────────
    def on_mouse_motion(self, x, y, dx, dy) -> None:
        self.mouse_pos = Vec2(x, y)
        self.drag_pos  = Vec2(x, y)

        if not self.dragging_key:
            self.hovered_ped_idx = None
            for idx, pp in enumerate(self.game.pedestals):
                py = self._world_y(pp.y)
                if math.hypot(x-pp.x, y-py) <= 28:
                    self.hovered_ped_idx = idx
                    break

    def on_mouse_press(self, x, y, button, modifiers) -> None:
        cx, cy = SCREEN_WIDTH/2, SCREEN_HEIGHT/2

        # ── Modals ─────────────────────────────────────────────────────
        if self.is_paused:
            if (x,y) in arcade.XYWH(cx, cy+35, 200, 38):
                self.is_paused = False
            elif (x,y) in arcade.XYWH(cx, cy-15, 200, 38):
                self.window.show_view(GameplayView(self.level_id))
            elif (x,y) in arcade.XYWH(cx, cy-65, 200, 38):
                self.window.show_view(LevelSelectView())
            return

        if self.game.is_victory:
            if self.level_id < 10 and (x,y) in arcade.XYWH(cx, cy-35, 220, 38):
                self.window.show_view(GameplayView(self.level_id+1))
            elif (x,y) in arcade.XYWH(cx, cy-80, 220, 38):
                self.window.show_view(LevelSelectView())
            return

        if self.game.is_game_over:
            if (x,y) in arcade.XYWH(cx, cy-15, 200, 38):
                self.window.show_view(GameplayView(self.level_id))
            elif (x,y) in arcade.XYWH(cx, cy-60, 200, 38):
                self.window.show_view(LevelSelectView())
            return

        # ── Fireball targeting mode ─────────────────────────────────────
        if self.spell_targeting == "fireball":
            # Click in play area = launch fireball there
            if y > BOT_PANEL_H and y < SCREEN_HEIGHT - TOP_HUD_H:
                game_y = y - BOT_PANEL_H
                self.game.cast_fireball(Vec2(x, game_y))
            self.spell_targeting = None
            return

        # ── Top HUD buttons ────────────────────────────────────────────
        bar_y = SCREEN_HEIGHT - TOP_HUD_H/2

        # Speed buttons
        for i, val in enumerate([1, 2, 3]):
            bx = 840 + i*36
            if (x,y) in arcade.XYWH(bx, bar_y, 30, 24):
                self.game.game_speed = val
                return

        # Pause button
        if (x,y) in arcade.XYWH(960, bar_y, 62, 30):
            self.is_paused = True
            return

        # ── Bottom panel: spells ────────────────────────────────────────
        spell_key = self._spell_card_at(x, y)
        if spell_key == "fireball":
            if self.game.mana >= GameManager.SPELL_MANA_COST["fireball"]:
                self.spell_targeting = "fireball"
            return
        if spell_key == "frost_blast":
            self.game.cast_frost_blast()
            return

        # ── Bottom panel: drag start ────────────────────────────────────
        card_key = self._card_at(x, y)
        if card_key is not None:
            d = next(c for c in DRAGON_CATALOG if c["key"] == card_key)
            if self.game.gold >= d["gold"] and self.game.ruby >= d["ruby"]:
                self.dragging_key = card_key
                self.drag_pos = Vec2(x, y)
            return

        # ── Click on pedestal (game area) ──────────────────────────────
        ped_idx = self._ped_near(x, y)
        if ped_idx is not None:
            if self.selected_ped_idx == ped_idx:
                self.selected_ped_idx = None
            else:
                self.selected_ped_idx = ped_idx
            return

        # ── Upgrade / Sell buttons in popup ────────────────────────────
        if self.selected_ped_idx is not None:
            ped = self.game.pedestals[self.selected_ped_idx]
            tower = self._tower_at(self.selected_ped_idx)
            px, py_s = ped.x, self._world_y(ped.y)
            if tower:
                if (x,y) in arcade.XYWH(px-65, py_s-72, 115, 28):
                    self.game.upgrade_tower(tower)
                elif (x,y) in arcade.XYWH(px+65, py_s-72, 105, 28):
                    self.game.sell_tower(tower)
            self.selected_ped_idx = None

    def on_mouse_release(self, x, y, button, modifiers) -> None:
        if self.dragging_key:
            ped_idx = self._ped_near(x, y)
            if ped_idx is not None:
                d = next(c for c in DRAGON_CATALOG if c["key"] == self.dragging_key)
                if not self._tower_at(ped_idx):
                    tower = d["cls"](len(self.game.towers)+1, self.game.pedestals[ped_idx])
                    self.game.add_tower(tower)
            self.dragging_key = None

    # ──────────────────────────────────────────────────────────────────
    # KEYBOARD
    # ──────────────────────────────────────────────────────────────────
    def on_key_press(self, symbol, modifiers) -> None:
        if symbol in (arcade.key.ESCAPE, arcade.key.P):
            if self.spell_targeting:
                self.spell_targeting = None   # Cancel aim
            else:
                self.is_paused = not self.is_paused
        elif not self.is_paused:
            if symbol == arcade.key.Q:
                if self.game.mana >= GameManager.SPELL_MANA_COST["fireball"]:
                    self.spell_targeting = "fireball"
            elif symbol == arcade.key.W:
                self.game.cast_frost_blast()
            elif symbol == arcade.key.KEY_1:
                self.game.game_speed = 1
            elif symbol == arcade.key.KEY_2:
                self.game.game_speed = 2
            elif symbol == arcade.key.KEY_3:
                self.game.game_speed = 3
