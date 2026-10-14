"""
upgrade_manager.py
==================
Reads the Skill Shop state (saved by upgrade_shop.html via a JSON bridge file)
and provides computed bonus values to the game engine.

The shop saves its state to  `shop_state.json`  in the game root.
This module reads that file and exposes typed accessors.

JSON schema (written by JS in upgrade_shop.html):
  {
    "gold": 106200,
    "levels": {
      "ice_mastery":  3,
      "dragon_fury":  1,
      ...
    }
  }
"""
from __future__ import annotations
import os
import json
from typing import Dict

# Path to the shared state file (written by the HTML shop, read here)
_STATE_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "shop_state.json")

# ─────────────────────────────────────────────────────────────────────────────
# Upgrade definitions — MUST mirror upgrade_shop.html UPGRADES array
# ─────────────────────────────────────────────────────────────────────────────
_DEFS: Dict[str, dict] = {
    # ── Row 0: Attack ──────────────────────────────────────────────────────
    "ice_mastery":   {"base": 2.0,  "step": 0.15, "max": 15},  # Slow duration (s)
    "dragon_fury":   {"base": 0,    "step": 8,    "max": 4},   # Fire DMG bonus (flat)
    "storm_call":    {"base": 0,    "step": 5,    "max": 15},  # Attack rate bonus (%)
    "inferno_core":  {"base": 52,   "step": 6,    "max": 20},  # Fire AoE radius (px)
    "nature_toxin":  {"base": 5,    "step": 3,    "max": 15},  # Poison DoT/tick
    "shadow_flame":  {"base": 7,    "step": 5,    "max": 10},  # Burn damage bonus
    # ── Row 1: Defense / Support ──────────────────────────────────────────
    "flame_aura":    {"base": 0,    "step": 3,    "max": 15},  # Nest armor (%) — future
    "beast_hide":    {"base": 5,    "step": 1,    "max": 4},   # Max eggs bonus
    "vine_ward":     {"base": 0,    "step": 4,    "max": 3},   # Entry slow (%)
    "tidal_guard":   {"base": 240,  "step": 12,   "max": 15},  # Ice tower range (px)
    "blood_feast":   {"base": 0,    "step": 4,    "max": 10},  # Gold per kill bonus
    "mana_flow":     {"base": 6,    "step": 1,    "max": 10},  # Mana regen /s
    # ── Row 2: Economy / Special ─────────────────────────────────────────
    "gold_rush":     {"base": 500,  "step": 50,   "max": 15},  # Starting gold
    "dragon_scale":  {"base": 0,    "step": 4,    "max": 4},   # Range bonus (%)
    "comet_slash":   {"base": 0,    "step": 2,    "max": 1},   # Crit chance (%)
    "spirit_blade":  {"base": 2.0,  "step": 0.2,  "max": 35},  # Crit multiplier
    "inferno_ring":  {"base": 200,  "step": 10,   "max": 10},  # Nova radius (px)
    "dragon_eye":    {"base": 0,    "step": 10,   "max": 10},  # Wave gold bonus
}


def _load() -> dict:
    """Load raw state dict from shop_state.json; returns defaults if missing."""
    try:
        if os.path.exists(_STATE_FILE):
            with open(_STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {"gold": 0, "levels": {}}


def _stat(skill_id: str, levels: dict) -> float:
    """Compute the current stat value for a skill given its upgrade level."""
    d = _DEFS.get(skill_id)
    if not d:
        return 0.0
    lv = min(levels.get(skill_id, 0), d["max"])
    return d["base"] + lv * d["step"]


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────
class UpgradeManager:
    """
    Singleton-style accessor for all upgrade bonuses.
    Call  UpgradeManager.reload()  after the shop HTML saves new state.
    """

    _data: dict = {}
    _levels: dict = {}

    @classmethod
    def reload(cls) -> None:
        cls._data   = _load()
        cls._levels = cls._data.get("levels", {})

    @classmethod
    def level(cls, skill_id: str) -> int:
        return cls._levels.get(skill_id, 0)

    @classmethod
    def set_level(cls, skill_id: str, new_level: int) -> None:
        """Set the upgrade level for a skill (used by SkillShopView)."""
        cls._levels[skill_id] = new_level

    @classmethod
    def save(cls, gold: int) -> None:
        """Persist current levels + gold to shop_state.json."""
        import json
        data = {"gold": gold, "levels": dict(cls._levels)}
        try:
            with open(_STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    @classmethod
    def stat(cls, skill_id: str) -> float:
        return _stat(skill_id, cls._levels)

    # ── Convenience getters ───────────────────────────────────────────────

    @classmethod
    def starting_gold(cls) -> int:
        """Starting gold as defined by gold_rush upgrade."""
        return int(_stat("gold_rush", cls._levels))

    @classmethod
    def attack_rate_mult(cls) -> float:
        """Multiplier for fire_interval (e.g. 0.90 = 10% faster)."""
        bonus_pct = _stat("storm_call", cls._levels)
        return max(0.4, 1.0 - bonus_pct / 100.0)

    @classmethod
    def fire_damage_bonus(cls) -> float:
        """Flat extra damage added to every FireDragon attack."""
        return _stat("dragon_fury", cls._levels) + _stat("shadow_flame", cls._levels)

    @classmethod
    def fire_burn_bonus(cls) -> float:
        """Extra burn DoT damage from shadow_flame."""
        return _stat("shadow_flame", cls._levels)

    @classmethod
    def fire_aoe_radius(cls) -> float:
        """Base AoE radius override for level-1 Fire Dragon (inferno_core)."""
        return _stat("inferno_core", cls._levels)

    @classmethod
    def fire_nova_radius(cls) -> float:
        """Extra nova radius for fire_aura (inferno_ring)."""
        return _stat("inferno_ring", cls._levels)

    @classmethod
    def ice_slow_duration(cls) -> float:
        """Base slow duration for Ice Dragon (ice_mastery)."""
        return _stat("ice_mastery", cls._levels)

    @classmethod
    def ice_range_bonus_px(cls) -> float:
        """Flat range bonus for Ice Dragon towers (tidal_guard)."""
        bonus = _stat("tidal_guard", cls._levels) - 240  # baseline already in tower
        return max(0.0, bonus)

    @classmethod
    def poison_dot_bonus(cls) -> float:
        """Extra poison DoT per tick (nature_toxin)."""
        return _stat("nature_toxin", cls._levels) - 5   # 5 is baseline

    @classmethod
    def range_bonus_pct(cls) -> float:
        """Global range multiplier for all towers (dragon_scale)."""
        return _stat("dragon_scale", cls._levels) / 100.0

    @classmethod
    def crit_chance_bonus(cls) -> float:
        """Extra crit chance % (comet_slash)."""
        return _stat("comet_slash", cls._levels) / 100.0

    @classmethod
    def crit_multiplier(cls) -> float:
        """Crit damage multiplier (spirit_blade)."""
        return _stat("spirit_blade", cls._levels)

    @classmethod
    def mana_regen_bonus(cls) -> float:
        """Extra mana per second (mana_flow — adds on top of base 6)."""
        return _stat("mana_flow", cls._levels) - 6   # 6 is baseline

    @classmethod
    def gold_per_kill_bonus(cls) -> int:
        """Flat extra gold per enemy kill (blood_feast)."""
        return int(_stat("blood_feast", cls._levels))

    @classmethod
    def wave_gold_bonus(cls) -> int:
        """Flat extra gold from each wave cleared (dragon_eye)."""
        return int(_stat("dragon_eye", cls._levels))

    @classmethod
    def max_eggs_bonus(cls) -> int:
        """Extra starting eggs (beast_hide)."""
        return int(_stat("beast_hide", cls._levels)) - 5  # 5 is default

    @classmethod
    def shop_saved_gold(cls) -> int:
        """Return the gold saved in the shop JSON (for display only)."""
        return int(cls._data.get("gold", 0))


# ── Module-level auto-load on import ─────────────────────────────────────────
UpgradeManager.reload()
