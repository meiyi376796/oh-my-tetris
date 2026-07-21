"""Stateless geometry and layout helpers for the Tetris UI."""

import pygame

from tetris_core import Position, Tetromino
from tetris_ui_config import (
    GAME_LAYOUT,
    SCREEN,
)

# Flat single-column layout: title, status line, playfield, key hints.
TITLE_CENTER_Y = 52
_PLAYFIELD_TOP = 130
_STATUS_BAR_HEIGHT = 26
_STATUS_BAR_GAP = 12


def get_playfield_rect() -> pygame.Rect:
    width = GAME_LAYOUT.grid_width * GAME_LAYOUT.grid_size
    height = GAME_LAYOUT.grid_height * GAME_LAYOUT.grid_size
    x = (SCREEN.width - width) // 2
    return pygame.Rect(x, _PLAYFIELD_TOP, width, height)


def get_status_bar_rect() -> pygame.Rect:
    playfield = get_playfield_rect()
    return pygame.Rect(
        playfield.x,
        playfield.y - _STATUS_BAR_HEIGHT - _STATUS_BAR_GAP,
        playfield.width,
        _STATUS_BAR_HEIGHT,
    )


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
