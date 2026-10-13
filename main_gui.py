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
