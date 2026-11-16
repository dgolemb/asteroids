from enum import Enum
import pygame
from constants import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    MENU_TITLE_FONT_SIZE,
    MENU_SUBTITLE_FONT_SIZE,
    MENU_OPTION_FONT_SIZE,
    MENU_LINE_SPACING,
    MENU_BLINK_INTERVAL_SECONDS,
    MENU_OVERLAY_ALPHA,
    MENU_TEXT_COLOR,
    MENU_SELECTED_COLOR,
    MENU_OPTIONS,
    TOUCH_PAUSE_BUTTON_SIZE,
    TOUCH_PAUSE_BUTTON_MARGIN,
    TOUCH_PAUSE_BUTTON_ALPHA,
)


class GameState(Enum):
    MENU = "menu"
    PLAYING = "playing"
    PAUSED = "paused"
    GAME_OVER = "game_over"


class Menu:
    def __init__(self) -> None:
        self.title_font = pygame.font.Font(None, MENU_TITLE_FONT_SIZE)
        self.subtitle_font = pygame.font.Font(None, MENU_SUBTITLE_FONT_SIZE)
        self.option_font = pygame.font.Font(None, MENU_OPTION_FONT_SIZE)
        self.overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.overlay.set_alpha(MENU_OVERLAY_ALPHA)
        self.overlay.fill("black")
        self.selected = 0
        self.blink_time = 0.0
        self.touch_mode = False

    def reset_selection(self) -> None:
        self.selected = 0

    def set_selection(self, index: int) -> None:
        self.selected = index % len(MENU_OPTIONS)

    def reset_blink(self) -> None:
        self.blink_time = 0.0

    def move_selection(self, step: int) -> None:
        self.selected = (self.selected + step) % len(MENU_OPTIONS)

    def selected_option(self) -> str:
        return MENU_OPTIONS[self.selected]

    def is_blink_visible(self) -> bool:
        return int(self.blink_time / MENU_BLINK_INTERVAL_SECONDS) % 2 == 0

    def update(self, dt: float) -> None:
        self.blink_time += dt

    def draw_centered(self, screen: pygame.Surface, font: pygame.font.Font, text: str, color, center_y: float) -> pygame.Rect:
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect(center=(SCREEN_WIDTH / 2, center_y))
        screen.blit(text_surface, text_rect)
        return text_rect

    def draw_title_screen(self, screen: pygame.Surface) -> None:
        center_y = SCREEN_HEIGHT / 2
        title_surface = self.title_font.render("NEW GAME", True, MENU_SELECTED_COLOR)
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH / 2, center_y))
        if self.is_blink_visible():
            screen.blit(title_surface, title_rect)
        subtitle_y = title_rect.bottom + MENU_LINE_SPACING + MENU_SUBTITLE_FONT_SIZE / 2
        start_text = "Tap to start." if self.touch_mode else "Press ENTER to start."
        start_rect = self.draw_centered(screen, self.subtitle_font, start_text, MENU_TEXT_COLOR, subtitle_y)
        if self.touch_mode:
            return
        exit_y = start_rect.bottom + MENU_LINE_SPACING / 2 + MENU_SUBTITLE_FONT_SIZE / 2
        self.draw_centered(screen, self.subtitle_font, "Press ESC to exit.", MENU_TEXT_COLOR, exit_y)

    def pause_option_rects(self) -> list[pygame.Rect]:
        total_height = len(MENU_OPTIONS) * MENU_OPTION_FONT_SIZE + (len(MENU_OPTIONS) - 1) * MENU_LINE_SPACING
        y = SCREEN_HEIGHT / 2 - total_height / 2 + MENU_OPTION_FONT_SIZE / 2
        rects = []
        for _ in MENU_OPTIONS:
            rect = pygame.Rect(0, 0, SCREEN_WIDTH / 2, MENU_OPTION_FONT_SIZE + MENU_LINE_SPACING)
            rect.center = (SCREEN_WIDTH / 2, y)
            rects.append(rect)
            y += MENU_OPTION_FONT_SIZE + MENU_LINE_SPACING
        return rects

    def pause_option_at(self, position: pygame.Vector2) -> int | None:
        for index, rect in enumerate(self.pause_option_rects()):
            if rect.collidepoint(position):
                return index
        return None

    def draw_pause_menu(self, screen: pygame.Surface) -> None:
        screen.blit(self.overlay, (0, 0))
        for index, (option, rect) in enumerate(zip(MENU_OPTIONS, self.pause_option_rects())):
            color = MENU_SELECTED_COLOR if index == self.selected else MENU_TEXT_COLOR
            self.draw_centered(screen, self.option_font, option, color, rect.centery)

    def pause_button_rect(self) -> pygame.Rect:
        return pygame.Rect(
            SCREEN_WIDTH / 2 + TOUCH_PAUSE_BUTTON_MARGIN,
            TOUCH_PAUSE_BUTTON_MARGIN,
            TOUCH_PAUSE_BUTTON_SIZE,
            TOUCH_PAUSE_BUTTON_SIZE,
        )

    def is_pause_button_hit(self, position: pygame.Vector2) -> bool:
        hit_rect = self.pause_button_rect().inflate(TOUCH_PAUSE_BUTTON_MARGIN * 2, TOUCH_PAUSE_BUTTON_MARGIN * 2)
        return hit_rect.collidepoint(position)

    def draw_pause_button(self, screen: pygame.Surface) -> pygame.Rect:
        rect = self.pause_button_rect()
        button = pygame.Surface(rect.size, pygame.SRCALPHA)
        color = (*MENU_SELECTED_COLOR, TOUCH_PAUSE_BUTTON_ALPHA)
        pygame.draw.rect(button, color, button.get_rect(), width=3, border_radius=TOUCH_PAUSE_BUTTON_SIZE // 5)
        bar_width = TOUCH_PAUSE_BUTTON_SIZE // 8
        bar_height = TOUCH_PAUSE_BUTTON_SIZE // 2
        for bar_x in (TOUCH_PAUSE_BUTTON_SIZE // 2 - bar_width * 1.5, TOUCH_PAUSE_BUTTON_SIZE // 2 + bar_width * 0.5):
            pygame.draw.rect(button, color, (bar_x, (TOUCH_PAUSE_BUTTON_SIZE - bar_height) // 2, bar_width, bar_height))
        screen.blit(button, rect)
        return rect

    def draw_game_over(self, screen: pygame.Surface, score: int, stat_lines: list[str]) -> None:
        center_y = SCREEN_HEIGHT / 3
        score_rect = self.draw_centered(screen, self.title_font, f"Final score: {score}", MENU_SELECTED_COLOR, center_y)
        bottom = score_rect.bottom
        for line in stat_lines:
            line_y = bottom + MENU_LINE_SPACING / 2 + MENU_SUBTITLE_FONT_SIZE / 2
            bottom = self.draw_centered(screen, self.subtitle_font, line, MENU_TEXT_COLOR, line_y).bottom
        thanks_y = bottom + MENU_LINE_SPACING + MENU_OPTION_FONT_SIZE / 2
        thanks_rect = self.draw_centered(screen, self.option_font, "Thanks for playing!", MENU_SELECTED_COLOR, thanks_y)
        hint_y = thanks_rect.bottom + MENU_LINE_SPACING + MENU_SUBTITLE_FONT_SIZE / 2
        hint_text = "Tap to continue." if self.touch_mode else "Press ENTER to continue."
        self.draw_centered(screen, self.subtitle_font, hint_text, MENU_TEXT_COLOR, hint_y)
