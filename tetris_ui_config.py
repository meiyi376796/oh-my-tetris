"""Shared UI configuration, types, and constants for the Tetris runtime."""

import os
from dataclasses import dataclass
from typing import Literal, TypeAlias

import pygame

from tetris_core import Action, BOARD_HEIGHT, BOARD_WIDTH, Color

# Shared UI typing helpers.
FontKey: TypeAlias = Literal["title", "score", "body"]
FontMap: TypeAlias = dict[FontKey, pygame.font.Font]
TextAlign: TypeAlias = Literal["left", "center", "right"]
TextAnchor: TypeAlias = tuple[int, TextAlign]
VerticalBand: TypeAlias = tuple[int, int]


@dataclass(frozen=True)
class SpacingScale:
    sm: int = 8
    md: int = 13
    lg: int = 21
    xl: int = 34


@dataclass(frozen=True)
class FontSizes:
    title: int = 34
    score: int = 21
    body: int = 13


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
SCREEN = ScreenConfig(width=600, height=800)

GAME_LAYOUT = GameLayoutConfig(
    grid_size=24,
    grid_width=BOARD_WIDTH,
    grid_height=BOARD_HEIGHT,
    cell_inset=2,
    playfield_border_width=3,
)

# UI overlay transparency levels.
OVERLAY_ALPHA: int = 89
PANEL_ALPHA: int = 144

# CRT arcade monitor palette in the Game Boy LCD phosphor-green family.
PALETTE: dict[str, Color] = {
    "bg": (28, 28, 32),
    "monitor": (32, 32, 38),
    "monitor_light": (55, 55, 64),
    "monitor_dark": (18, 18, 22),
    "neon": (155, 188, 15),
    "neon_dim": (100, 140, 10),
    "screen_bg": (148, 181, 15),
    "screen_light": (132, 165, 15),
    "block_fill": (15, 56, 15),
    "ghost": (48, 98, 48),
    "text_dim": (105, 125, 20),
    "overlay": (15, 56, 15),
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
