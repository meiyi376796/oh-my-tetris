"""Stateless geometry and layout helpers for the Tetris UI."""

import pygame

from tetris_core import Position, Tetromino
from tetris_ui_config import (
    GAME_LAYOUT,
    SPACING,
)

# CRT arcade monitor layout.
MONITOR_RECT = pygame.Rect(100, 80, 400, 640)

_SCREEN_MARGIN = 55
_PLAYFIELD_TOP_OFFSET = 25

SCREEN_RECT = pygame.Rect(
    MONITOR_RECT.x + _SCREEN_MARGIN,
    MONITOR_RECT.y + _SCREEN_MARGIN,
    MONITOR_RECT.width - _SCREEN_MARGIN * 2,
    MONITOR_RECT.height - _SCREEN_MARGIN * 2,
)

STATUS_BAR_RECT = pygame.Rect(
    SCREEN_RECT.x,
    MONITOR_RECT.y + SPACING.lg,
    SCREEN_RECT.width,
    SPACING.xl,
)


def get_monitor_rect() -> pygame.Rect:
    return MONITOR_RECT.copy()


def get_screen_rect() -> pygame.Rect:
    return SCREEN_RECT.copy()


def get_status_bar_rect() -> pygame.Rect:
    return STATUS_BAR_RECT.copy()


def get_playfield_rect() -> pygame.Rect:
    screen = get_screen_rect()
    width = GAME_LAYOUT.grid_width * GAME_LAYOUT.grid_size
    height = GAME_LAYOUT.grid_height * GAME_LAYOUT.grid_size
    x = screen.x + (screen.width - width) // 2
    y = screen.y + _PLAYFIELD_TOP_OFFSET
    return pygame.Rect(x, y, width, height)


def make_inset_rect(x: int, y: int, size: int, inset: int) -> pygame.Rect:
    return pygame.Rect(
        x + inset,
        y + inset,
        size - 2 * inset,
        size - 2 * inset,
    )


def get_visible_piece_positions(piece: Tetromino) -> list[Position]:
    return [
        (x, y)
        for x, y in piece.get_positions()
        if 0 <= y < GAME_LAYOUT.grid_height
    ]
