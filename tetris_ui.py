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
    PANEL_ALPHA,
    PALETTE,
    SCREEN,
    SPACING,
    TextAnchor,
    VerticalBand,
)
from tetris_ui_helpers import (
    get_monitor_rect,
    get_playfield_rect,
    get_screen_rect,
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

        self.monitor_rect: pygame.Rect = get_monitor_rect()
        self.screen_rect: pygame.Rect = get_screen_rect()
        self.status_bar_rect: pygame.Rect = get_status_bar_rect()
        self.playfield_rect: pygame.Rect = get_playfield_rect()

        self.scanline_surface: pygame.Surface = self._make_scanline_surface()
        self.vignette_surface: pygame.Surface = self._make_vignette_surface()
        self.glow_surface: pygame.Surface = self._make_glow_surface()

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

    def _draw_phosphor_block(self, rect: pygame.Rect) -> None:
        pygame.draw.rect(self.screen, PALETTE["block_fill"], rect)

    def _draw_block(self, x: int, y: int) -> None:
        rect = self._make_playfield_cell_rect(x, y)
        self._draw_phosphor_block(rect)

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

    def _blit_surface_in_band(
        self,
        surface: pygame.Surface,
        anchor: TextAnchor,
        band: VerticalBand,
        target_surface: pygame.Surface | None = None,
    ) -> pygame.Rect:
        x, align = anchor
        top, height = band
        target = self.screen if target_surface is None else target_surface
        rect = surface.get_rect()
        if align == "center":
            rect.centerx = x
        elif align == "right":
            rect.right = x
        else:
            rect.x = x
        rect.y = top + max(0, (height - surface.get_height()) // 2)
        target.blit(surface, rect)
        return rect

    # CRT arcade monitor shell drawing.
    def _draw_background(self) -> None:
        self.screen.fill(PALETTE["bg"])

    def _make_glow_surface(self) -> pygame.Surface:
        pad = SPACING.lg
        size = (
            self.monitor_rect.width + pad * 2,
            self.monitor_rect.height + pad * 2,
        )
        surface = pygame.Surface(size, pygame.SRCALPHA)
        for i in range(8, 0, -1):
            t = i / 8
            alpha = int(21 * t)
            rect = pygame.Rect(
                pad - i * 2,
                pad - i * 2,
                size[0] - (pad - i * 2) * 2,
                size[1] - (pad - i * 2) * 2,
            )
            pygame.draw.rect(
                surface,
                (*PALETTE["neon"], alpha),
                rect,
                border_radius=0,
            )
        return surface

    def _draw_monitor_glow(self) -> None:
        glow_rect = self.glow_surface.get_rect(center=self.monitor_rect.center)
        self.screen.blit(self.glow_surface, glow_rect)

    def _draw_monitor_frame(self) -> None:
        # Outer frame body.
        pygame.draw.rect(
            self.screen,
            PALETTE["monitor_dark"],
            self.monitor_rect,
            border_radius=0,
        )
        inner = self.monitor_rect.inflate(-13, -13)
        pygame.draw.rect(
            self.screen,
            PALETTE["monitor"],
            inner,
            border_radius=0,
        )
        # Inner bevel.
        pygame.draw.rect(
            self.screen,
            PALETTE["monitor_light"],
            inner,
            width=3,
            border_radius=0,
        )
        # Decorative screws.
        screw_offset = SPACING.lg
        corners = [
            (self.monitor_rect.left + screw_offset, self.monitor_rect.top + screw_offset),
            (self.monitor_rect.right - screw_offset, self.monitor_rect.top + screw_offset),
            (self.monitor_rect.left + screw_offset, self.monitor_rect.bottom - screw_offset),
            (self.monitor_rect.right - screw_offset, self.monitor_rect.bottom - screw_offset),
        ]
        for x, y in corners:
            pygame.draw.circle(self.screen, PALETTE["monitor_light"], (x, y), 5)
            pygame.draw.circle(self.screen, PALETTE["monitor_dark"], (x, y), 5, 3)

    def _make_scanline_surface(self) -> pygame.Surface:
        surface = pygame.Surface(self.screen_rect.size, pygame.SRCALPHA)
        dark = (0, 0, 0)
        for y in range(0, self.screen_rect.height, 2):
            pygame.draw.line(
                surface,
                (*dark, 8),
                (0, y),
                (self.screen_rect.width, y),
                1,
            )
        return surface

    def _make_vignette_surface(self) -> pygame.Surface:
        surface = pygame.Surface(self.screen_rect.size, pygame.SRCALPHA)
        cx, cy = self.screen_rect.width // 2, self.screen_rect.height // 2
        max_dist = (cx ** 2 + cy ** 2) ** 0.5
        for y in range(self.screen_rect.height):
            for x in range(self.screen_rect.width):
                dist = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
                t = dist / max_dist
                alpha = int(34 * (t ** 2))
                surface.set_at((x, y), (0, 0, 0, alpha))
        return surface

    # In-screen HUD.
    def _draw_status_bar(self) -> None:
        score_surface = self._render_text_surface(
            f"{self.score:06d}", "score", PALETTE["text_dim"]
        )
        self._blit_surface_in_band(
            score_surface,
            (self.status_bar_rect.x + SPACING.md, "left"),
            (self.status_bar_rect.y, self.status_bar_rect.height),
        )

        stats_surface = self._render_text_surface(
            f"LINES {self.lines:03d}  LEVEL {self.level:02d}",
            "body",
            PALETTE["text_dim"],
        )
        self._blit_surface_in_band(
            stats_surface,
            (self.status_bar_rect.right - SPACING.md, "right"),
            (self.status_bar_rect.y, self.status_bar_rect.height),
        )

    def _draw_playfield(self) -> None:
        pygame.draw.rect(self.screen, PALETTE["screen_bg"], self.playfield_rect)

        # Grid lines.
        grid_color = PALETTE["screen_light"]
        for x in range(1, GAME_LAYOUT.grid_width):
            grid_line_x = self.playfield_rect.x + x * GAME_LAYOUT.grid_size
            pygame.draw.line(
                self.screen,
                grid_color,
                (grid_line_x, self.playfield_rect.y),
                (grid_line_x, self.playfield_rect.bottom - 1),
                1,
            )
        for y in range(1, GAME_LAYOUT.grid_height):
            grid_line_y = self.playfield_rect.y + y * GAME_LAYOUT.grid_size
            pygame.draw.line(
                self.screen,
                grid_color,
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

        # Playfield border (drawn outside the playfield so it doesn't cover blocks).
        outer_border = self.playfield_rect.inflate(
            GAME_LAYOUT.playfield_border_width * 2,
            GAME_LAYOUT.playfield_border_width * 2,
        )
        pygame.draw.rect(
            self.screen,
            PALETTE["screen_light"],
            outer_border,
            GAME_LAYOUT.playfield_border_width,
        )

    def _draw_overlay(self) -> None:
        if self.state == GameState.PLAYING:
            return

        overlay = pygame.Surface(self.playfield_rect.size, pygame.SRCALPHA)
        overlay.fill((*PALETTE["overlay"], OVERLAY_ALPHA))
        self.screen.blit(overlay, self.playfield_rect.topleft)

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
            main_text, "title", PALETTE["screen_bg"]
        )
        sub_surface = self._render_text_surface(
            sub_text, "body", PALETTE["screen_bg"]
        )

        center_x = self.playfield_rect.centerx
        center_y = self.playfield_rect.centery
        main_rect = main_surface.get_rect(center=(center_x, center_y - SPACING.md))
        sub_rect = sub_surface.get_rect(center=(center_x, center_y + SPACING.xl))

        # Dark horizontal band behind the text, spanning the full playfield.
        panel_rect = main_rect.union(sub_rect).inflate(0, SPACING.xl)
        panel_rect.width = self.playfield_rect.width
        panel_rect.centerx = self.playfield_rect.centerx
        panel = pygame.Surface(panel_rect.size, pygame.SRCALPHA)
        panel.fill((*PALETTE["block_fill"], PANEL_ALPHA))
        self.screen.blit(panel, panel_rect.topleft)

        self.screen.blit(main_surface, main_rect)
        self.screen.blit(sub_surface, sub_rect)

    # Title and key hints.
    def _draw_window_title(self) -> None:
        title_surface = self._render_text_surface("TETRIS", "title", PALETTE["neon"])
        title_rect = title_surface.get_rect(centerx=self.screen.get_rect().centerx)
        title_rect.y = max(0, (self.monitor_rect.top - title_rect.height) // 2)
        # Soft neon halo.
        halo = self._render_text_surface("TETRIS", "title", PALETTE["neon_dim"])
        halo = pygame.transform.scale(
            halo,
            (int(halo.get_width() * 1.125), int(halo.get_height() * 1.125)),
        )
        halo.set_alpha(89)
        halo_rect = halo.get_rect(center=title_rect.center)
        self.screen.blit(halo, halo_rect)
        self.screen.blit(title_surface, title_rect)

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
        y = self.monitor_rect.bottom + SPACING.lg
        for line in hints:
            surface = self._render_text_surface(line, "body", PALETTE["text_dim"])
            rect = surface.get_rect(centerx=self.screen.get_rect().centerx, y=y)
            self.screen.blit(surface, rect)
            y += surface.get_height() + SPACING.sm

    def draw(self) -> None:
        self._draw_background()
        self._draw_window_title()
        self._draw_monitor_glow()
        self._draw_monitor_frame()
        self._draw_status_bar()
        self._draw_playfield()
        self.screen.blit(self.scanline_surface, self.screen_rect.topleft)
        self.screen.blit(self.vignette_surface, self.screen_rect.topleft)
        self._draw_overlay()
        self._draw_key_hints()
        pygame.display.flip()
