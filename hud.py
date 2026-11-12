import pygame
from constants import SCREEN_WIDTH, HUD_FONT_SIZE, HUD_MARGIN, HUD_LINE_SPACING


class Hud:
    def __init__(self) -> None:
        self.font = pygame.font.Font(None, HUD_FONT_SIZE)
        self.score = 0

    def add_score(self, points: int) -> None:
        self.score += points

    def get_lines(self) -> list[str]:
        return [f"SCORE: {self.score}"]

    def draw(self, screen: pygame.Surface) -> None:
        y = HUD_MARGIN
        for line in self.get_lines():
            text_surface = self.font.render(line, True, "white")
            text_rect = text_surface.get_rect()
            text_rect.topright = (SCREEN_WIDTH - HUD_MARGIN, y)
            screen.blit(text_surface, text_rect)
            y += text_rect.height + HUD_LINE_SPACING
