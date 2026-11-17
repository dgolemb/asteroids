import unittest
from unittest import mock

import pygame

from asteroid import Asteroid
from constants import ASTEROID_MIN_RADIUS, ASTEROID_SCORES, SCREEN_HEIGHT, SCREEN_WIDTH, SHIELD_RADIUS
from hud import Hud
from main import destroy_asteroid, shield_hits
from player import Player
from shape import Shape
from stats import GameStats
from tests.helpers import AsteroidTestCase


class StubField:
    def __init__(self, multiplier):
        self.multiplier = multiplier

    def score_multiplier(self):
        return self.multiplier


class DestroyAsteroidTest(AsteroidTestCase):
    @classmethod
    def setUpClass(cls):
        pygame.font.init()

    def setUp(self):
        super().setUp()
        self.main_log = self.enterContext(mock.patch("main.log_event"))
        self.hud = Hud()
        self.stats = GameStats()

    def destroy(self, kind, multiplier=1.0, source="shot_hit"):
        asteroid = Asteroid(100, 100, ASTEROID_MIN_RADIUS * kind)
        destroy_asteroid(asteroid, StubField(multiplier), self.hud, self.stats, source)
        return asteroid

    def test_adds_the_base_score_at_the_first_level(self):
        for kind, points in ASTEROID_SCORES.items():
            with self.subTest(kind=kind):
                hud = Hud()
                asteroid = Asteroid(100, 100, ASTEROID_MIN_RADIUS * kind)
                destroy_asteroid(asteroid, StubField(1.0), hud, GameStats(), "shot_hit")
                self.assertEqual(hud.score, points)

    def test_score_is_scaled_by_the_level_multiplier(self):
        self.destroy(1, multiplier=1.3)
        self.assertEqual(self.hud.score, 650)

    def test_score_is_rounded_to_a_whole_number(self):
        self.destroy(3, multiplier=1.004)
        self.assertEqual(self.hud.score, 100)
        self.assertIsInstance(self.hud.score, int)

    def test_scores_accumulate_over_several_asteroids(self):
        self.destroy(1)
        self.destroy(2)
        self.assertEqual(self.hud.score, ASTEROID_SCORES[1] + ASTEROID_SCORES[2])

    def test_records_the_size_class_in_the_stats(self):
        self.destroy(3)
        self.destroy(3)
        self.destroy(1)
        self.assertEqual(self.stats.asteroids_destroyed, {1: 1, 2: 0, 3: 2})

    def test_logs_the_source_and_the_awarded_points(self):
        self.destroy(2, multiplier=1.2, source="shield_hit")
        self.main_log.assert_called_once_with("shield_hit", score=300)

    def test_splits_the_asteroid(self):
        asteroid = self.destroy(3)
        self.assertNotIn(asteroid, self.asteroids)
        self.assertEqual(len(self.asteroids), 2)

    def test_small_asteroid_leaves_nothing_behind(self):
        self.destroy(1)
        self.assertEqual(len(self.asteroids), 0)


class ShieldHitsTest(unittest.TestCase):
    def setUp(self):
        self.player = Player(500, 300)

    def test_asteroid_inside_the_shield_is_hit(self):
        self.assertTrue(shield_hits(self.player, Shape(520, 300, 40)))

    def test_asteroid_far_away_is_not_hit(self):
        self.assertFalse(shield_hits(self.player, Shape(900, 300, 40)))

    def test_boundary_is_inclusive(self):
        self.assertTrue(shield_hits(self.player, Shape(500 + SHIELD_RADIUS + 40, 300, 40)))

    def test_just_beyond_the_boundary_is_not_hit(self):
        self.assertFalse(shield_hits(self.player, Shape(500 + SHIELD_RADIUS + 40 + 0.5, 300, 40)))

    def test_bigger_asteroids_are_hit_from_further_away(self):
        distance = SHIELD_RADIUS + 50
        self.assertFalse(shield_hits(self.player, Shape(500 + distance, 300, 20)))
        self.assertTrue(shield_hits(self.player, Shape(500 + distance, 300, 60)))

    def test_distance_is_measured_across_the_horizontal_screen_edge(self):
        player = Player(5, 300)
        self.assertTrue(shield_hits(player, Shape(SCREEN_WIDTH - 5, 300, 20)))

    def test_distance_is_measured_across_the_vertical_screen_edge(self):
        player = Player(500, 5)
        self.assertTrue(shield_hits(player, Shape(500, SCREEN_HEIGHT - 5, 20)))

    def test_diagonal_distance_uses_the_euclidean_length(self):
        offset = (SHIELD_RADIUS + 40) / 2**0.5
        self.assertTrue(shield_hits(self.player, Shape(500 + offset, 300 + offset, 40)))
        self.assertFalse(shield_hits(self.player, Shape(500 + offset + 1, 300 + offset + 1, 40)))


if __name__ == "__main__":
    unittest.main()
