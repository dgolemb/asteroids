import unittest

import pygame

from constants import (
    HEART_KIND,
    PLAYER_MAX_LIVES,
    PLAYER_RESPAWN_INVULNERABILITY_SECONDS,
    PLAYER_START_LIVES,
    SHIELD_KIND,
    POWERUP_SPAWN_MAX_SECONDS,
)
from hud import Hud
from player import Player
from powerup import Powerup
from powerupspawner import PowerupSpawner


def new_spawner(hud, player):
    powerups = pygame.sprite.Group()
    Powerup.containers = (powerups,)
    return PowerupSpawner(powerups, player, hud), powerups


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
        pygame.font.init()
        Powerup.textures = {HEART_KIND: pygame.Surface((60, 60), pygame.SRCALPHA)}
        self.hud = Hud()
        self.player = Player(640, 360)

    def tearDown(self):
        Powerup.textures = {}
        Powerup.containers = ()

    def test_not_available_with_full_lives(self):
        spawner, _ = new_spawner(self.hud, self.player)
        self.assertFalse(spawner.is_available(HEART_KIND))

    def test_available_after_losing_a_life(self):
        spawner, _ = new_spawner(self.hud, self.player)
        self.hud.lose_life()
        self.assertTrue(spawner.is_available(HEART_KIND))

    def test_not_available_while_a_heart_is_on_screen(self):
        spawner, powerups = new_spawner(self.hud, self.player)
        self.hud.lose_life()
        Powerup(100, 100, HEART_KIND)
        self.assertEqual(len(powerups), 1)
        self.assertFalse(spawner.is_available(HEART_KIND))

    def test_not_available_again_once_lives_are_refilled(self):
        spawner, _ = new_spawner(self.hud, self.player)
        self.hud.lose_life()
        self.hud.add_life()
        self.assertFalse(spawner.is_available(HEART_KIND))

    def test_heart_does_not_depend_on_player_effects(self):
        spawner, _ = new_spawner(self.hud, self.player)
        self.hud.lose_life()
        self.player.add_effect(SHIELD_KIND, 30)
        self.assertTrue(spawner.is_available(HEART_KIND))

    def test_no_heart_spawns_while_lives_are_full(self):
        spawner, powerups = new_spawner(self.hud, self.player)
        for _ in range(int(POWERUP_SPAWN_MAX_SECONDS * 3) * 60):
            spawner.update(1 / 20)
        self.assertEqual(len(powerups), 0)

    def test_heart_spawns_after_losing_a_life(self):
        spawner, powerups = new_spawner(self.hud, self.player)
        self.hud.lose_life()
        for _ in range(60 * 60):
            spawner.update(1 / 20)
            if len(powerups):
                break
        self.assertEqual([powerup.kind for powerup in powerups], [HEART_KIND])


if __name__ == "__main__":
    unittest.main()
