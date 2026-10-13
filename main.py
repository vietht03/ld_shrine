#!/usr/bin/env python3
"""
Lair Defense: Shrine - Main Game Launcher.
Initializes the Python Arcade Window and starts the Scene/State Manager on MainMenuView.
"""

from __future__ import annotations
import arcade
from gui.game_views import MainMenuView, SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE


def main() -> None:
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    main_menu = MainMenuView()
    window.show_view(main_menu)
    arcade.run()


if __name__ == "__main__":
    main()
