"""Shared UI configuration, types, and constants for the Tetris runtime."""

import os
from dataclasses import dataclass
from typing import Literal, TypeAlias

import pygame

from tetris_core import Action, BOARD_HEIGHT, BOARD_WIDTH, Color

# Shared UI typing helpers.
FontKey: TypeAlias = Literal["title", "score", "body"]
FontMap: TypeAlias = dict[FontKey, pygame.font.Font]


@dataclass(frozen=True)
class SpacingScale:
    sm: int = 8
    md: int = 13
    lg: int = 21


@dataclass(frozen=True)
class FontSizes:
    title: int = 26
    score: int = 15
    body: int = 12


@dataclass(frozen=True)
class ScreenConfig:
    width: int
    height: int


@dataclass(frozen=True)
class GameLayoutConfig:
    grid_size: int
    grid_width: int
    grid_height: int
    cell_inset: int
    playfield_border_width: int


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHICAGO_FONT_PATH = os.path.join(BASE_DIR, "CHICAGO.TTF")

SPACING = SpacingScale()
FONT_SIZES = FontSizes()
SCREEN = ScreenConfig(width=420, height=740)

GAME_LAYOUT = GameLayoutConfig(
    grid_size=26,
    grid_width=BOARD_WIDTH,
    grid_height=BOARD_HEIGHT,
    cell_inset=2,
    playfield_border_width=1,
)

# Dim level applied to the playfield behind overlay text.
OVERLAY_ALPHA: int = 150

# Flat Game Boy LCD palette: one green phosphor field on a warm dark canvas.
PALETTE: dict[str, Color] = {
    "canvas": (23, 24, 21),
    "lcd": (139, 172, 15),
    "lcd_line": (124, 153, 21),
    "lcd_dark": (15, 56, 15),
    "ghost": (48, 98, 48),
    "ink": (155, 188, 15),
    "ink_dim": (92, 112, 26),
}


@dataclass(frozen=True)
class ControlBinding:
    """Immutable keyboard binding metadata for input and help text."""

    action: Action
    key: int
    key_label: str
    help_text: str


CONTROL_BINDINGS: tuple[ControlBinding, ...] = (
    ControlBinding(Action.MOVE_LEFT, pygame.K_a, "A", "Left"),
    ControlBinding(Action.MOVE_RIGHT, pygame.K_d, "D", "Right"),
    ControlBinding(Action.ROTATE, pygame.K_w, "W", "Rotate"),
    ControlBinding(Action.SOFT_DROP, pygame.K_s, "S", "Drop"),
    ControlBinding(Action.HARD_DROP, pygame.K_SPACE, "Space", "Hard"),
    ControlBinding(Action.PAUSE_RESUME, pygame.K_p, "P", "Pause"),
    ControlBinding(Action.RESTART, pygame.K_r, "R", "Reset"),
)
ACTION_BY_KEY: dict[int, Action] = {
    binding.key: binding.action
    for binding in CONTROL_BINDINGS
}
