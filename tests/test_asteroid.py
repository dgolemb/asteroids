import math
import unittest
from math import ceil

import pygame

from asteroid import Asteroid
from constants import (
    ASTEROID_KINDS,
    ASTEROID_MIN_RADIUS,
    ASTEROID_SCORES,
    ASTEROID_SHAPE_AMPLITUDE,
    ASTEROID_SHAPE_POINTS,
    EXPLOSION_PARTICLE_COUNT_MAX,
    EXPLOSION_PARTICLE_COUNT_MIN,
    EXPLOSION_PARTICLE_LIFETIME_MAX_SECONDS,
    EXPLOSION_PARTICLE_LIFETIME_MIN_SECONDS,
    EXPLOSION_PARTICLE_SPEED_MAX,
    EXPLOSION_PARTICLE_SPEED_MIN,
    EXPLOSION_SPREAD_SCALE_PER_KIND,
    SCREEN_WIDTH,
)
from tests.helpers import AsteroidTestCase


class GenerateShapesTest(AsteroidTestCase):
    def test_creates_an_outline_for_every_kind(self):
        self.assertEqual(sorted(Asteroid.shapes), list(range(1, ASTEROID_KINDS + 1)))
        for points in Asteroid.shapes.values():
            self.assertEqual(len(points), ASTEROID_SHAPE_POINTS)

    def test_outline_stays_within_the_amplitude_around_the_unit_circle(self):
        for kind, points in Asteroid.shapes.items():
            for x, y in points:
                with self.subTest(kind=kind):
                    self.assertGreaterEqual(math.hypot(x, y), 1 - ASTEROID_SHAPE_AMPLITUDE - 1e-9)
                    self.assertLessEqual(math.hypot(x, y), 1 + ASTEROID_SHAPE_AMPLITUDE + 1e-9)

    def test_regenerating_replaces_the_outlines(self):
        before = Asteroid.shapes
        Asteroid.generate_shapes()
        self.assertIsNot(Asteroid.shapes, before)
        self.assertEqual(sorted(Asteroid.shapes), sorted(before))


class AsteroidBasicsTest(AsteroidTestCase):
    def test_is_added_to_its_containers(self):
        asteroid = Asteroid(100, 100, 40)
        self.assertIn(asteroid, self.asteroids)

    def test_score_depends_on_the_size_class(self):
        for kind in range(1, ASTEROID_KINDS + 1):
            with self.subTest(kind=kind):
                asteroid = Asteroid(0, 0, ASTEROID_MIN_RADIUS * kind)
                self.assertEqual(asteroid.get_score(), ASTEROID_SCORES[kind])

    def test_smaller_asteroids_are_worth_more(self):
        small = Asteroid(0, 0, ASTEROID_MIN_RADIUS)
        large = Asteroid(0, 0, ASTEROID_MIN_RADIUS * ASTEROID_KINDS)
        self.assertGreater(small.get_score(), large.get_score())

    def test_unknown_size_class_scores_zero(self):
        asteroid = Asteroid(0, 0, ASTEROID_MIN_RADIUS)
        asteroid.radius = ASTEROID_MIN_RADIUS * (ASTEROID_KINDS + 2)
        self.assertEqual(asteroid.get_score(), 0)

    def test_unknown_size_class_cannot_be_constructed(self):
        with self.assertRaises(KeyError):
            Asteroid(0, 0, ASTEROID_MIN_RADIUS * (ASTEROID_KINDS + 2))

    def test_bounding_radius_includes_the_shape_amplitude(self):
        self.assertAlmostEqual(Asteroid(0, 0, 40).bounding_radius(), 40 * (1 + ASTEROID_SHAPE_AMPLITUDE))

    def test_image_is_a_square_covering_the_bounding_circle(self):
        asteroid = Asteroid(0, 0, 40)
        size = ceil(40 * 2 * (1 + ASTEROID_SHAPE_AMPLITUDE))
        self.assertEqual(asteroid.image.get_size(), (size, size))

    def test_image_is_transparent_outside_the_outline(self):
        asteroid = Asteroid(0, 0, 40)
        self.assertEqual(asteroid.image.get_at((0, 0)).a, 0)
        center = asteroid.image.get_width() // 2
        self.assertEqual(asteroid.image.get_at((center, center)).a, 255)

    def test_mask_is_not_empty(self):
        self.assertGreater(Asteroid(0, 0, 40).get_mask().count(), 0)

    def test_draw_paints_the_asteroid_on_the_screen(self):
        screen = pygame.Surface((200, 200))
        Asteroid(100, 100, 40).draw(screen)
        self.assertNotEqual(screen.get_at((100, 100))[:3], (0, 0, 0))
        self.assertEqual(screen.get_at((0, 0))[:3], (0, 0, 0))


class AsteroidUpdateTest(AsteroidTestCase):
    def test_moves_by_velocity_times_dt(self):
        asteroid = Asteroid(100, 200, 40)
        asteroid.velocity = pygame.Vector2(50, -20)
        asteroid.update(0.5)
        self.assertEqual(asteroid.position, pygame.Vector2(125, 190))

    def test_rotates_by_rotation_speed_times_dt(self):
        asteroid = Asteroid(100, 200, 40)
        asteroid.rotation = 10
        asteroid.rotation_speed = 60
        asteroid.update(0.5)
        self.assertAlmostEqual(asteroid.rotation, 40)

    def test_rotation_wraps_at_360_degrees(self):
        asteroid = Asteroid(100, 200, 40)
        asteroid.rotation = 359
        asteroid.rotation_speed = 60
        asteroid.update(0.1)
        self.assertAlmostEqual(asteroid.rotation, 5)

    def test_position_wraps_around_the_screen(self):
        asteroid = Asteroid(SCREEN_WIDTH - 1, 100, 40)
        asteroid.velocity = pygame.Vector2(100, 0)
        asteroid.update(0.1)
        self.assertAlmostEqual(asteroid.position.x, 9)


class AsteroidExplodeTest(AsteroidTestCase):
    def test_creates_the_configured_number_of_particles_at_the_asteroid(self):
        asteroid = Asteroid(300, 400, 40)
        asteroid.explode()
        self.assertGreaterEqual(len(self.particles), EXPLOSION_PARTICLE_COUNT_MIN)
        self.assertLessEqual(len(self.particles), EXPLOSION_PARTICLE_COUNT_MAX)
        for particle in self.particles:
            self.assertEqual(particle.position, pygame.Vector2(300, 400))

    def test_particle_lifetimes_stay_in_range(self):
        Asteroid(0, 0, 40).explode()
        for particle in self.particles:
            self.assertGreaterEqual(particle.lifetime, EXPLOSION_PARTICLE_LIFETIME_MIN_SECONDS)
            self.assertLessEqual(particle.lifetime, EXPLOSION_PARTICLE_LIFETIME_MAX_SECONDS)

    def test_particle_speed_scales_with_the_size_class(self):
        for kind in range(1, ASTEROID_KINDS + 1):
            self.particles.empty()
            Asteroid(0, 0, ASTEROID_MIN_RADIUS * kind).explode()
            scale = 1 + (kind - 1) * EXPLOSION_SPREAD_SCALE_PER_KIND
            for particle in self.particles:
                with self.subTest(kind=kind):
                    self.assertGreaterEqual(particle.velocity.length(), EXPLOSION_PARTICLE_SPEED_MIN * scale - 1e-6)
                    self.assertLessEqual(particle.velocity.length(), EXPLOSION_PARTICLE_SPEED_MAX * scale + 1e-6)

    def test_particles_fly_in_all_directions(self):
        Asteroid(0, 0, 40).explode()
        directions = {(round(p.velocity.normalize().x, 3), round(p.velocity.normalize().y, 3)) for p in self.particles}
        self.assertEqual(len(directions), len(self.particles))
        self.assertTrue(any(x > 0 for x, _ in directions))
        self.assertTrue(any(x < 0 for x, _ in directions))
        self.assertTrue(any(y > 0 for _, y in directions))
        self.assertTrue(any(y < 0 for _, y in directions))

    def test_logs_the_explosion_and_keeps_the_asteroid_alive(self):
        asteroid = Asteroid(0, 0, 40)
        asteroid.explode()
        self.assertEqual(self.logged_events(), ["asteroid_explosion"])
        self.assertIn(asteroid, self.asteroids)


class AsteroidSplitTest(AsteroidTestCase):
    def test_small_asteroid_disappears_without_children(self):
        asteroid = Asteroid(100, 100, ASTEROID_MIN_RADIUS)
        asteroid.velocity = pygame.Vector2(50, 0)
        asteroid.split()
        self.assertEqual(len(self.asteroids), 0)
        self.assertNotIn("asteroid_split", self.logged_events())
        self.assertGreater(len(self.particles), 0)

    def test_larger_asteroid_is_replaced_by_two_smaller_ones(self):
        asteroid = Asteroid(100, 200, ASTEROID_MIN_RADIUS * 3)
        asteroid.velocity = pygame.Vector2(100, 0)
        asteroid.split()
        self.assertNotIn(asteroid, self.asteroids)
        self.assertEqual(len(self.asteroids), 2)
        for child in self.asteroids:
            self.assertEqual(child.radius, ASTEROID_MIN_RADIUS * 2)
            self.assertEqual(child.position, pygame.Vector2(100, 200))
        self.assertEqual(self.logged_events(), ["asteroid_explosion", "asteroid_split"])

    def test_children_fly_apart_symmetrically_and_faster(self):
        asteroid = Asteroid(0, 0, ASTEROID_MIN_RADIUS * 3)
        asteroid.velocity = pygame.Vector2(100, 0)
        asteroid.split()
        first, second = sorted(self.asteroids, key=lambda child: child.velocity.y)
        self.assertAlmostEqual(first.velocity.length(), 120)
        self.assertAlmostEqual(second.velocity.length(), 120)
        self.assertAlmostEqual(first.velocity.x, second.velocity.x)
        self.assertAlmostEqual(first.velocity.y, -second.velocity.y)
        angle = math.degrees(math.atan2(second.velocity.y, second.velocity.x))
        self.assertGreaterEqual(angle, 20)
        self.assertLessEqual(angle, 50)

    def test_children_inherit_the_direction_of_a_moving_parent(self):
        asteroid = Asteroid(0, 0, ASTEROID_MIN_RADIUS * 3)
        asteroid.velocity = pygame.Vector2(0, -100)
        asteroid.split()
        for child in self.asteroids:
            self.assertLess(child.velocity.y, 0)

    def test_splitting_the_whole_tree_takes_seven_hits(self):
        Asteroid(100, 100, ASTEROID_MIN_RADIUS * ASTEROID_KINDS).velocity = pygame.Vector2(10, 0)
        hits = 0
        while len(self.asteroids):
            next(iter(self.asteroids)).split()
            hits += 1
        self.assertEqual(hits, 1 + 2 + 4)
        self.assertEqual(self.logged_events().count("asteroid_split"), 3)
        self.assertEqual(self.logged_events().count("asteroid_explosion"), 7)


if __name__ == "__main__":
    unittest.main()
