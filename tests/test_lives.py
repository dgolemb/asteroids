import unittest

import pygame

from constants import (
    HEART_KIND,
    PLAYER_MAX_LIVES,
    PLAYER_RESPAWN_INVULNERABILITY_SECONDS,
    PLAYER_START_LIVES,
    SHIELD_KIND,
    HEART_SPAWN_MIN_SECONDS,
    HEART_SPAWN_MAX_SECONDS,
    HEART_FULL_LIVES_BONUS_SCORE,
)
from hud import Hud
from player import Player
from powerup import Powerup
from powerupspawner import PowerupSpawner


def new_spawner(player):
    powerups = pygame.sprite.Group()
    Powerup.containers = (powerups,)
    return PowerupSpawner(powerups, player), powerups


class HudLivesTest(unittest.TestCase):
    def setUp(self):
        pygame.font.init()

    def test_starts_with_full_lives(self):
        hud = Hud()
        self.assertEqual(hud.lives, PLAYER_START_LIVES)
        self.assertTrue(hud.has_full_lives())

    def test_add_life_never_exceeds_the_maximum(self):
        hud = Hud()
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
        hud.collect_heart()
        self.assertEqual(hud.lives, PLAYER_MAX_LIVES)
        self.assertEqual(hud.score, HEART_FULL_LIVES_BONUS_SCORE)

    def test_collecting_a_heart_with_missing_life_restores_it_without_score(self):
        hud = Hud()
        hud.lose_life()
        hud.collect_heart()
        self.assertEqual(hud.lives, PLAYER_MAX_LIVES)
        self.assertEqual(hud.score, 0)

    def test_game_over_at_zero_lives(self):
        hud = Hud()
        for _ in range(PLAYER_START_LIVES - 1):
            hud.lose_life()
        self.assertFalse(hud.is_game_over())
        hud.lose_life()
        self.assertTrue(hud.is_game_over())


class PlayerInvulnerabilityTest(unittest.TestCase):
    def test_keeps_position_motion_and_weapon(self):
        player = Player(100, 200)
        player.velocity = pygame.Vector2(30, -40)
        player.speed = 120.0
        player.rotation = 75
        player.weapon_level = 3
        player.start_invulnerability()
        self.assertEqual(player.position, pygame.Vector2(100, 200))
        self.assertEqual(player.velocity, pygame.Vector2(30, -40))
        self.assertEqual(player.speed, 120.0)
        self.assertEqual(player.rotation, 75)
        self.assertEqual(player.weapon_level, 3)
        self.assertTrue(player.is_invulnerable())
        self.assertEqual(player.invulnerable_timer, PLAYER_RESPAWN_INVULNERABILITY_SECONDS)


class HeartSpawnTest(unittest.TestCase):
    def setUp(self):
        Powerup.textures = {HEART_KIND: pygame.Surface((60, 60), pygame.SRCALPHA)}
        self.player = Player(640, 360)

    def tearDown(self):
        Powerup.textures = {}
        Powerup.containers = ()

    def test_available_regardless_of_lives(self):
        spawner, _ = new_spawner(self.player)
        self.assertTrue(spawner.is_available(HEART_KIND))

    def test_not_available_while_a_heart_is_on_screen(self):
        spawner, powerups = new_spawner(self.player)
        Powerup(100, 100, HEART_KIND)
        self.assertEqual(len(powerups), 1)
        self.assertFalse(spawner.is_available(HEART_KIND))

    def test_heart_does_not_depend_on_player_effects(self):
        spawner, _ = new_spawner(self.player)
        self.player.add_effect(SHIELD_KIND, 30)
        self.assertTrue(spawner.is_available(HEART_KIND))

    def test_heart_spawns_within_the_configured_window(self):
        spawner, powerups = new_spawner(self.player)
        elapsed = 0.0
        while elapsed < HEART_SPAWN_MAX_SECONDS + 1 and not len(powerups):
            spawner.update(1 / 20)
            elapsed += 1 / 20
        self.assertEqual([powerup.kind for powerup in powerups], [HEART_KIND])
        self.assertGreaterEqual(elapsed, HEART_SPAWN_MIN_SECONDS)

    def test_next_heart_follows_after_the_previous_one_is_gone(self):
        spawner, powerups = new_spawner(self.player)
        spawned = 0
        for _ in range(int(HEART_SPAWN_MAX_SECONDS * 3 * 20)):
            spawner.update(1 / 20)
            if len(powerups):
                spawned += 1
                for powerup in list(powerups):
                    powerup.kill()
        self.assertGreaterEqual(spawned, 2)


if __name__ == "__main__":
    unittest.main()
