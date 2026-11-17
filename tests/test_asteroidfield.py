import unittest
from unittest import mock

import pygame

from asteroid import Asteroid
from asteroidfield import AsteroidField
from constants import ASTEROID_KINDS, ASTEROID_MIN_RADIUS, SCREEN_HEIGHT, SCREEN_WIDTH
from tests.helpers import AsteroidTestCase


class AsteroidFieldTestCase(AsteroidTestCase):
    def setUp(self):
        super().setUp()
        self.fields = pygame.sprite.Group()
        self.enterContext(mock.patch.object(AsteroidField, "containers", self.fields, create=True))
        self.field_log = self.enterContext(mock.patch("asteroidfield.log_event"))
        self.field = AsteroidField(self.asteroids)

    def fill_with_asteroids(self, count):
        for _ in range(count):
            Asteroid(100, 100, ASTEROID_MIN_RADIUS)


class DifficultyFormulasTest(AsteroidFieldTestCase):
    def test_first_level_values(self):
        self.assertEqual(self.field.level, 1)
        self.assertAlmostEqual(self.field.level_duration(), 30)
        self.assertAlmostEqual(self.field.speed_multiplier(), 1.0)
        self.assertAlmostEqual(self.field.score_multiplier(), 1.0)
        self.assertAlmostEqual(self.field.spawn_interval(), 0.8)
        self.assertEqual(self.field.max_count(), 10)

    def test_third_level_values(self):
        self.field.level = 3
        self.assertAlmostEqual(self.field.level_duration(), 50)
        self.assertAlmostEqual(self.field.speed_multiplier(), 1.2)
        self.assertAlmostEqual(self.field.score_multiplier(), 1.2)
        self.assertAlmostEqual(self.field.spawn_interval(), 0.648)
        self.assertEqual(self.field.max_count(), 30)

    def test_levels_get_longer(self):
        durations = []
        for level in range(1, 5):
            self.field.level = level
            durations.append(self.field.level_duration())
        self.assertEqual(durations, [30, 40, 50, 60])

    def test_spawn_interval_shrinks_every_level(self):
        intervals = []
        for level in range(1, 6):
            self.field.level = level
            intervals.append(self.field.spawn_interval())
        self.assertEqual(intervals, sorted(intervals, reverse=True))
        self.assertEqual(len(set(intervals)), 5)

    def test_max_count_reaches_the_cap_and_stays_there(self):
        counts = {}
        for level in (9, 10, 11, 20):
            self.field.level = level
            counts[level] = self.field.max_count()
        self.assertEqual(counts, {9: 90, 10: 100, 11: 100, 20: 100})


class LevelProgressionTest(AsteroidFieldTestCase):
    def setUp(self):
        super().setUp()
        self.enterContext(mock.patch.object(self.field, "spawn"))

    def test_level_does_not_change_before_the_level_duration(self):
        self.field.update(29.9)
        self.assertEqual(self.field.level, 1)
        self.field_log.assert_not_called()

    def test_level_rises_when_the_duration_is_reached(self):
        self.field.update(30)
        self.assertEqual(self.field.level, 2)
        self.assertAlmostEqual(self.field.level_timer, 0)
        self.field_log.assert_called_once_with("level_up", level=2)

    def test_leftover_time_carries_over_to_the_next_level(self):
        self.field.update(35)
        self.assertEqual(self.field.level, 2)
        self.assertAlmostEqual(self.field.level_timer, 5)

    def test_second_level_needs_the_longer_duration(self):
        self.field.update(30)
        self.field.update(39.5)
        self.assertEqual(self.field.level, 2)
        self.field.update(0.5)
        self.assertEqual(self.field.level, 3)
        self.assertEqual(self.field_log.call_args_list[-1], mock.call("level_up", level=3))

    def test_level_timer_accumulates_over_many_small_steps(self):
        for _ in range(59):
            self.field.update(0.5)
        self.assertEqual(self.field.level, 1)
        self.field.update(0.5)
        self.assertEqual(self.field.level, 2)


class SpawnTimingTest(AsteroidFieldTestCase):
    def test_no_spawn_when_the_interval_is_exactly_reached(self):
        self.field.update(self.field.spawn_interval())
        self.assertEqual(len(self.asteroids), 0)

    def test_spawns_one_asteroid_once_the_interval_is_exceeded(self):
        self.field.update(self.field.spawn_interval() + 0.001)
        self.assertEqual(len(self.asteroids), 1)

    def test_spawn_timer_restarts_after_a_spawn(self):
        self.field.update(self.field.spawn_interval() + 0.001)
        self.assertEqual(self.field.spawn_timer, 0)
        self.field.update(0.1)
        self.assertEqual(len(self.asteroids), 1)

    def test_spawns_repeatedly_over_time(self):
        for _ in range(5):
            self.field.update(self.field.spawn_interval() + 0.001)
        self.assertEqual(len(self.asteroids), 5)

    def test_stops_spawning_at_the_asteroid_limit(self):
        self.fill_with_asteroids(self.field.max_count())
        self.field.update(self.field.spawn_interval() + 0.001)
        self.assertEqual(len(self.asteroids), self.field.max_count())
        self.assertEqual(self.field.spawn_timer, 0)

    def test_still_spawns_just_below_the_asteroid_limit(self):
        self.fill_with_asteroids(self.field.max_count() - 1)
        self.field.update(self.field.spawn_interval() + 0.001)
        self.assertEqual(len(self.asteroids), self.field.max_count())

    def test_higher_level_raises_the_limit(self):
        self.field.level = 2
        self.fill_with_asteroids(10)
        self.field.update(self.field.spawn_interval() + 0.001)
        self.assertEqual(len(self.asteroids), 11)


class SpawnPlacementTest(AsteroidFieldTestCase):
    def spawn_with(self, edge_index, speed, angle, edge_fraction, kind):
        with (
            mock.patch("asteroidfield.random.choice", return_value=AsteroidField.edges[edge_index]),
            mock.patch("asteroidfield.random.randint", side_effect=[speed, angle, kind]),
            mock.patch("asteroidfield.random.uniform", return_value=edge_fraction),
        ):
            self.field.update(self.field.spawn_interval() + 0.001)
        return next(iter(self.asteroids))

    def test_left_edge_asteroid_flies_right(self):
        asteroid = self.spawn_with(0, speed=50, angle=0, edge_fraction=0.5, kind=2)
        self.assertEqual(asteroid.position, pygame.Vector2(0, SCREEN_HEIGHT * 0.5))
        self.assertEqual(asteroid.velocity, pygame.Vector2(50, 0))
        self.assertEqual(asteroid.radius, ASTEROID_MIN_RADIUS * 2)

    def test_right_edge_asteroid_flies_left(self):
        asteroid = self.spawn_with(1, speed=50, angle=0, edge_fraction=0.25, kind=1)
        self.assertEqual(asteroid.position, pygame.Vector2(SCREEN_WIDTH, SCREEN_HEIGHT * 0.25))
        self.assertEqual(asteroid.velocity, pygame.Vector2(-50, 0))

    def test_top_edge_asteroid_flies_down(self):
        asteroid = self.spawn_with(2, speed=50, angle=0, edge_fraction=0.5, kind=3)
        self.assertEqual(asteroid.position, pygame.Vector2(SCREEN_WIDTH * 0.5, 0))
        self.assertEqual(asteroid.velocity, pygame.Vector2(0, 50))
        self.assertEqual(asteroid.radius, ASTEROID_MIN_RADIUS * 3)

    def test_bottom_edge_asteroid_flies_up(self):
        asteroid = self.spawn_with(3, speed=50, angle=0, edge_fraction=0.5, kind=1)
        self.assertEqual(asteroid.position, pygame.Vector2(SCREEN_WIDTH * 0.5, SCREEN_HEIGHT))
        self.assertEqual(asteroid.velocity, pygame.Vector2(0, -50))

    def test_launch_direction_is_rotated_by_the_random_angle(self):
        asteroid = self.spawn_with(0, speed=100, angle=30, edge_fraction=0.5, kind=1)
        self.assertAlmostEqual(asteroid.velocity.length(), 100)
        self.assertAlmostEqual(asteroid.velocity.x, 100 * 0.8660254, places=4)
        self.assertAlmostEqual(asteroid.velocity.y, 50, places=4)

    def test_speed_scales_with_the_level(self):
        self.field.level = 3
        asteroid = self.spawn_with(0, speed=50, angle=0, edge_fraction=0.5, kind=1)
        self.assertAlmostEqual(asteroid.velocity.x, 60)

    def test_every_edge_points_into_the_screen(self):
        for index, (direction, edge_position) in enumerate(AsteroidField.edges):
            with self.subTest(edge=index):
                start = edge_position(0.5)
                inside = start + direction * 10
                self.assertGreaterEqual(inside.x, 0)
                self.assertLessEqual(inside.x, SCREEN_WIDTH)
                self.assertGreaterEqual(inside.y, 0)
                self.assertLessEqual(inside.y, SCREEN_HEIGHT)
                self.assertTrue(start.x in (0, SCREEN_WIDTH) or start.y in (0, SCREEN_HEIGHT))


class SpawnRandomRangesTest(AsteroidFieldTestCase):
    def test_random_spawns_stay_on_the_border_with_valid_size_and_speed(self):
        for _ in range(300):
            self.asteroids.empty()
            self.field.level_timer = 0
            self.field.update(self.field.spawn_interval() + 0.001)
            asteroid = next(iter(self.asteroids))
            on_border = asteroid.position.x in (0, SCREEN_WIDTH) or asteroid.position.y in (0, SCREEN_HEIGHT)
            self.assertTrue(on_border)
            self.assertIn(asteroid.radius, [ASTEROID_MIN_RADIUS * kind for kind in range(1, ASTEROID_KINDS + 1)])
            self.assertGreaterEqual(asteroid.velocity.length(), 40 - 1e-6)
            self.assertLessEqual(asteroid.velocity.length(), 100 + 1e-6)


if __name__ == "__main__":
    unittest.main()
