import unittest
from unittest import mock

import pygame

from constants import (
    HEART_FULL_LIVES_BONUS_SCORE,
    HEART_KIND,
    HEART_SPAWN_MAX_SECONDS,
    HEART_SPAWN_MIN_SECONDS,
    PLAYER_MAX_LIVES,
    PLAYER_RESPAWN_INVULNERABILITY_SECONDS,
    PLAYER_START_LIVES,
    SHIELD_DURATION_SECONDS,
    SHIELD_KIND,
)
from hud import Hud
from player import Player
from powerup import Powerup
from powerupspawner import PowerupSpawner
from tests.helpers import pressed


class HudLivesTest(unittest.TestCase):
    def setUp(self):
        pygame.font.init()

    def test_starts_with_full_lives(self):
        hud = Hud()
        self.assertEqual(hud.lives, PLAYER_START_LIVES)
        self.assertTrue(hud.has_full_lives())

    def test_add_life_never_exceeds_the_maximum(self):
        hud = Hud()
        hud.lives = PLAYER_MAX_LIVES
        hud.add_life()
        self.assertEqual(hud.lives, PLAYER_MAX_LIVES)

    def test_add_life_restores_one_lost_life(self):
        hud = Hud()
        hud.lose_life()
        hud.lose_life()
        hud.add_life()
        self.assertEqual(hud.lives, PLAYER_MAX_LIVES - 1)
        self.assertFalse(hud.has_full_lives())

    def test_collecting_a_heart_with_full_lives_awards_bonus_score(self):
        hud = Hud()
        hud.lives = PLAYER_MAX_LIVES
        hud.collect_heart()
        self.assertEqual(hud.lives, PLAYER_MAX_LIVES)
        self.assertEqual(hud.score, HEART_FULL_LIVES_BONUS_SCORE)

    def test_collecting_a_heart_with_missing_life_restores_it_without_score(self):
        hud = Hud()
        hud.lives = PLAYER_MAX_LIVES
        hud.lose_life()
        hud.collect_heart()
        self.assertEqual(hud.lives, PLAYER_MAX_LIVES)
        self.assertEqual(hud.score, 0)

    def test_collecting_hearts_after_losing_everything_restores_one_life_at_a_time(self):
        hud = Hud()
        hud.lives = 0
        hud.collect_heart()
        self.assertEqual(hud.lives, 1)
        self.assertEqual(hud.score, 0)

    def test_game_over_at_zero_lives(self):
        hud = Hud()
        hud.lives = 1
        self.assertFalse(hud.is_game_over())
        hud.lose_life()
        self.assertTrue(hud.is_game_over())

    def test_game_over_below_zero_lives(self):
        hud = Hud()
        hud.lives = -1
        self.assertTrue(hud.is_game_over())

    def test_losing_all_start_lives_ends_the_game_exactly_on_the_last_one(self):
        hud = Hud()
        for _ in range(PLAYER_START_LIVES - 1):
            hud.lose_life()
        self.assertFalse(hud.is_game_over())
        hud.lose_life()
        self.assertTrue(hud.is_game_over())


class PlayerInvulnerabilityTest(unittest.TestCase):
    def setUp(self):
        self.player = Player(100, 200)
        self.enterContext(mock.patch.object(self.player, "shoot"))

    def tick(self, dt):
        with mock.patch("pygame.key.get_pressed", return_value=pressed()):
            self.player.update(dt)

    def test_fresh_player_is_vulnerable(self):
        self.assertFalse(self.player.is_invulnerable())

    def test_start_makes_the_player_invulnerable(self):
        self.player.start_invulnerability()
        self.assertTrue(self.player.is_invulnerable())

    def test_keeps_position_motion_and_weapon(self):
        self.player.velocity = pygame.Vector2(30, -40)
        self.player.speed = 120.0
        self.player.rotation = 75
        self.player.weapon_level = 3
        self.player.start_invulnerability()
        self.assertEqual(self.player.position, pygame.Vector2(100, 200))
        self.assertEqual(self.player.velocity, pygame.Vector2(30, -40))
        self.assertEqual(self.player.speed, 120.0)
        self.assertEqual(self.player.rotation, 75)
        self.assertEqual(self.player.weapon_level, 3)

    def test_lasts_for_the_configured_time(self):
        self.player.start_invulnerability()
        self.tick(PLAYER_RESPAWN_INVULNERABILITY_SECONDS - 0.5)
        self.assertTrue(self.player.is_invulnerable())
        self.tick(0.5)
        self.assertFalse(self.player.is_invulnerable())

    def test_timer_never_goes_negative(self):
        self.player.start_invulnerability()
        self.tick(PLAYER_RESPAWN_INVULNERABILITY_SECONDS * 10)
        self.assertEqual(self.player.invulnerable_timer, 0)

    def test_starting_again_refreshes_the_timer(self):
        self.player.start_invulnerability()
        self.tick(PLAYER_RESPAWN_INVULNERABILITY_SECONDS - 0.5)
        self.player.start_invulnerability()
        self.tick(PLAYER_RESPAWN_INVULNERABILITY_SECONDS - 0.5)
        self.assertTrue(self.player.is_invulnerable())


class HeartSpawnTest(unittest.TestCase):
    def setUp(self):
        self.powerups = pygame.sprite.Group()
        self.enterContext(
            mock.patch.object(Powerup, "textures", {HEART_KIND: pygame.Surface((60, 60), pygame.SRCALPHA)})
        )
        self.enterContext(mock.patch.object(Powerup, "containers", (self.powerups,), create=True))
        self.player = Player(640, 360)
        self.spawner = PowerupSpawner(self.powerups, self.player)
        self.enterContext(
            mock.patch.object(self.spawner, "random_interval", return_value=HEART_SPAWN_MIN_SECONDS)
        )
        positions = iter(pygame.Vector2(100 + 150 * index, 200) for index in range(50))
        self.enterContext(mock.patch.object(self.spawner, "random_position", side_effect=lambda: next(positions)))

    def collect_all(self):
        for powerup in list(self.powerups):
            powerup.kill()

    def test_available_when_nothing_blocks_it(self):
        self.assertTrue(self.spawner.is_available(HEART_KIND))

    def test_not_available_while_a_heart_is_on_screen(self):
        Powerup(100, 100, HEART_KIND)
        self.assertEqual(len(self.powerups), 1)
        self.assertFalse(self.spawner.is_available(HEART_KIND))

    def test_available_even_when_the_player_has_a_heart_effect(self):
        self.player.add_effect(HEART_KIND, SHIELD_DURATION_SECONDS)
        self.assertTrue(self.spawner.is_available(HEART_KIND))

    def test_available_while_the_player_has_a_shield(self):
        self.player.add_effect(SHIELD_KIND, SHIELD_DURATION_SECONDS)
        self.assertTrue(self.spawner.is_available(HEART_KIND))

    def test_heart_does_not_spawn_before_the_interval(self):
        self.spawner.update(HEART_SPAWN_MIN_SECONDS - 0.5)
        self.assertEqual(len(self.powerups), 0)

    def test_heart_spawns_when_the_interval_elapses(self):
        self.spawner.update(HEART_SPAWN_MIN_SECONDS - 0.5)
        self.spawner.update(0.5)
        self.assertEqual([powerup.kind for powerup in self.powerups], [HEART_KIND])

    def test_second_heart_is_not_spawned_while_the_first_is_alive(self):
        self.spawner.update(HEART_SPAWN_MIN_SECONDS)
        self.spawner.update(HEART_SPAWN_MIN_SECONDS)
        self.assertEqual(len(self.powerups), 1)

    def test_blocked_heart_restarts_its_countdown_instead_of_spawning_late(self):
        self.spawner.update(HEART_SPAWN_MIN_SECONDS)
        self.spawner.update(HEART_SPAWN_MIN_SECONDS)
        self.collect_all()
        self.spawner.update(HEART_SPAWN_MIN_SECONDS - 0.5)
        self.assertEqual(len(self.powerups), 0)
        self.spawner.update(0.5)
        self.assertEqual(len(self.powerups), 1)

    def test_next_heart_comes_one_full_interval_after_the_previous_spawn(self):
        self.spawner.update(HEART_SPAWN_MIN_SECONDS)
        self.collect_all()
        self.spawner.update(HEART_SPAWN_MIN_SECONDS - 0.5)
        self.assertEqual(len(self.powerups), 0)
        self.spawner.update(0.5)
        self.assertEqual(len(self.powerups), 1)

    def test_hearts_keep_coming_for_the_whole_session(self):
        spawned = 0
        for _ in range(5):
            self.spawner.update(HEART_SPAWN_MIN_SECONDS)
            spawned += len(self.powerups)
            self.collect_all()
        self.assertEqual(spawned, 5)


class HeartIntervalTest(unittest.TestCase):
    def test_interval_stays_inside_the_configured_window(self):
        spawner = PowerupSpawner(pygame.sprite.Group(), Player(0, 0))
        intervals = [spawner.random_interval(HEART_KIND) for _ in range(500)]
        self.assertGreaterEqual(min(intervals), HEART_SPAWN_MIN_SECONDS)
        self.assertLessEqual(max(intervals), HEART_SPAWN_MAX_SECONDS)

    def test_interval_actually_varies(self):
        spawner = PowerupSpawner(pygame.sprite.Group(), Player(0, 0))
        intervals = {spawner.random_interval(HEART_KIND) for _ in range(50)}
        self.assertGreater(len(intervals), 1)


if __name__ == "__main__":
    unittest.main()
