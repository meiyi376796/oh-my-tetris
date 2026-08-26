"""Pygame UI window, layout, and rendering helpers for the Tetris runtime."""

import os

import pygame

from tetris_core import GameState, Grid, Tetromino
from tetris_ui_config import (
    CHICAGO_FONT_PATH,
    Color,
    CONTROL_BINDINGS,
    FONT_SIZES,
    FontKey,
    FontMap,
    GAME_LAYOUT,
    GRAIN_ALPHA,
    OVERLAY_ALPHA,
    PALETTE,
    SCANLINE_ALPHA,
    SCREEN,
    SPACING,
)
from tetris_ui_helpers import (
    NEXT_BOX_SIZE,
    NEXT_CELL_INSET,
    NEXT_CELL_SIZE,
    TITLE_CENTER_Y,
    get_info_column_rect,
    get_playfield_rect,
    get_visible_piece_positions,
    make_inset_rect,
)


class TetrisUI:
    """Shared Pygame window, layout state, and rendering helpers."""

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

    @property
    def next_piece(self) -> Tetromino | None:
        raise NotImplementedError

    @property
    def clearing_rows(self) -> list[int]:
        raise NotImplementedError

    @property
    def line_clear_step(self) -> int:
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
        self.info_column_rect: pygame.Rect = get_info_column_rect()

        self.shell_texture: pygame.Surface = self._make_shell_texture()
        self.scanline_surface: pygame.Surface = self._make_scanline_surface(
            self.playfield_rect.size
        )
        self.next_scanline_surface: pygame.Surface = self._make_scanline_surface(
            (NEXT_BOX_SIZE, NEXT_BOX_SIZE)
        )
        self.overlay_surface: pygame.Surface = self._make_overlay_surface(
            self.playfield_rect.size
        )
        self.next_overlay_surface: pygame.Surface = self._make_overlay_surface(
            (NEXT_BOX_SIZE, NEXT_BOX_SIZE)
        )

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

    def _draw_lcd_cell(self, rect: pygame.Rect) -> None:
        pygame.draw.rect(self.screen, PALETTE["block"], rect)

    def _draw_block(self, x: int, y: int) -> None:
        self._draw_lcd_cell(self._make_playfield_cell_rect(x, y))

    def _draw_ghost_block(self, x: int, y: int) -> None:
        rect = self._make_playfield_cell_rect(x, y)
        pygame.draw.rect(self.screen, PALETTE["dim"], rect, 1)

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

    # Hairline frame just outside a rect.
    def _draw_hairline_frame(self, rect: pygame.Rect) -> None:
        width = GAME_LAYOUT.playfield_border_width
        pygame.draw.rect(self.screen, PALETTE["dim"], rect.inflate(width * 2, width * 2), width)

    def _draw_background(self) -> None:
        self.screen.fill(PALETTE["shell"])
        self.screen.blit(self.shell_texture, (0, 0))

    # Ordered-dither grain over the shell.
    def _make_shell_texture(self) -> pygame.Surface:
        surface = pygame.Surface((SCREEN.width, SCREEN.height), pygame.SRCALPHA)
        for y in range(0, SCREEN.height, 2):
            for x in range(0, SCREEN.width, 2):
                if (x // 2 + y // 2) % 2 == 0:
                    surface.set_at((x, y), (255, 255, 255, GRAIN_ALPHA))
        return surface

    # Power LED: solid while playing, blinking while paused, dark otherwise.
    def _draw_power_led(self) -> None:
        center = (self.playfield_rect.x // 2, self.playfield_rect.centery)
        lit = self.state == GameState.PLAYING
        if self.state == GameState.PAUSED:
            lit = (pygame.time.get_ticks() // 400) % 2 == 0
        color = PALETTE["led_on"] if lit else PALETTE["led_off"]
        pygame.draw.circle(self.screen, color, center, 3)

    def _make_scanline_surface(self, size: tuple[int, int]) -> pygame.Surface:
        surface = pygame.Surface(size, pygame.SRCALPHA)
        for y in range(0, size[1], 2):
            pygame.draw.line(
                surface,
                (0, 0, 0, SCANLINE_ALPHA),
                (0, y),
                (size[0], y),
                1,
            )
        return surface

    def _make_overlay_surface(self, size: tuple[int, int]) -> pygame.Surface:
        surface = pygame.Surface(size, pygame.SRCALPHA)
        surface.fill((*PALETTE["block"], OVERLAY_ALPHA))
        return surface

    # Title flanked by hairline rules.
    def _draw_title(self) -> None:
        center_x = self.screen.get_rect().centerx
        title_surface = self._render_text_surface(
            "TETRIS", "title", PALETTE["ink"], tracking=10
        )
        title_rect = title_surface.get_rect(center=(center_x, TITLE_CENTER_Y))
        self.screen.blit(title_surface, title_rect)

        rule_y = title_rect.centery
        rule_inset = self.playfield_rect.x - GAME_LAYOUT.playfield_border_width
        gap = SPACING.md
        for start_x, end_x in (
            (rule_inset, title_rect.left - gap),
            (title_rect.right + gap, SCREEN.width - rule_inset - 1),
        ):
            pygame.draw.line(
                self.screen,
                PALETTE["dim"],
                (start_x, rule_y),
                (end_x, rule_y),
                1,
            )

    def _compute_next_box_rect(self) -> pygame.Rect:
        column = self.info_column_rect
        label = self._render_text_surface("NEXT", "body", PALETTE["dim"], tracking=2)
        section_height = column.height // 4
        block_height = label.get_height() + SPACING.sm + NEXT_BOX_SIZE
        slot_top = column.y + 3 * section_height
        rect = pygame.Rect(0, 0, NEXT_BOX_SIZE, NEXT_BOX_SIZE)
        rect.centerx = column.centerx
        rect.y = slot_top + (section_height - block_height) // 2 + label.get_height() + SPACING.sm
        return rect

    # Right info column: four sections, each block centered in its slot.
    def _draw_info_column(self) -> None:
        column = self.info_column_rect
        section_height = column.height // 4

        def block_top(index: int, height: int) -> int:
            slot_top = column.y + index * section_height
            return slot_top + (section_height - height) // 2

        stats = (
            ("SCORE", f"{self.score:08d}"),
            ("LINES", f"{self.lines:04d}"),
            ("LEVEL", f"{self.level:03d}"),
        )
        for index, (label, value) in enumerate(stats):
            label_surface = self._render_text_surface(
                label, "body", PALETTE["dim"], tracking=2
            )
            value_surface = self._render_text_surface(
                value, "score", PALETTE["ink"]
            )
            y = block_top(
                index,
                label_surface.get_height() + SPACING.xs + value_surface.get_height(),
            )
            self.screen.blit(
                label_surface,
                label_surface.get_rect(centerx=column.centerx, y=y),
            )
            self.screen.blit(
                value_surface,
                value_surface.get_rect(
                    centerx=column.centerx, y=y + label_surface.get_height() + SPACING.xs
                ),
            )

        label_surface = self._render_text_surface(
            "NEXT", "body", PALETTE["dim"], tracking=2
        )
        box_rect = self._compute_next_box_rect()
        self.screen.blit(
            label_surface,
            label_surface.get_rect(
                centerx=column.centerx, y=box_rect.y - SPACING.sm - label_surface.get_height()
            ),
        )

        # Miniature LCD: shows the piece while playing or paused; dimmed unless playing.
        pygame.draw.rect(self.screen, PALETTE["screen"], box_rect)

        piece = self.next_piece
        if piece is not None and self.state in (GameState.PLAYING, GameState.PAUSED):
            matrix = piece.get_shape_matrix()
            cells = [
                (x, y)
                for y, row in enumerate(matrix)
                for x, cell in enumerate(row)
                if cell
            ]
            min_x = min(x for x, _ in cells)
            min_y = min(y for _, y in cells)
            max_x = max(x for x, _ in cells)
            max_y = max(y for _, y in cells)
            origin_x = box_rect.centerx - (max_x - min_x + 1) * NEXT_CELL_SIZE // 2
            origin_y = box_rect.centery - (max_y - min_y + 1) * NEXT_CELL_SIZE // 2
            for x, y in cells:
                rect = make_inset_rect(
                    origin_x + (x - min_x) * NEXT_CELL_SIZE,
                    origin_y + (y - min_y) * NEXT_CELL_SIZE,
                    NEXT_CELL_SIZE,
                    NEXT_CELL_INSET,
                )
                self._draw_lcd_cell(rect)

        if self.state != GameState.PLAYING:
            self.screen.blit(self.next_overlay_surface, box_rect.topleft)
        self.screen.blit(self.next_scanline_surface, box_rect.topleft)
        self._draw_hairline_frame(box_rect)

    # NES line clear animation erases two columns per step, center outward.
    def _is_cell_erased(self, x: int, y: int, clearing_rows: set[int]) -> bool:
        step = self.line_clear_step
        if step <= 0 or y not in clearing_rows:
            return False
        center_left = GAME_LAYOUT.grid_width // 2 - 1
        return center_left - (step - 1) <= x <= center_left + step

    def _draw_playfield(self) -> None:
        pygame.draw.rect(self.screen, PALETTE["screen"], self.playfield_rect)

        # Grid hairlines.
        for x in range(1, GAME_LAYOUT.grid_width):
            grid_line_x = self.playfield_rect.x + x * GAME_LAYOUT.grid_size
            pygame.draw.line(
                self.screen,
                PALETTE["ink"],
                (grid_line_x, self.playfield_rect.y),
                (grid_line_x, self.playfield_rect.bottom - 1),
                1,
            )
        for y in range(1, GAME_LAYOUT.grid_height):
            grid_line_y = self.playfield_rect.y + y * GAME_LAYOUT.grid_size
            pygame.draw.line(
                self.screen,
                PALETTE["ink"],
                (self.playfield_rect.x, grid_line_y),
                (self.playfield_rect.right - 1, grid_line_y),
                1,
            )

        # Locked blocks.
        clearing_rows = set(self.clearing_rows)
        for y in range(GAME_LAYOUT.grid_height):
            for x in range(GAME_LAYOUT.grid_width):
                if self.grid[y][x] and not self._is_cell_erased(x, y, clearing_rows):
                    self._draw_block(x, y)

        # Ghost piece.
        if self.state in (GameState.PLAYING, GameState.PAUSED) and self.current_piece:
            shadow = self._get_shadow_piece()
            for x, y in get_visible_piece_positions(shadow):
                self._draw_ghost_block(x, y)

        # Current piece.
        current_piece = self.current_piece
        if current_piece:
            for x, y in get_visible_piece_positions(current_piece):
                self._draw_block(x, y)

        self._draw_hairline_frame(self.playfield_rect)

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

    # Key hints on a fixed four-column grid, cells left-aligned.
    def _draw_key_hints(self) -> None:
        rows = tuple(
            tuple(
                self._render_text_surface(
                    f"{b.key_label}  {b.help_text}",
                    "body",
                    PALETTE["dim"],
                )
                for b in CONTROL_BINDINGS[i:i + 4]
            )
            for i in range(0, len(CONTROL_BINDINGS), 4)
        )
        cell_width = max(cell.get_width() for row in rows for cell in row)
        pitch = cell_width + SPACING.lg
        start_x = self.screen.get_rect().centerx - (pitch * 4 - SPACING.lg) // 2
        y = self.playfield_rect.bottom + SPACING.lg
        for row in rows:
            for index, cell in enumerate(row):
                self.screen.blit(cell, (start_x + index * pitch, y))
            y += max(cell.get_height() for cell in row) + SPACING.sm

    def draw(self) -> None:
        self._draw_background()
        self._draw_title()
        self._draw_power_led()
        self._draw_info_column()
        self._draw_playfield()
        self._draw_overlay_dim()
        self.screen.blit(self.scanline_surface, self.playfield_rect.topleft)
        self._draw_overlay_text()
        self._draw_key_hints()
        pygame.display.flip()
