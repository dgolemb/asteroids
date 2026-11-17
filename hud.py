import pygame
from constants import (
    SCREEN_WIDTH,
    HUD_FONT_SIZE,
    HUD_MARGIN,
    HUD_LINE_SPACING,
    HUD_HEART_SPACING,
    PLAYER_START_LIVES,
    PLAYER_MAX_LIVES,
)


class Hud:
    heart_full: pygame.Surface | None = None
    heart_empty: pygame.Surface | None = None

    def __init__(self) -> None:
        self.font = pygame.font.Font(None, HUD_FONT_SIZE)
        self.score = 0
        self.lives = PLAYER_START_LIVES
        self.level = 1

    def add_score(self, points: int) -> None:
        self.score += points

    def lose_life(self) -> None:
        self.lives -= 1

    def add_life(self) -> None:
        self.lives = min(self.lives + 1, PLAYER_MAX_LIVES)

    def has_full_lives(self) -> bool:
        return self.lives >= PLAYER_MAX_LIVES

    def is_game_over(self) -> bool:
        return self.lives <= 0

    def get_score_line(self) -> str:
        return f"SCORE: {self.score}"

    def get_level_line(self) -> str:
        return f"LEVEL: {self.level}"

    def draw_text(self, screen: pygame.Surface, line: str, y: int) -> int:
        text_surface = self.font.render(line, True, "white")
        text_rect = text_surface.get_rect()
        text_rect.topright = (SCREEN_WIDTH - HUD_MARGIN, y)
        screen.blit(text_surface, text_rect)
        return y + text_rect.height + HUD_LINE_SPACING

    def draw_hearts(self, screen: pygame.Surface, y: int) -> int:
        heart_width, heart_height = self.heart_full.get_size()
        x = SCREEN_WIDTH - HUD_MARGIN - PLAYER_MAX_LIVES * heart_width - (PLAYER_MAX_LIVES - 1) * HUD_HEART_SPACING
        for index in range(PLAYER_MAX_LIVES):
            heart = self.heart_full if index < self.lives else self.heart_empty
            screen.blit(heart, (x + index * (heart_width + HUD_HEART_SPACING), y))
        return y + heart_height + HUD_LINE_SPACING

    def draw(self, screen: pygame.Surface) -> None:
        y = self.draw_text(screen, self.get_score_line(), HUD_MARGIN)
        y = self.draw_hearts(screen, y)
        self.draw_text(screen, self.get_level_line(), y)
