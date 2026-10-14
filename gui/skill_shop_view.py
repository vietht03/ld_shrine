"""
gui/skill_shop_view.py
======================
In-game Skill Shop screen built with Python Arcade.
Replaces the web-based upgrade_shop.html — no browser required.

Layout (1000×700):
  ┌──────────────────────── HEADER (title + gold) ─────────────────────────┐
  │  Left: 3 rows × 6 skill icons (with level badge)                       │
  │  Right: Detail panel (icon, name, desc, stats, upgrade button)          │
  └────────────────────────── FOOTER (back button) ─────────────────────────┘
"""
from __future__ import annotations

import json
import math
import os
from typing import Optional

import arcade

from core.upgrade_manager import UpgradeManager

# ──────────────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────────────
SW, SH = 1000, 700          # Screen dimensions
HEADER_H = 72               # Header bar height
FOOTER_H = 60               # Footer bar height
PANEL_W  = 270              # Right detail panel width
GRID_W   = SW - PANEL_W     # Left grid area width

# Grid layout
ICON_SIZE  = 82             # Circle diameter
ICON_GAP   = 12             # Gap between icons
ROW_START_X = 28            # Left margin for first icon column
ROW_START_Y  = SH - HEADER_H - 20   # Y of first row top
ROW_STEP_Y   = ICON_SIZE + 38       # Vertical step between rows (icon + label)

# Colors
C_BG          = (20, 10, 3)
C_HEADER      = (50, 24, 8)
C_FOOTER      = (28, 12, 3)
C_PANEL       = (25, 13, 3)
C_BORDER      = (139, 105, 20)
C_GOLD        = (240, 192, 64)
C_TEXT        = (245, 223, 160)
C_DIM         = (140, 100, 40)
C_GREEN       = (80, 220, 90)
C_RED         = (220, 60, 50)
C_BTN_UP      = (180, 100, 16)
C_BTN_HOV     = (220, 130, 22)
C_BTN_DIS     = (60, 40, 20)
C_BTN_MAX     = (70, 30, 130)

# State file path (same as upgrade_manager)
_STATE_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "shop_state.json")

# ──────────────────────────────────────────────────────────────────────────────
# Upgrade definitions (18 skills)
# ──────────────────────────────────────────────────────────────────────────────
UPGRADES = [
    # row 0 — Attack
    dict(id="ice_mastery",   row=0, name="Ice Mastery",    desc="Increases Ice Dragon\nfreeze and slow duration.",        icon="❄",  color=(30, 140, 220),  glow=(60, 200, 255),  stat="Slow Duration", base=2.0,  step=0.15, unit="s",  max_lv=15, cost=300,  scale=1.40),
    dict(id="dragon_fury",   row=0, name="Dragon Fury",    desc="Boosts Fire Dragon\nraw attack damage.",                 icon="🐉", color=(210, 60, 10),   glow=(255, 120, 30),  stat="Fire DMG Bonus",base=0,    step=8,    unit="",   max_lv=4,  cost=500,  scale=1.80),
    dict(id="storm_call",    row=0, name="Storm Call",     desc="Crackling energy boosts\nall tower attack rate.",        icon="⚡", color=(200, 160, 0),   glow=(255, 220, 30),  stat="Attack Rate",   base=0,    step=5,    unit="%",  max_lv=15, cost=350,  scale=1.45),
    dict(id="inferno_core",  row=0, name="Inferno Core",   desc="Expands Fire Dragon\nAoE explosion radius.",            icon="🔥", color=(190, 30, 10),   glow=(255, 80, 20),   stat="AoE Radius",    base=52,   step=6,    unit="px", max_lv=20, cost=400,  scale=1.35),
    dict(id="nature_toxin",  row=0, name="Nature Toxin",   desc="Enhances poison potency,\nincreasing DoT per tick.",    icon="☘",  color=(20, 160, 40),   glow=(60, 255, 80),   stat="DoT per Tick",  base=5,    step=3,    unit="",   max_lv=15, cost=320,  scale=1.40),
    dict(id="shadow_flame",  row=0, name="Shadow Flame",   desc="Dark energy boosts\nburn damage of fire attacks.",      icon="🌑", color=(100, 0, 200),   glow=(180, 40, 255),  stat="Burn Damage",   base=7,    step=5,    unit="",   max_lv=10, cost=600,  scale=1.60),
    # row 1 — Defense
    dict(id="flame_aura",    row=1, name="Flame Aura",     desc="Fire aura reduces damage\ntaken by the Dragon Nest.",   icon="🔴", color=(200, 20, 20),   glow=(255, 60, 60),   stat="Nest Armor",    base=0,    step=3,    unit="%",  max_lv=15, cost=280,  scale=1.40),
    dict(id="beast_hide",    row=1, name="Beast Hide",     desc="Thickens nest walls,\nraising max egg capacity.",       icon="🦎", color=(20, 140, 60),   glow=(60, 220, 100),  stat="Max Eggs",      base=5,    step=1,    unit="",   max_lv=4,  cost=800,  scale=2.00),
    dict(id="vine_ward",     row=1, name="Vine Ward",      desc="Magical vines slow enemies\napproaching the nest.",     icon="🌿", color=(10, 120, 120),  glow=(30, 200, 200),  stat="Entry Slow",    base=0,    step=4,    unit="%",  max_lv=3,  cost=700,  scale=2.20),
    dict(id="tidal_guard",   row=1, name="Tidal Guard",    desc="Tidal barrier extends\nIce Dragon attack range.",      icon="🌊", color=(0, 80, 160),    glow=(20, 160, 240),  stat="Ice Range",     base=240,  step=12,   unit="px", max_lv=15, cost=350,  scale=1.45),
    dict(id="blood_feast",   row=1, name="Blood Feast",    desc="Increases gold earned\nper enemy kill.",               icon="🍖", color=(160, 10, 10),   glow=(240, 30, 30),   stat="Gold/Kill",     base=0,    step=4,    unit="g",  max_lv=10, cost=500,  scale=1.55),
    dict(id="mana_flow",     row=1, name="Mana Flow",      desc="Improves mana regen rate\nfor casting more spells.",   icon="💧", color=(20, 120, 180),  glow=(60, 200, 255),  stat="Mana Regen",    base=6,    step=1,    unit="/s", max_lv=10, cost=450,  scale=1.50),
    # row 2 — Economy
    dict(id="gold_rush",     row=2, name="Gold Rush",      desc="Increases starting gold\nat the beginning of levels.", icon="💰", color=(0, 140, 160),   glow=(20, 220, 240),  stat="Starting Gold", base=500,  step=50,   unit="g",  max_lv=15, cost=400,  scale=1.40),
    dict(id="dragon_scale",  row=2, name="Dragon Scale",   desc="Reinforced scales extend\nrange for all towers.",     icon="🐲", color=(10, 60, 160),   glow=(40, 120, 255),  stat="Range Bonus",   base=0,    step=4,    unit="%",  max_lv=4,  cost=600,  scale=1.90),
    dict(id="comet_slash",   row=2, name="Comet Slash",    desc="Grants towers a chance\nto deal critical damage.",    icon="✨", color=(80, 80, 200),   glow=(160, 160, 255), stat="Crit Chance",   base=0,    step=2,    unit="%",  max_lv=1,  cost=999,  scale=3.00),
    dict(id="spirit_blade",  row=2, name="Spirit Blade",   desc="Spirit energy amplifies\ncritical hit multiplier.",   icon="🗡", color=(170, 120, 0),   glow=(255, 200, 40),  stat="Crit Multi",    base=2.0,  step=0.2,  unit="x",  max_lv=35, cost=250,  scale=1.30),
    dict(id="inferno_ring",  row=2, name="Inferno Ring",   desc="Flaming ring expands\nFire Aura nova radius.",        icon="🔥", color=(180, 50, 0),    glow=(255, 100, 20),  stat="Nova Radius",   base=200,  step=10,   unit="px", max_lv=10, cost=500,  scale=1.55),
    dict(id="dragon_eye",    row=2, name="Dragon Eye",     desc="Dragon eye grants extra\ngold from each wave.",       icon="👁", color=(20, 70, 180),   glow=(60, 140, 255),  stat="Wave Gold",     base=0,    step=10,   unit="g",  max_lv=10, cost=550,  scale=1.50),
]

ROW_LABELS = [
    "⚔ Row 1 — Attack Power upgrades",
    "🛡 Row 2 — Defense & Support upgrades",
    "💰 Row 3 — Economy & Special upgrades",
]

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────
def _lv(u: dict) -> int:
    return UpgradeManager.level(u["id"])

def _maxed(u: dict) -> bool:
    return _lv(u) >= u["max_lv"]

def _cost(u: dict) -> int:
    return int(u["cost"] * (u["scale"] ** _lv(u)))

def _stat_val(u: dict, level: int) -> float:
    return u["base"] + level * u["step"]

def _fmt(u: dict, level: int) -> str:
    v = _stat_val(u, level)
    s = str(int(v)) if isinstance(v, float) and v == int(v) else f"{v:.1f}"
    return s + u["unit"]

def _icon_pos(u: dict) -> tuple[float, float]:
    """Return (cx, cy) center of skill icon in screen coords."""
    col = [x for x in UPGRADES if x["row"] == u["row"]].index(u)
    cx = ROW_START_X + col * (ICON_SIZE + ICON_GAP) + ICON_SIZE // 2
    cy = ROW_START_Y - u["row"] * ROW_STEP_Y
    return cx, cy


def _load_state() -> dict:
    try:
        if os.path.exists(_STATE_FILE):
            with open(_STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {"gold": 0, "levels": {}}


def _save_state(gold: int) -> None:
    data = {
        "gold": gold,
        "levels": {u["id"]: UpgradeManager.level(u["id"]) for u in UPGRADES},
    }
    try:
        with open(_STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


# ──────────────────────────────────────────────────────────────────────────────
# SkillShopView
# ──────────────────────────────────────────────────────────────────────────────
class SkillShopView(arcade.View):
    """
    Full-screen in-game Skill Shop built with Arcade drawing primitives.
    Call  window.show_view(SkillShopView(previous_view, gold))  to open.
    """

    def __init__(self, previous_view: arcade.View, shop_gold: int = 0) -> None:
        super().__init__()
        UpgradeManager.reload()
        self._prev = previous_view
        self.shop_gold: int = max(shop_gold, _load_state().get("gold", 106_200))

        self.selected: Optional[dict] = None
        self.mouse_x: float = 0.0
        self.mouse_y: float = 0.0
        self.anim_t: float = 0.0

        # Toast notification
        self._toast_msg: str = ""
        self._toast_timer: float = 0.0
        self._toast_ok: bool = True

        # Shake effect for "not enough gold"
        self._shake_t: float = 0.0

        # Load dragon textures
        self._textures: dict = {}
        self._load_textures()

    # ── Texture loading ───────────────────────────────────────────────────────
    def _load_textures(self) -> None:
        base = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "sprites")
        for name, fname in [("fire", "fire_dragon.png"), ("ice", "ice_dragon.png"), ("poison", "poison_dragon.png")]:
            path = os.path.join(base, fname)
            if os.path.exists(path):
                try:
                    self._textures[name] = arcade.load_texture(path)
                except Exception:
                    pass

    # ── Update ────────────────────────────────────────────────────────────────
    def on_update(self, dt: float) -> None:
        self.anim_t += dt
        if self._toast_timer > 0:
            self._toast_timer -= dt
        if self._shake_t > 0:
            self._shake_t -= dt

    # ── Draw ──────────────────────────────────────────────────────────────────
    def on_draw(self) -> None:
        self.clear()
        arcade.set_background_color(C_BG)

        self._draw_bg_pattern()
        self._draw_header()
        self._draw_grid()
        self._draw_detail_panel()
        self._draw_footer()
        self._draw_toast()

    # ── Background ────────────────────────────────────────────────────────────
    def _draw_bg_pattern(self) -> None:
        # Subtle grid lines for texture
        for x in range(0, SW, 40):
            arcade.draw_line(x, FOOTER_H, x, SH - HEADER_H, (255, 200, 80, 8), 1)
        for y in range(FOOTER_H, SH - HEADER_H, 40):
            arcade.draw_line(0, y, SW, y, (255, 200, 80, 8), 1)

        # Dividing line between grid and panel
        arcade.draw_line(GRID_W, FOOTER_H, GRID_W, SH - HEADER_H, C_BORDER, 2)

        # Magical glow orbs in background
        t = self.anim_t
        for ox, oy, r, hue in [(200, 400, 80, (200,80,20)), (500, 250, 60, (20,80,200)), (700, 500, 70, (80,180,20))]:
            pulse = abs(math.sin(t * 0.7 + ox * 0.01))
            alpha = int(12 + 8 * pulse)
            arcade.draw_circle_filled(ox, oy, r, (*hue, alpha))

    # ── Header ────────────────────────────────────────────────────────────────
    def _draw_header(self) -> None:
        arcade.draw_rect_filled(arcade.XYWH(SW/2, SH - HEADER_H/2, SW, HEADER_H), C_HEADER)
        arcade.draw_line(0, SH - HEADER_H, SW, SH - HEADER_H, C_BORDER, 2)

        # Title
        arcade.draw_text("⚔  SKILL SHOP  ⚔", SW/2, SH - HEADER_H/2 - 10,
                         C_GOLD, 26, bold=True, anchor_x="center", anchor_y="center")

        # Gold display (top-right)
        shake_x = int(math.sin(self._shake_t * 40) * 5) if self._shake_t > 0 else 0
        gx = SW - 160 + shake_x
        gy = SH - HEADER_H/2
        arcade.draw_rect_filled(arcade.XYWH(gx, gy, 180, 38), (0, 0, 0, 160))
        arcade.draw_rect_outline(arcade.XYWH(gx, gy, 180, 38), C_BORDER, 2)
        # Coin circle
        pulse = abs(math.sin(self.anim_t * 2)) * 0.4 + 0.6
        coin_c = (int(255 * pulse), int(200 * pulse), 0)
        arcade.draw_circle_filled(gx - 68, gy, 11, coin_c)
        arcade.draw_circle_outline(gx - 68, gy, 11, C_BORDER, 1)
        arcade.draw_text(f"{self.shop_gold:,}", gx - 48, gy - 7,
                         C_GOLD, 15, bold=True)

    # ── Skill Grid ────────────────────────────────────────────────────────────
    def _draw_grid(self) -> None:
        rows_data = [[], [], []]
        for u in UPGRADES:
            rows_data[u["row"]].append(u)

        for ri, row_items in enumerate(rows_data):
            # Row label
            label_y = ROW_START_Y - ri * ROW_STEP_Y + 8
            arcade.draw_text(ROW_LABELS[ri], ROW_START_X, label_y,
                             (180, 140, 60, 200), 9, italic=True)

            for u in row_items:
                self._draw_icon(u)

    def _draw_icon(self, u: dict) -> None:
        cx, cy = _icon_pos(u)
        lv   = _lv(u)
        mx   = _maxed(u)
        sel  = (self.selected is u)
        hov  = (math.hypot(self.mouse_x - cx, self.mouse_y - cy) < ICON_SIZE // 2 + 4)

        r    = ICON_SIZE // 2
        col  = u["color"]
        glow = u["glow"]

        t = self.anim_t

        # Glow ring when selected or hovered
        if sel:
            glow_r = r + 6 + 2 * abs(math.sin(t * 4))
            arcade.draw_circle_outline(cx, cy, glow_r, (*glow, 200), 3)
        elif hov:
            arcade.draw_circle_outline(cx, cy, r + 4, (*glow, 120), 2)

        # Dark background circle
        arcade.draw_circle_filled(cx, cy, r, (10, 5, 2))

        # Gradient fill — approximate with 3 concentric circles
        arcade.draw_circle_filled(cx, cy, r, (*col, 220))
        mid = tuple(min(255, c + 40) for c in col)
        arcade.draw_circle_filled(cx - r//4, cy + r//4, r * 0.65, (*mid, 180))
        arcade.draw_circle_filled(cx - r//3, cy + r//3, r * 0.30, (255, 255, 255, 60))

        # Shine highlight
        arcade.draw_circle_filled(cx - r//3, cy + r//3, r * 0.22, (255, 255, 255, 80))

        # Icon emoji text
        arcade.draw_text(u["icon"], cx, cy - 4, (255, 255, 255), 24,
                         anchor_x="center", anchor_y="center")

        # Max-level golden shine
        if mx:
            pulse_a = int(80 + 60 * abs(math.sin(t * 3)))
            arcade.draw_circle_outline(cx, cy, r, (255, 160, 0, pulse_a), 3)

        # Border ring
        border_c = C_GOLD if sel else C_BORDER
        arcade.draw_circle_outline(cx, cy, r, border_c, 2)

        # Level badge at bottom
        badge_y = cy - r - 2
        badge_text = f"{lv}/{u['max_lv']}"
        bw = len(badge_text) * 6 + 8
        bx = cx - bw // 2
        badge_col = (50, 20, 0, 210)
        arcade.draw_rect_filled(arcade.XYWH(cx, badge_y, bw, 14), badge_col)
        arcade.draw_rect_outline(arcade.XYWH(cx, badge_y, bw, 14),
                                 (255, 150, 0) if mx else C_BORDER, 1)
        arcade.draw_text(badge_text, cx, badge_y - 4,
                         (255, 160, 0) if mx else C_GOLD, 8,
                         bold=True, anchor_x="center", anchor_y="center")

    # ── Detail Panel ──────────────────────────────────────────────────────────
    def _draw_detail_panel(self) -> None:
        px = GRID_W
        ph = SH - HEADER_H - FOOTER_H
        py_center = FOOTER_H + ph / 2

        # Panel background
        arcade.draw_rect_filled(arcade.XYWH(px + PANEL_W/2, py_center, PANEL_W, ph), C_PANEL)

        if self.selected is None:
            arcade.draw_text("Click a skill\nto view details", px + PANEL_W//2,
                             py_center, C_DIM, 12, italic=True,
                             anchor_x="center", anchor_y="center",
                             multiline=True, width=PANEL_W - 20)
            return

        u  = self.selected
        lv = _lv(u)
        mx = _maxed(u)
        c  = u["color"]
        g  = u["glow"]

        inner_x   = px + 16
        inner_w   = PANEL_W - 32
        cur_y     = SH - HEADER_H - 20

        # ── Icon preview ──────────────────────────────────────────────────────
        ico_cx = px + PANEL_W // 2
        ico_cy = cur_y - 38
        ico_r  = 34
        arcade.draw_circle_filled(ico_cx, ico_cy, ico_r, (*c, 230))
        mid2 = tuple(min(255, x + 40) for x in c)
        arcade.draw_circle_filled(ico_cx - 10, ico_cy + 10, ico_r * 0.6, (*mid2, 180))
        arcade.draw_circle_filled(ico_cx - 12, ico_cy + 12, ico_r * 0.25, (255, 255, 255, 80))
        arcade.draw_circle_outline(ico_cx, ico_cy, ico_r, (*g, 200), 3)
        arcade.draw_text(u["icon"], ico_cx, ico_cy - 4, (255, 255, 255), 22,
                         anchor_x="center", anchor_y="center")
        cur_y -= 82

        # ── Name ─────────────────────────────────────────────────────────────
        arcade.draw_text(u["name"], px + PANEL_W//2, cur_y,
                         C_GOLD, 13, bold=True,
                         anchor_x="center", anchor_y="center")
        cur_y -= 18

        # ── Separator ────────────────────────────────────────────────────────
        arcade.draw_line(inner_x, cur_y, inner_x + inner_w, cur_y, C_BORDER, 1)
        cur_y -= 14

        # ── Description ───────────────────────────────────────────────────────
        for line in u["desc"].split("\n"):
            arcade.draw_text(line, px + PANEL_W//2, cur_y, C_TEXT, 10,
                             italic=True, anchor_x="center", anchor_y="center")
            cur_y -= 15
        cur_y -= 6

        # ── Stats box ────────────────────────────────────────────────────────
        box_h = 60 if not mx else 42
        box_cy = cur_y - box_h // 2
        arcade.draw_rect_filled(arcade.XYWH(px + PANEL_W//2, box_cy, inner_w, box_h), (0, 0, 0, 100))
        arcade.draw_rect_outline(arcade.XYWH(px + PANEL_W//2, box_cy, inner_w, box_h), C_BORDER, 1)

        bx = inner_x + 8
        by = cur_y - 14
        arcade.draw_text(u["stat"], bx, by, C_DIM, 9)
        by -= 14

        cur_val  = _fmt(u, lv)
        arcade.draw_text("Current:", bx, by, C_DIM, 9)
        arcade.draw_text(cur_val, bx + 90, by, C_GOLD, 11, bold=True)
        by -= 16

        if not mx:
            next_val = _fmt(u, lv + 1)
            arcade.draw_text("Next:", bx, by, C_DIM, 9)
            arcade.draw_text(next_val, bx + 90, by, C_GREEN, 11, bold=True)

        cur_y -= box_h + 12

        if mx:
            # Max badge
            arcade.draw_rect_filled(arcade.XYWH(px + PANEL_W//2, cur_y - 12, inner_w, 26),
                                    (80, 30, 130, 200))
            arcade.draw_rect_outline(arcade.XYWH(px + PANEL_W//2, cur_y - 12, inner_w, 26),
                                     (160, 80, 255), 2)
            arcade.draw_text("✦  MAX LEVEL  ✦", px + PANEL_W//2, cur_y - 12,
                             (200, 120, 255), 11, bold=True,
                             anchor_x="center", anchor_y="center")
            return

        # ── Cost bar ──────────────────────────────────────────────────────────
        c_val = _cost(u)
        can_afford = self.shop_gold >= c_val
        arcade.draw_rect_filled(arcade.XYWH(px + PANEL_W//2, cur_y - 16, inner_w, 28),
                                (0, 0, 0, 130))
        arcade.draw_rect_outline(arcade.XYWH(px + PANEL_W//2, cur_y - 16, inner_w, 28),
                                 C_BORDER if can_afford else (160, 40, 40), 1)
        # Coin
        arcade.draw_circle_filled(inner_x + 14, cur_y - 16, 9,
                                  (255, 200, 0) if can_afford else (120, 80, 0))
        arcade.draw_text(f"{c_val:,}", inner_x + 26, cur_y - 22,
                         C_GOLD if can_afford else (150, 80, 30), 12, bold=True)
        cur_y -= 42

        # ── Upgrade button ────────────────────────────────────────────────────
        btn_rect = arcade.XYWH(px + PANEL_W//2, cur_y - 20, inner_w, 38)
        bx2, by2 = px + PANEL_W//2, cur_y - 20
        hov_btn = abs(self.mouse_x - bx2) < inner_w//2 and abs(self.mouse_y - by2) < 19

        if can_afford:
            btn_col = C_BTN_HOV if hov_btn else C_BTN_UP
            txt_col = (255, 248, 220)
        else:
            btn_col = C_BTN_DIS
            txt_col = (120, 80, 40)

        arcade.draw_rect_filled(btn_rect, btn_col)
        arcade.draw_rect_outline(btn_rect,
                                 (220, 160, 30) if can_afford else (80, 50, 20), 2)
        arcade.draw_text("UPGRADE", bx2, by2, txt_col, 13, bold=True,
                         anchor_x="center", anchor_y="center")

    # ── Footer ────────────────────────────────────────────────────────────────
    def _draw_footer(self) -> None:
        arcade.draw_rect_filled(arcade.XYWH(SW/2, FOOTER_H/2, SW, FOOTER_H), C_FOOTER)
        arcade.draw_line(0, FOOTER_H, SW, FOOTER_H, C_BORDER, 2)

        # Back button
        hov = (self.mouse_x < 160 and self.mouse_y < FOOTER_H)
        col = (60, 60, 70) if hov else (40, 40, 50)
        arcade.draw_rect_filled(arcade.XYWH(90, FOOTER_H//2, 160, 38), col)
        arcade.draw_rect_outline(arcade.XYWH(90, FOOTER_H//2, 160, 38), C_BORDER, 2)
        arcade.draw_text("◀  Back", 90, FOOTER_H//2 - 7, C_TEXT, 13, bold=True,
                         anchor_x="center")

        # Dragon sprite previews in footer
        self._draw_footer_dragons()

        # ESC hint
        arcade.draw_text("ESC = Back", SW - 90, FOOTER_H//2 - 6, C_DIM, 9,
                         anchor_x="center")

    def _draw_footer_dragons(self) -> None:
        """Draw small dragon portraits in the footer area."""
        labels = [("fire", "Fire Dragon", (230, 100, 20)),
                  ("ice",  "Ice Dragon",  (60, 190, 240)),
                  ("poison","Poison Dragon",(100, 210, 80))]
        start_x = 300
        for i, (key, name, col) in enumerate(labels):
            cx = start_x + i * 200
            cy = FOOTER_H // 2
            tex = self._textures.get(key)
            if tex:
                arcade.draw_texture_rect(
                    tex,
                    arcade.XYWH(cx, cy, 50, 50)
                )
            else:
                # Fallback: colored circle with letter
                arcade.draw_circle_filled(cx - 20, cy, 20, col)
                arcade.draw_text(key[0].upper(), cx - 20, cy - 8, (255,255,255), 13,
                                 bold=True, anchor_x="center")
            arcade.draw_text(name, cx + (5 if tex else 8), cy - 7, col, 9, bold=True)

    # ── Toast ─────────────────────────────────────────────────────────────────
    def _draw_toast(self) -> None:
        if self._toast_timer <= 0:
            return
        alpha = min(255, int(255 * self._toast_timer / 2.0))
        col   = (30, 180, 60) if self._toast_ok else (180, 40, 30)
        txt_c = (200, 255, 200) if self._toast_ok else (255, 180, 160)
        arcade.draw_rect_filled(arcade.XYWH(SW//2, SH - HEADER_H - 30, 400, 36),
                                (*col, min(200, alpha)))
        arcade.draw_rect_outline(arcade.XYWH(SW//2, SH - HEADER_H - 30, 400, 36),
                                 (*txt_c, alpha), 2)
        arcade.draw_text(self._toast_msg, SW//2, SH - HEADER_H - 38,
                         (*txt_c, alpha), 11, bold=True, anchor_x="center")

    def _show_toast(self, msg: str, ok: bool = True) -> None:
        self._toast_msg   = msg
        self._toast_ok    = ok
        self._toast_timer = 2.2

    # ── Mouse ─────────────────────────────────────────────────────────────────
    def on_mouse_motion(self, x, y, dx, dy) -> None:
        self.mouse_x = x
        self.mouse_y = y

    def on_mouse_press(self, x, y, button, modifiers) -> None:
        if button != arcade.MOUSE_BUTTON_LEFT:
            return

        # Back button
        if x < 170 and y < FOOTER_H:
            self._go_back()
            return

        # Upgrade button (only when panel is open)
        if self.selected and not _maxed(self.selected):
            u = self.selected
            px = GRID_W
            inner_w = PANEL_W - 32
            bx2 = px + PANEL_W // 2
            by2 = self._upgrade_btn_y()
            if abs(x - bx2) < inner_w // 2 and abs(y - by2) < 19:
                self._do_upgrade(u)
                return

        # Click on skill icon
        for u in UPGRADES:
            cx, cy = _icon_pos(u)
            if math.hypot(x - cx, y - cy) < ICON_SIZE // 2 + 4:
                self.selected = u
                return

        # Click outside icons (in grid area) — deselect
        if x < GRID_W:
            self.selected = None

    def _upgrade_btn_y(self) -> float:
        """Compute upgrade button Y for hit-testing."""
        if not self.selected:
            return -999
        u = self.selected
        cur_y = SH - HEADER_H - 20
        cur_y -= 82   # icon
        cur_y -= 18   # name
        cur_y -= 14   # sep
        for _ in u["desc"].split("\n"):
            cur_y -= 15
        cur_y -= 6
        box_h = 60
        cur_y -= box_h + 12
        cur_y -= 42   # cost bar
        return cur_y - 20

    def _do_upgrade(self, u: dict) -> None:
        c = _cost(u)
        if self.shop_gold < c:
            self._show_toast(f"Not enough Gold! Need {c:,}g", ok=False)
            self._shake_t = 0.5
            return

        self.shop_gold -= c
        new_lv = _lv(u) + 1
        UpgradeManager.set_level(u["id"], new_lv)
        UpgradeManager.save(self.shop_gold)
        UpgradeManager.reload()

        if _maxed(u):
            self._show_toast(f"✦ {u['name']} maxed out!", ok=True)
        else:
            self._show_toast(f"{u['name']} upgraded to Lv {new_lv}!", ok=True)

    def _go_back(self) -> None:
        _save_state(self.shop_gold)
        UpgradeManager.reload()
        self.window.show_view(self._prev)

    # ── Keyboard ──────────────────────────────────────────────────────────────
    def on_key_press(self, key, modifiers) -> None:
        if key == arcade.key.ESCAPE:
            self._go_back()
