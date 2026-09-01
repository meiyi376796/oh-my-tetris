"""Stateless geometry and layout helpers for the Tetris UI."""

import pygame

from tetris_core import Position, Tetromino
from tetris_ui_config import (
    GAME_LAYOUT,
    SCREEN,
)

# Game Boy layout.
TITLE_CENTER_Y = 70
_MARGIN = 50
# Playfield sits one pixel inside the margin; its hairline frame is the outer edge.
_PLAYFIELD_LEFT = _MARGIN + GAME_LAYOUT.playfield_border_width
_PLAYFIELD_TOP = 111
_INFO_COLUMN_GAP = 32
NEXT_CELL_SIZE = GAME_LAYOUT.grid_size // 2
NEXT_CELL_INSET = 1
NEXT_BOX_PADDING = 10
NEXT_BOX_SIZE = 4 * NEXT_CELL_SIZE + 2 * NEXT_BOX_PADDING


def get_playfield_rect() -> pygame.Rect:
    # One extra pixel for the closing grid line on the right/bottom edge.
    width = GAME_LAYOUT.grid_width * GAME_LAYOUT.grid_size + 1
    height = GAME_LAYOUT.grid_height * GAME_LAYOUT.grid_size + 1
    return pygame.Rect(_PLAYFIELD_LEFT, _PLAYFIELD_TOP, width, height)


def get_info_column_rect() -> pygame.Rect:
    playfield = get_playfield_rect()
    x = playfield.right + _INFO_COLUMN_GAP
    return pygame.Rect(
        x,
        playfield.y,
        SCREEN.width - _MARGIN - x,
        playfield.height,
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
