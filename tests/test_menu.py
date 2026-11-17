import unittest

import pygame

from constants import (
    MENU_OPTION_CONTINUE,
    MENU_OPTION_EXIT,
    MENU_SELECTED_COLOR,
    MENU_TEXT_COLOR,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    TOUCH_PAUSE_BUTTON_SIZE,
)
from menu import GameState, Menu


class RecordingFont:
    def __init__(self):
        self.rendered = []

    def render(self, text, antialias, color):
        self.rendered.append(text)
        return pygame.Surface((10, 10))


def count_pixels(surface, rect, color):
    return sum(
        1
        for x in range(rect.left, rect.right)
        for y in range(rect.top, rect.bottom)
        if surface.get_at((x, y))[:3] == color
    )


class MenuTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.font.init()

    def setUp(self):
        self.menu = Menu()

    def with_recording_fonts(self):
        recorder = RecordingFont()
        self.menu.title_font = recorder
        self.menu.subtitle_font = recorder
        self.menu.option_font = recorder
        return recorder


class GameStateTest(unittest.TestCase):
    def test_has_the_four_screens(self):
        self.assertEqual({state.name for state in GameState}, {"MENU", "PLAYING", "PAUSED", "GAME_OVER"})


class SelectionTest(MenuTestCase):
    def test_starts_on_the_first_option(self):
        self.assertEqual(self.menu.selected_option(), MENU_OPTION_CONTINUE)

    def test_move_selection_wraps_forward(self):
        self.menu.move_selection(1)
        self.assertEqual(self.menu.selected_option(), MENU_OPTION_EXIT)
        self.menu.move_selection(1)
        self.assertEqual(self.menu.selected_option(), MENU_OPTION_CONTINUE)

    def test_move_selection_wraps_backward(self):
        self.menu.move_selection(-1)
        self.assertEqual(self.menu.selected_option(), MENU_OPTION_EXIT)

    def test_set_selection_wraps_out_of_range_indexes(self):
        self.menu.set_selection(1)
        self.assertEqual(self.menu.selected, 1)
        self.menu.set_selection(2)
        self.assertEqual(self.menu.selected, 0)
        self.menu.set_selection(-1)
        self.assertEqual(self.menu.selected, 1)

    def test_reset_selection_returns_to_the_first_option(self):
        self.menu.set_selection(1)
        self.menu.reset_selection()
        self.assertEqual(self.menu.selected, 0)


class BlinkTest(MenuTestCase):
    def test_visible_at_the_start(self):
        self.assertTrue(self.menu.is_blink_visible())

    def test_hides_after_one_interval_and_shows_again_after_two(self):
        self.menu.update(0.5)
        self.assertFalse(self.menu.is_blink_visible())
        self.menu.update(0.5)
        self.assertTrue(self.menu.is_blink_visible())

    def test_stays_visible_just_before_the_interval(self):
        self.menu.update(0.49)
        self.assertTrue(self.menu.is_blink_visible())

    def test_reset_blink_makes_it_visible_again(self):
        self.menu.update(0.5)
        self.menu.reset_blink()
        self.assertTrue(self.menu.is_blink_visible())
        self.assertEqual(self.menu.blink_time, 0.0)


class PauseOptionsTest(MenuTestCase):
    def test_one_rect_per_option_stacked_top_to_bottom(self):
        rects = self.menu.pause_option_rects()
        self.assertEqual(len(rects), 2)
        self.assertLess(rects[0].centery, rects[1].centery)
        self.assertFalse(rects[0].colliderect(rects[1]))

    def test_rects_are_centered_on_the_screen(self):
        rects = self.menu.pause_option_rects()
        for rect in rects:
            self.assertEqual(rect.centerx, SCREEN_WIDTH // 2)
        self.assertEqual((rects[0].centery + rects[1].centery) / 2, SCREEN_HEIGHT / 2)

    def test_option_at_a_position(self):
        first, second = self.menu.pause_option_rects()
        self.assertEqual(self.menu.pause_option_at(pygame.Vector2(first.center)), 0)
        self.assertEqual(self.menu.pause_option_at(pygame.Vector2(second.center)), 1)

    def test_option_at_the_border_between_rects_belongs_to_the_lower_one(self):
        first, second = self.menu.pause_option_rects()
        self.assertEqual(self.menu.pause_option_at(pygame.Vector2(first.centerx, second.top)), 1)
        self.assertEqual(self.menu.pause_option_at(pygame.Vector2(first.centerx, second.top - 1)), 0)

    def test_no_option_outside_the_rects(self):
        first, _ = self.menu.pause_option_rects()
        self.assertIsNone(self.menu.pause_option_at(pygame.Vector2(5, first.centery)))
        self.assertIsNone(self.menu.pause_option_at(pygame.Vector2(SCREEN_WIDTH / 2, 5)))


class PauseButtonTest(MenuTestCase):
    def test_button_sits_in_the_top_middle_area(self):
        rect = self.menu.pause_button_rect()
        self.assertEqual(rect.size, (TOUCH_PAUSE_BUTTON_SIZE, TOUCH_PAUSE_BUTTON_SIZE))
        self.assertGreater(rect.left, SCREEN_WIDTH / 2)
        self.assertLess(rect.top, SCREEN_HEIGHT / 4)

    def test_hit_inside_the_button(self):
        self.assertTrue(self.menu.is_pause_button_hit(pygame.Vector2(self.menu.pause_button_rect().center)))

    def test_hit_area_is_larger_than_the_button(self):
        rect = self.menu.pause_button_rect()
        self.assertTrue(self.menu.is_pause_button_hit(pygame.Vector2(rect.left - 10, rect.centery)))
        self.assertTrue(self.menu.is_pause_button_hit(pygame.Vector2(rect.right + 10, rect.centery)))

    def test_miss_outside_the_hit_area(self):
        rect = self.menu.pause_button_rect()
        self.assertFalse(self.menu.is_pause_button_hit(pygame.Vector2(rect.left - 20, rect.centery)))
        self.assertFalse(self.menu.is_pause_button_hit(pygame.Vector2(rect.right + 20, rect.centery)))
        self.assertFalse(self.menu.is_pause_button_hit(pygame.Vector2(rect.centerx, rect.bottom + 20)))

    def test_draw_returns_the_rect_and_paints_it(self):
        screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        rect = self.menu.draw_pause_button(screen)
        self.assertEqual(rect, self.menu.pause_button_rect())
        self.assertNotEqual(screen.get_at((rect.left + 1, rect.centery))[:3], (0, 0, 0))
        self.assertEqual(screen.get_at((5, 5))[:3], (0, 0, 0))


class DrawPauseMenuTest(MenuTestCase):
    def test_overlay_dims_the_screen_behind_the_options(self):
        screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        screen.fill((255, 255, 255))
        self.menu.draw_pause_menu(screen)
        dimmed = screen.get_at((5, 5))[:3]
        self.assertLess(dimmed[0], 255)
        self.assertEqual(dimmed[0], dimmed[1])

    def test_selected_option_uses_the_highlight_color(self):
        screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        first, second = self.menu.pause_option_rects()
        self.menu.draw_pause_menu(screen)
        self.assertGreater(count_pixels(screen, first, MENU_SELECTED_COLOR), 0)
        self.assertEqual(count_pixels(screen, second, MENU_SELECTED_COLOR), 0)
        self.assertGreater(count_pixels(screen, second, MENU_TEXT_COLOR), 0)

    def test_highlight_follows_the_selection(self):
        screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        first, second = self.menu.pause_option_rects()
        self.menu.move_selection(1)
        self.menu.draw_pause_menu(screen)
        self.assertEqual(count_pixels(screen, first, MENU_SELECTED_COLOR), 0)
        self.assertGreater(count_pixels(screen, second, MENU_SELECTED_COLOR), 0)


class DrawTitleScreenTest(MenuTestCase):
    def title_area(self):
        return pygame.Rect(400, SCREEN_HEIGHT // 2 - 20, 480, 40)

    def test_title_is_drawn_while_the_blink_is_visible(self):
        screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.menu.draw_title_screen(screen)
        self.assertGreater(count_pixels(screen, self.title_area(), MENU_SELECTED_COLOR), 0)

    def test_title_is_hidden_while_the_blink_is_off(self):
        screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.menu.update(0.5)
        self.menu.draw_title_screen(screen)
        self.assertEqual(count_pixels(screen, self.title_area(), MENU_SELECTED_COLOR), 0)

    def test_keyboard_hints_on_desktop(self):
        recorder = self.with_recording_fonts()
        self.menu.draw_title_screen(pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)))
        self.assertEqual(recorder.rendered, ["NEW GAME", "Press ENTER to start.", "Press ESC to exit."])

    def test_touch_hint_in_touch_mode(self):
        recorder = self.with_recording_fonts()
        self.menu.touch_mode = True
        self.menu.draw_title_screen(pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)))
        self.assertEqual(recorder.rendered, ["NEW GAME", "Tap to start."])


class DrawGameOverTest(MenuTestCase):
    def test_shows_score_stats_and_keyboard_hint(self):
        recorder = self.with_recording_fonts()
        self.menu.draw_game_over(pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)), 1234, ["line one", "line two"])
        self.assertEqual(
            recorder.rendered,
            ["Final score: 1234", "line one", "line two", "Thanks for playing!", "Press ENTER to continue."],
        )

    def test_touch_mode_asks_for_a_tap(self):
        recorder = self.with_recording_fonts()
        self.menu.touch_mode = True
        self.menu.draw_game_over(pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)), 0, [])
        self.assertEqual(recorder.rendered[-1], "Tap to continue.")

    def test_renders_with_real_fonts(self):
        screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.menu.draw_game_over(screen, 500, ["a", "b", "c"])
        self.assertGreater(count_pixels(screen, pygame.Rect(200, 190, 880, 100), MENU_SELECTED_COLOR), 0)


if __name__ == "__main__":
    unittest.main()
