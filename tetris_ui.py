"""Pygame UI shell, layout, and rendering helpers for the Tetris runtime."""

import os

import pygame

from tetris_core import Action, Color, GameState, Grid, Tetromino
from tetris_ui_config import (
    CHICAGO_FONT_PATH,
    CONTROL_BINDINGS,
    FONT_SIZES,
    FontKey,
    FontMap,
    GAME_LAYOUT,
    OVERLAY_ALPHA,
    PALETTE,
    SCREEN,
    SPACING,
)
from tetris_ui_helpers import (
    TITLE_CENTER_Y,
    get_playfield_rect,
    get_status_bar_rect,
    get_visible_piece_positions,
    make_inset_rect,
)


class TetrisUI:
    """Shared Pygame window shell, layout state, and rendering helpers."""

    # Gameplay host hooks.
    @property
    def grid(self) -> Grid:
        raise NotImplementedError

    @property
    def score(self) -> int:
        raise NotImplementedError

    @property
    def level(self) -> int:
        raise NotImplementedError

    @property
    def lines(self) -> int:
        raise NotImplementedError

    @property
    def state(self) -> GameState:
        raise NotImplementedError

    @state.setter
    def state(self, next_state: GameState) -> None:
        raise NotImplementedError

    @property
    def current_piece(self) -> Tetromino | None:
        raise NotImplementedError

    def _reset_input_state(self) -> None:
        raise NotImplementedError

    def _get_shadow_piece(self) -> Tetromino:
        raise NotImplementedError

    def __init__(self) -> None:
        pygame.init()
        self.screen: pygame.Surface = pygame.display.set_mode(
            (SCREEN.width, SCREEN.height)
        )
        pygame.display.set_caption("TETRIS")
        pygame.key.stop_text_input()

        self.fonts: FontMap = {}
        self._setup_fonts()

        self.window_focused: bool = True

        self.playfield_rect: pygame.Rect = get_playfield_rect()
        self.status_bar_rect: pygame.Rect = get_status_bar_rect()

        self.scanline_surface: pygame.Surface = self._make_scanline_surface()
        self.overlay_surface: pygame.Surface = self._make_overlay_surface()

    def _setup_fonts(self) -> None:
        font_path = self._get_font_path()
        try:
            self.fonts = {
                "title": pygame.font.Font(font_path, FONT_SIZES.title),
                "score": pygame.font.Font(font_path, FONT_SIZES.score),
                "body": pygame.font.Font(font_path, FONT_SIZES.body),
            }
        except (OSError, RuntimeError) as font_error:
            raise RuntimeError(
                f"Unable to load font at {font_path}. "
                "Place CHICAGO.TTF in the project root or update CHICAGO_FONT_PATH."
            ) from font_error

    @staticmethod
    def _get_font_path() -> str:
        if os.path.exists(CHICAGO_FONT_PATH):
            return CHICAGO_FONT_PATH
        raise RuntimeError(
            f"Required font not found at {CHICAGO_FONT_PATH}. "
            "Place CHICAGO.TTF in the project root or update CHICAGO_FONT_PATH."
        )

    # Focus handling.
    def _deactivate_window(self) -> None:
        if not self.window_focused:
            return
        self.window_focused = False
        self._reset_input_state()
        if self.state == GameState.PLAYING:
            self.state = GameState.PAUSED

    def _activate_window(self) -> None:
        self.window_focused = True

    # Primitive drawing helpers.
    def _make_playfield_cell_rect(self, x: int, y: int) -> pygame.Rect:
        return make_inset_rect(
            self.playfield_rect.x + x * GAME_LAYOUT.grid_size,
            self.playfield_rect.y + y * GAME_LAYOUT.grid_size,
            GAME_LAYOUT.grid_size,
            GAME_LAYOUT.cell_inset,
        )

    def _draw_block(self, x: int, y: int) -> None:
        rect = self._make_playfield_cell_rect(x, y)
        pygame.draw.rect(self.screen, PALETTE["lcd_dark"], rect)

    def _draw_ghost_block(self, x: int, y: int) -> None:
        rect = self._make_playfield_cell_rect(x, y)
        pygame.draw.rect(self.screen, PALETTE["ghost"], rect, 1)

    # Text rendering.
    def _render_text_surface(
        self,
        text: str,
        font_key: FontKey,
        color: Color,
        tracking: int = 0,
    ) -> pygame.Surface:
        font = self.fonts[font_key]
        if tracking <= 0 or len(text) <= 1:
            return font.render(text, True, color)

        glyphs = [font.render(ch, True, color) for ch in text]
        width = sum(glyph.get_width() for glyph in glyphs) + tracking * (len(glyphs) - 1)
        height = max(
            (glyph.get_height() for glyph in glyphs),
            default=font.get_linesize(),
        )
        surface = pygame.Surface((max(1, width), max(1, height)), pygame.SRCALPHA)

        cursor_x = 0
        for glyph in glyphs:
            surface.blit(glyph, (cursor_x, 0))
            cursor_x += glyph.get_width() + tracking
        return surface

    def _draw_background(self) -> None:
        self.screen.fill(PALETTE["canvas"])

    def _make_scanline_surface(self) -> pygame.Surface:
        surface = pygame.Surface(self.playfield_rect.size, pygame.SRCALPHA)
        for y in range(0, self.playfield_rect.height, 2):
            pygame.draw.line(
                surface,
                (0, 0, 0, 8),
                (0, y),
                (self.playfield_rect.width, y),
                1,
            )
        return surface

    def _make_overlay_surface(self) -> pygame.Surface:
        surface = pygame.Surface(self.playfield_rect.size, pygame.SRCALPHA)
        surface.fill((*PALETTE["lcd_dark"], OVERLAY_ALPHA))
        return surface

    # Title flanked by hairline rules, like old handheld silkscreen.
    def _draw_title(self) -> None:
        title_surface = self._render_text_surface(
            "TETRIS", "title", PALETTE["ink"], tracking=10
        )
        center_x = self.screen.get_rect().centerx
        title_rect = title_surface.get_rect(center=(center_x, TITLE_CENTER_Y))
        self.screen.blit(title_surface, title_rect)

        rule_y = title_rect.centery
        rule_inset = self.playfield_rect.x // 2
        gap = SPACING.md
        for start_x, end_x in (
            (rule_inset, title_rect.left - gap),
            (title_rect.right + gap, SCREEN.width - rule_inset),
        ):
            pygame.draw.line(
                self.screen,
                PALETTE["ink_dim"],
                (start_x, rule_y),
                (end_x, rule_y),
                1,
            )

    # Status line: dim labels, bright values, centered over the playfield.
    def _draw_status_bar(self) -> None:
        segments = (
            ("SCORE ", PALETTE["ink_dim"]),
            (f"{self.score:06d}", PALETTE["ink"]),
            ("   LINES ", PALETTE["ink_dim"]),
            (f"{self.lines:03d}", PALETTE["ink"]),
            ("   LEVEL ", PALETTE["ink_dim"]),
            (f"{self.level:02d}", PALETTE["ink"]),
        )
        surfaces = [
            self._render_text_surface(text, "score", color)
            for text, color in segments
        ]
        total_width = sum(surface.get_width() for surface in surfaces)

        cursor_x = self.screen.get_rect().centerx - total_width // 2
        for surface in surfaces:
            rect = surface.get_rect()
            rect.x = cursor_x
            rect.y = self.status_bar_rect.y + max(
                0, (self.status_bar_rect.height - surface.get_height()) // 2
            )
            self.screen.blit(surface, rect)
            cursor_x = rect.right

    def _draw_playfield(self) -> None:
        pygame.draw.rect(self.screen, PALETTE["lcd"], self.playfield_rect)

        # Grid hairlines.
        for x in range(1, GAME_LAYOUT.grid_width):
            grid_line_x = self.playfield_rect.x + x * GAME_LAYOUT.grid_size
            pygame.draw.line(
                self.screen,
                PALETTE["lcd_line"],
                (grid_line_x, self.playfield_rect.y),
                (grid_line_x, self.playfield_rect.bottom - 1),
                1,
            )
        for y in range(1, GAME_LAYOUT.grid_height):
            grid_line_y = self.playfield_rect.y + y * GAME_LAYOUT.grid_size
            pygame.draw.line(
                self.screen,
                PALETTE["lcd_line"],
                (self.playfield_rect.x, grid_line_y),
                (self.playfield_rect.right - 1, grid_line_y),
                1,
            )

        # Locked blocks.
        for y in range(GAME_LAYOUT.grid_height):
            for x in range(GAME_LAYOUT.grid_width):
                if self.grid[y][x]:
                    self._draw_block(x, y)

        # Ghost piece.
        if self.state == GameState.PLAYING and self.current_piece:
            try:
                shadow = self._get_shadow_piece()
                for x, y in get_visible_piece_positions(shadow):
                    self._draw_ghost_block(x, y)
            except RuntimeError:
                pass

        # Current piece.
        current_piece = self.current_piece
        if current_piece:
            for x, y in get_visible_piece_positions(current_piece):
                self._draw_block(x, y)

        # Single hairline frame just outside the playfield.
        frame = self.playfield_rect.inflate(
            GAME_LAYOUT.playfield_border_width * 2,
            GAME_LAYOUT.playfield_border_width * 2,
        )
        pygame.draw.rect(
            self.screen,
            PALETTE["ink_dim"],
            frame,
            GAME_LAYOUT.playfield_border_width,
        )

    def _draw_overlay_dim(self) -> None:
        if self.state == GameState.PLAYING:
            return
        self.screen.blit(self.overlay_surface, self.playfield_rect.topleft)

    def _draw_overlay_text(self) -> None:
        if self.state == GameState.PLAYING:
            return

        if self.state == GameState.START:
            main_text = "WELCOME"
            sub_text = "Press any key to start"
        elif self.state == GameState.PAUSED:
            main_text = "PAUSED"
            sub_text = "Press P to resume"
        else:
            main_text = "GAME OVER"
            sub_text = "Press R to restart"

        main_surface = self._render_text_surface(
            main_text, "title", PALETTE["ink"], tracking=6
        )
        sub_surface = self._render_text_surface(
            sub_text, "body", PALETTE["ink"]
        )

        center_x = self.playfield_rect.centerx
        center_y = self.playfield_rect.centery
        main_rect = main_surface.get_rect(center=(center_x, center_y - SPACING.sm))
        sub_rect = sub_surface.get_rect(center=(center_x, center_y + SPACING.lg))
        self.screen.blit(main_surface, main_rect)
        self.screen.blit(sub_surface, sub_rect)

    # Key hints.
    def _draw_key_hints(self) -> None:
        gameplay_actions = {
            Action.MOVE_LEFT, Action.MOVE_RIGHT, Action.ROTATE,
            Action.SOFT_DROP, Action.HARD_DROP,
        }
        gameplay_bindings = [b for b in CONTROL_BINDINGS if b.action in gameplay_actions]
        meta_bindings = [b for b in CONTROL_BINDINGS if b.action not in gameplay_actions]

        hints = (
            "    ".join(f"{b.key_label}  {b.help_text}" for b in gameplay_bindings),
            "    ".join(f"{b.key_label}  {b.help_text}" for b in meta_bindings),
        )
        y = self.playfield_rect.bottom + SPACING.lg
        for line in hints:
            surface = self._render_text_surface(line, "body", PALETTE["ink_dim"])
            rect = surface.get_rect(centerx=self.screen.get_rect().centerx, y=y)
            self.screen.blit(surface, rect)
            y += surface.get_height() + SPACING.sm

    def draw(self) -> None:
        self._draw_background()
        self._draw_title()
        self._draw_status_bar()
        self._draw_playfield()
        self._draw_overlay_dim()
        self.screen.blit(self.scanline_surface, self.playfield_rect.topleft)
        self._draw_overlay_text()
        self._draw_key_hints()
        pygame.display.flip()
