import unittest
from unittest import mock

import pygame

from constants import (
    HEART_KIND,
    HEART_SPAWN_MAX_SECONDS,
    HEART_SPAWN_MIN_SECONDS,
    POWERUP_BLINK_SECONDS,
    POWERUP_PICKUP_SECONDS,
    POWERUP_RADIUS,
    POWERUP_SPAWN_ATTEMPTS,
    POWERUP_SPAWN_MAX_SECONDS,
    POWERUP_SPAWN_MIN_SECONDS,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    SHIELD_DURATION_SECONDS,
    SHIELD_KIND,
    WEAPON_DURATION_SECONDS,
    WEAPON_KIND,
)
from player import Player
from powerup import Powerup
from powerupspawner import PowerupSpawner
from tests.helpers import lowest_uniform, middle_uniform


def solid_surface(size=60):
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    surface.fill((255, 255, 255, 255))
    return surface


class PowerupTestCase(unittest.TestCase):
    textures = (SHIELD_KIND, WEAPON_KIND, HEART_KIND)

    def setUp(self):
        self.powerups = pygame.sprite.Group()
        self.enterContext(
            mock.patch.object(Powerup, "textures", {kind: solid_surface() for kind in self.textures})
        )
        self.enterContext(mock.patch.object(Powerup, "containers", (self.powerups,), create=True))
        self.player = Player(640, 360)
        self.spawner = PowerupSpawner(self.powerups, self.player)


class PowerupTest(PowerupTestCase):
    def test_initial_state(self):
        powerup = Powerup(100, 200, SHIELD_KIND)
        self.assertEqual(powerup.kind, SHIELD_KIND)
        self.assertEqual(powerup.radius, POWERUP_RADIUS)
        self.assertEqual(powerup.time_left, POWERUP_PICKUP_SECONDS)
        self.assertIn(powerup, self.powerups)

    def test_update_counts_down(self):
        powerup = Powerup(100, 200, SHIELD_KIND)
        powerup.update(2.5)
        self.assertAlmostEqual(powerup.time_left, POWERUP_PICKUP_SECONDS - 2.5)
        self.assertIn(powerup, self.powerups)

    def test_disappears_when_time_runs_out(self):
        powerup = Powerup(100, 200, SHIELD_KIND)
        powerup.update(POWERUP_PICKUP_SECONDS - 0.01)
        self.assertIn(powerup, self.powerups)
        powerup.update(0.01)
        self.assertNotIn(powerup, self.powerups)

    def test_blinking_starts_at_the_blink_threshold(self):
        powerup = Powerup(100, 200, SHIELD_KIND)
        powerup.time_left = POWERUP_BLINK_SECONDS + 0.01
        self.assertFalse(powerup.is_blinking())
        powerup.time_left = POWERUP_BLINK_SECONDS
        self.assertTrue(powerup.is_blinking())

    def test_mask_follows_the_texture(self):
        self.assertEqual(Powerup(100, 200, HEART_KIND).get_mask().count(), 60 * 60)

    def test_draw_paints_the_texture_around_the_position(self):
        screen = pygame.Surface((300, 300))
        Powerup(100, 100, SHIELD_KIND).draw(screen)
        self.assertEqual(screen.get_at((100, 100))[:3], (255, 255, 255))
        self.assertEqual(screen.get_at((10, 10))[:3], (0, 0, 0))

    def test_draw_skips_the_dark_phase_of_the_blink(self):
        screen = pygame.Surface((300, 300))
        powerup = Powerup(100, 100, SHIELD_KIND)
        powerup.time_left = 0.2
        powerup.draw(screen)
        self.assertEqual(screen.get_at((100, 100))[:3], (0, 0, 0))

    def test_draw_shows_the_bright_phase_of_the_blink(self):
        screen = pygame.Surface((300, 300))
        powerup = Powerup(100, 100, SHIELD_KIND)
        powerup.time_left = 0.1
        powerup.draw(screen)
        self.assertEqual(screen.get_at((100, 100))[:3], (255, 255, 255))


class SpawnIntervalTest(PowerupTestCase):
    def test_heart_uses_the_long_window(self):
        with mock.patch("powerupspawner.random.uniform", return_value=200) as uniform:
            self.assertEqual(self.spawner.random_interval(HEART_KIND), 200)
        uniform.assert_called_once_with(HEART_SPAWN_MIN_SECONDS, HEART_SPAWN_MAX_SECONDS)

    def test_other_kinds_use_the_short_window(self):
        for kind in (SHIELD_KIND, WEAPON_KIND):
            with self.subTest(kind=kind):
                with mock.patch("powerupspawner.random.uniform", return_value=15) as uniform:
                    self.assertEqual(self.spawner.random_interval(kind), 15)
                uniform.assert_called_once_with(POWERUP_SPAWN_MIN_SECONDS, POWERUP_SPAWN_MAX_SECONDS)

    def test_reset_schedule_restarts_the_timer_with_a_new_interval(self):
        self.spawner.spawn_timers[SHIELD_KIND] = 7.0
        with mock.patch("powerupspawner.random.uniform", return_value=12):
            self.spawner.reset_schedule(SHIELD_KIND)
        self.assertEqual(self.spawner.spawn_timers[SHIELD_KIND], 0.0)
        self.assertEqual(self.spawner.next_spawn_seconds[SHIELD_KIND], 12)


class AvailabilityTest(PowerupTestCase):
    def test_shield_is_available_without_the_effect(self):
        self.assertTrue(self.spawner.is_available(SHIELD_KIND))

    def test_shield_is_not_available_while_the_effect_is_active(self):
        self.player.add_effect(SHIELD_KIND, SHIELD_DURATION_SECONDS)
        self.assertFalse(self.spawner.is_available(SHIELD_KIND))

    def test_shield_is_not_available_while_one_lies_on_the_screen(self):
        Powerup(100, 100, SHIELD_KIND)
        self.assertFalse(self.spawner.is_available(SHIELD_KIND))

    def test_weapon_stays_available_while_the_effect_is_active(self):
        self.player.add_effect(WEAPON_KIND, WEAPON_DURATION_SECONDS)
        self.assertTrue(self.spawner.is_available(WEAPON_KIND))

    def test_weapon_is_not_available_while_one_lies_on_the_screen(self):
        Powerup(100, 100, WEAPON_KIND)
        self.assertFalse(self.spawner.is_available(WEAPON_KIND))

    def test_a_powerup_of_another_kind_does_not_block(self):
        Powerup(100, 100, WEAPON_KIND)
        self.assertTrue(self.spawner.is_available(SHIELD_KIND))


class RandomPositionTest(PowerupTestCase):
    def test_positions_stay_fully_on_the_screen(self):
        for _ in range(200):
            position = self.spawner.random_position()
            self.assertGreaterEqual(position.x, POWERUP_RADIUS)
            self.assertLessEqual(position.x, SCREEN_WIDTH - POWERUP_RADIUS)
            self.assertGreaterEqual(position.y, POWERUP_RADIUS)
            self.assertLessEqual(position.y, SCREEN_HEIGHT - POWERUP_RADIUS)

    def test_returns_none_when_every_attempt_overlaps_an_existing_powerup(self):
        Powerup(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2, SHIELD_KIND)
        with mock.patch("powerupspawner.random.uniform", side_effect=middle_uniform) as uniform:
            self.assertIsNone(self.spawner.random_position())
        self.assertEqual(uniform.call_count, POWERUP_SPAWN_ATTEMPTS * 2)

    def test_accepts_a_position_at_exactly_two_radii_away(self):
        Powerup(POWERUP_RADIUS, POWERUP_RADIUS, SHIELD_KIND)
        with mock.patch("powerupspawner.random.uniform", side_effect=[POWERUP_RADIUS * 3, POWERUP_RADIUS]):
            position = self.spawner.random_position()
        self.assertEqual(position, pygame.Vector2(POWERUP_RADIUS * 3, POWERUP_RADIUS))


class SpawnUpdateTest(PowerupTestCase):
    def update_with_lowest_values(self, dt):
        with mock.patch("powerupspawner.random.uniform", side_effect=lowest_uniform):
            self.spawner.update(dt)

    def test_nothing_spawns_before_the_interval(self):
        self.update_with_lowest_values(POWERUP_SPAWN_MIN_SECONDS - 0.01)
        self.assertEqual(len(self.powerups), 0)

    def test_spawns_the_first_due_kind_once_the_interval_passes(self):
        self.update_with_lowest_values(POWERUP_SPAWN_MIN_SECONDS)
        self.assertEqual([powerup.kind for powerup in self.powerups], [SHIELD_KIND])

    def test_blocked_kind_waits_for_free_space_without_losing_its_turn(self):
        self.update_with_lowest_values(POWERUP_SPAWN_MIN_SECONDS)
        self.update_with_lowest_values(0.1)
        self.assertEqual([powerup.kind for powerup in self.powerups], [SHIELD_KIND])
        for powerup in list(self.powerups):
            powerup.kill()
        self.update_with_lowest_values(0.1)
        self.assertIn(WEAPON_KIND, [powerup.kind for powerup in self.powerups])

    def test_schedule_restarts_after_a_spawn(self):
        self.update_with_lowest_values(POWERUP_SPAWN_MIN_SECONDS)
        self.assertEqual(self.spawner.spawn_timers[SHIELD_KIND], 0.0)

    def test_unavailable_kind_is_rescheduled_instead_of_spawned(self):
        self.player.add_effect(SHIELD_KIND, SHIELD_DURATION_SECONDS)
        with mock.patch.object(Powerup, "textures", {SHIELD_KIND: solid_surface()}):
            self.update_with_lowest_values(POWERUP_SPAWN_MIN_SECONDS)
        self.assertEqual(len(self.powerups), 0)
        self.assertEqual(self.spawner.spawn_timers[SHIELD_KIND], 0.0)

    def test_heart_waits_for_its_own_longer_interval(self):
        with mock.patch.object(Powerup, "textures", {HEART_KIND: solid_surface()}):
            self.update_with_lowest_values(HEART_SPAWN_MIN_SECONDS - 1)
            self.assertEqual(len(self.powerups), 0)
            self.update_with_lowest_values(1)
        self.assertEqual([powerup.kind for powerup in self.powerups], [HEART_KIND])


if __name__ == "__main__":
    unittest.main()
