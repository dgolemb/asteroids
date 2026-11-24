import unittest
from unittest import mock

import pygame

from constants import (
    HUD_HEART_SPACING,
    HUD_LINE_SPACING,
    HUD_MARGIN,
    PLAYER_MAX_LIVES,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)
from hud import Hud

FULL = (255, 0, 0)
EMPTY = (60, 60, 60)
HEART_SIZE = 10


def heart_surface(color):
    surface = pygame.Surface((HEART_SIZE, HEART_SIZE))
    surface.fill(color)
    return surface


class HudTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.font.init()

    def setUp(self):
        self.enterContext(mock.patch.object(Hud, "heart_full", heart_surface(FULL)))
        self.enterContext(mock.patch.object(Hud, "heart_empty", heart_surface(EMPTY)))
        self.hud = Hud()
        self.screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))


class HudTextTest(HudTestCase):
    def test_score_line_follows_the_score(self):
        self.assertEqual(self.hud.get_score_line(), "SCORE: 0")
        self.hud.add_score(250)
        self.hud.add_score(500)
        self.assertEqual(self.hud.get_score_line(), "SCORE: 750")

    def test_level_line_follows_the_level(self):
        self.assertEqual(self.hud.get_level_line(), "LEVEL: 1")
        self.hud.level = 4
        self.assertEqual(self.hud.get_level_line(), "LEVEL: 4")

    def test_lose_life_decrements_without_a_floor(self):
        self.hud.lives = 0
        self.hud.lose_life()
        self.assertEqual(self.hud.lives, -1)
        self.assertTrue(self.hud.is_game_over())


class HudDrawTest(HudTestCase):
    def test_draw_text_returns_the_y_of_the_next_line(self):
        next_y = self.hud.draw_text(self.screen, "SCORE: 0", 20)
        self.assertEqual(next_y, 20 + self.hud.font.size("SCORE: 0")[1] + HUD_LINE_SPACING)

    def test_draw_text_is_right_aligned_inside_the_margin(self):
        self.hud.draw_text(self.screen, "SCORE: 0", 20)
        painted = [x for x in range(SCREEN_WIDTH) for y in range(20, 40) if self.screen.get_at((x, y))[:3] != (0, 0, 0)]
        self.assertGreater(len(painted), 0)
        self.assertLess(max(painted), SCREEN_WIDTH - HUD_MARGIN)
        self.assertGreater(min(painted), SCREEN_WIDTH // 2)

    def test_hearts_show_lives_as_full_and_the_rest_as_empty(self):
        self.hud.lives = 2
        top = 100
        self.hud.draw_hearts(self.screen, top)
        first_x = SCREEN_WIDTH - HUD_MARGIN - PLAYER_MAX_LIVES * HEART_SIZE - (PLAYER_MAX_LIVES - 1) * HUD_HEART_SPACING
        colors = [
            self.screen.get_at((first_x + index * (HEART_SIZE + HUD_HEART_SPACING) + 1, top + 1))[:3]
            for index in range(PLAYER_MAX_LIVES)
        ]
        self.assertEqual(colors, [FULL, FULL, EMPTY])

    def test_hearts_all_empty_at_zero_lives(self):
        self.hud.lives = 0
        self.hud.draw_hearts(self.screen, 100)
        full_pixels = sum(1 for x in range(SCREEN_WIDTH - 100, SCREEN_WIDTH) if self.screen.get_at((x, 101))[:3] == FULL)
        self.assertEqual(full_pixels, 0)

    def test_draw_hearts_returns_the_y_of_the_next_line(self):
        self.assertEqual(self.hud.draw_hearts(self.screen, 100), 100 + HEART_SIZE + HUD_LINE_SPACING)

    def test_draw_paints_score_hearts_and_level_top_down(self):
        self.hud.draw(self.screen)
        top_band = pygame.Rect(SCREEN_WIDTH // 2, 0, SCREEN_WIDTH // 2, 120)
        painted_rows = {y for y in range(top_band.top, top_band.bottom) for x in range(top_band.left, top_band.right, 2) if self.screen.get_at((x, y))[:3] != (0, 0, 0)}
        self.assertGreater(len(painted_rows), 0)
        self.assertGreaterEqual(min(painted_rows), HUD_MARGIN - 4)
        self.assertEqual(self.screen.get_at((5, 5))[:3], (0, 0, 0))


if __name__ == "__main__":
    unittest.main()
