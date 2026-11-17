import unittest
from unittest import mock

import pygame

from asteroid import Asteroid
from constants import (
    ASTEROID_MIN_RADIUS,
    ASTEROID_SCORES,
    HEART_FULL_LIVES_BONUS_SCORE,
    HEART_KIND,
    PLAYER_START_LIVES,
    POWERUP_EFFECT_SECONDS,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    SHIELD_DURATION_SECONDS,
    SHIELD_KIND,
    SHIELD_RADIUS,
    WEAPON_KIND,
)
from hud import Hud
from main import apply_powerup, destroy_asteroid, resolve_collisions, shield_hits
from player import Player
from powerup import Powerup
from shape import Shape
from shot import Shot
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


def solid(width, height):
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    surface.fill((255, 255, 255, 255))
    return surface


class CollisionTestCase(AsteroidTestCase):
    @classmethod
    def setUpClass(cls):
        pygame.font.init()

    def setUp(self):
        super().setUp()
        self.shots = pygame.sprite.Group()
        self.powerups = pygame.sprite.Group()
        self.enterContext(mock.patch.object(Player, "texture", solid(40, 40), create=True))
        self.enterContext(mock.patch.object(Shot, "textures", [solid(4, 10)]))
        self.enterContext(mock.patch.object(Shot, "containers", (self.shots,), create=True))
        self.enterContext(
            mock.patch.object(Powerup, "textures", {kind: solid(60, 60) for kind in (SHIELD_KIND, WEAPON_KIND, HEART_KIND)})
        )
        self.enterContext(mock.patch.object(Powerup, "containers", (self.powerups,), create=True))
        self.main_log = self.enterContext(mock.patch("main.log_event"))
        self.player = Player(500, 300)
        self.hud = Hud()
        self.stats = GameStats()
        self.field = StubField(1.0)

    def resolve(self):
        return resolve_collisions(self.player, self.powerups, self.asteroids, self.shots, self.field, self.hud, self.stats)

    def asteroid_on_player(self, kind=1):
        return Asteroid(500, 300, ASTEROID_MIN_RADIUS * kind)

    def asteroid_inside_shield_only(self):
        return Asteroid(500 + SHIELD_RADIUS + 10, 300, ASTEROID_MIN_RADIUS)

    def far_asteroid(self, kind=1):
        return Asteroid(900, 600, ASTEROID_MIN_RADIUS * kind)


class ApplyPowerupTest(CollisionTestCase):
    def test_weapon_upgrades_the_weapon(self):
        powerup = Powerup(0, 0, WEAPON_KIND)
        apply_powerup(powerup, self.player, self.hud, self.stats)
        self.assertEqual(self.player.weapon_level, 1)
        self.assertTrue(self.player.has_effect(WEAPON_KIND))

    def test_shield_starts_the_shield_effect(self):
        powerup = Powerup(0, 0, SHIELD_KIND)
        apply_powerup(powerup, self.player, self.hud, self.stats)
        self.assertEqual(self.player.active_effects[SHIELD_KIND], POWERUP_EFFECT_SECONDS[SHIELD_KIND])
        self.assertEqual(self.player.weapon_level, 0)

    def test_heart_restores_a_life_when_one_is_missing(self):
        self.hud.lose_life()
        apply_powerup(Powerup(0, 0, HEART_KIND), self.player, self.hud, self.stats)
        self.assertEqual(self.hud.lives, PLAYER_START_LIVES)
        self.assertEqual(self.hud.score, 0)

    def test_heart_with_full_lives_gives_bonus_score(self):
        apply_powerup(Powerup(0, 0, HEART_KIND), self.player, self.hud, self.stats)
        self.assertEqual(self.hud.lives, PLAYER_START_LIVES)
        self.assertEqual(self.hud.score, HEART_FULL_LIVES_BONUS_SCORE)

    def test_heart_does_not_create_an_effect(self):
        apply_powerup(Powerup(0, 0, HEART_KIND), self.player, self.hud, self.stats)
        self.assertEqual(self.player.active_effects, {})

    def test_pickup_is_recorded_logged_and_removed(self):
        powerup = Powerup(0, 0, SHIELD_KIND)
        apply_powerup(powerup, self.player, self.hud, self.stats)
        self.assertEqual(self.stats.powerups_collected[SHIELD_KIND], 1)
        self.main_log.assert_called_once_with("powerup_picked", kind=SHIELD_KIND)
        self.assertNotIn(powerup, self.powerups)


class ResolvePowerupCollisionsTest(CollisionTestCase):
    def test_nothing_to_resolve(self):
        self.assertFalse(self.resolve())
        self.assertEqual(self.hud.lives, PLAYER_START_LIVES)

    def test_powerup_touching_the_player_is_collected(self):
        powerup = Powerup(500, 300, WEAPON_KIND)
        self.assertFalse(self.resolve())
        self.assertNotIn(powerup, self.powerups)
        self.assertEqual(self.player.weapon_level, 1)

    def test_powerup_far_away_stays(self):
        powerup = Powerup(100, 100, WEAPON_KIND)
        self.resolve()
        self.assertIn(powerup, self.powerups)
        self.assertEqual(self.player.weapon_level, 0)

    def test_powerup_is_collected_across_the_screen_edge(self):
        self.player.position = pygame.Vector2(5, 300)
        powerup = Powerup(SCREEN_WIDTH - 5, 300, SHIELD_KIND)
        self.resolve()
        self.assertNotIn(powerup, self.powerups)
        self.assertTrue(self.player.shield_active())

    def test_several_powerups_are_collected_in_one_frame(self):
        Powerup(500, 300, WEAPON_KIND)
        Powerup(505, 300, SHIELD_KIND)
        self.resolve()
        self.assertEqual(len(self.powerups), 0)
        self.assertEqual(self.stats.powerups_collected[WEAPON_KIND], 1)
        self.assertEqual(self.stats.powerups_collected[SHIELD_KIND], 1)


class ResolvePlayerHitTest(CollisionTestCase):
    def test_asteroid_on_the_player_costs_a_life_and_starts_invulnerability(self):
        self.asteroid_on_player()
        self.assertFalse(self.resolve())
        self.assertEqual(self.hud.lives, PLAYER_START_LIVES - 1)
        self.assertTrue(self.player.is_invulnerable())
        self.main_log.assert_called_once_with("player_hit")

    def test_far_asteroid_does_no_harm(self):
        self.far_asteroid()
        self.assertFalse(self.resolve())
        self.assertEqual(self.hud.lives, PLAYER_START_LIVES)
        self.assertFalse(self.player.is_invulnerable())

    def test_hit_across_the_screen_edge(self):
        self.player.position = pygame.Vector2(5, 300)
        Asteroid(SCREEN_WIDTH - 5, 300, ASTEROID_MIN_RADIUS)
        self.resolve()
        self.assertEqual(self.hud.lives, PLAYER_START_LIVES - 1)

    def test_invulnerable_player_is_not_hit(self):
        self.player.start_invulnerability()
        self.asteroid_on_player()
        self.assertFalse(self.resolve())
        self.assertEqual(self.hud.lives, PLAYER_START_LIVES)

    def test_losing_the_last_life_ends_the_game_without_invulnerability(self):
        self.hud.lives = 1
        self.asteroid_on_player()
        self.assertTrue(self.resolve())
        self.assertTrue(self.hud.is_game_over())
        self.assertFalse(self.player.is_invulnerable())

    def test_game_over_stops_processing_the_remaining_asteroids(self):
        self.hud.lives = 1
        self.asteroid_on_player()
        self.asteroid_on_player()
        self.assertTrue(self.resolve())
        self.assertEqual(self.hud.lives, 0)

    def test_game_over_leaves_the_score_untouched(self):
        self.hud.lives = 1
        self.hud.add_score(300)
        self.asteroid_on_player()
        self.resolve()
        self.assertEqual(self.hud.score, 300)

    def test_asteroid_survives_hitting_the_player(self):
        asteroid = self.asteroid_on_player()
        self.resolve()
        self.assertIn(asteroid, self.asteroids)
        self.assertEqual(len(self.asteroids), 1)

    def test_lingering_asteroid_costs_another_life_once_invulnerability_ends(self):
        self.asteroid_on_player()
        self.resolve()
        self.resolve()
        self.assertEqual(self.hud.lives, PLAYER_START_LIVES - 1)
        self.player.invulnerable_timer = 0
        self.resolve()
        self.assertEqual(self.hud.lives, PLAYER_START_LIVES - 2)

    def test_two_overlapping_asteroids_cost_only_one_life_per_frame(self):
        self.asteroid_on_player()
        self.asteroid_on_player()
        self.resolve()
        self.assertEqual(self.hud.lives, PLAYER_START_LIVES - 1)


class ResolveShieldTest(CollisionTestCase):
    def setUp(self):
        super().setUp()
        self.player.add_effect(SHIELD_KIND, SHIELD_DURATION_SECONDS)

    def test_shield_destroys_an_asteroid_that_enters_it(self):
        asteroid = self.asteroid_inside_shield_only()
        self.assertFalse(self.resolve())
        self.assertNotIn(asteroid, self.asteroids)
        self.assertEqual(self.hud.score, ASTEROID_SCORES[1])
        self.assertEqual(self.stats.asteroids_destroyed[1], 1)

    def test_shield_destruction_is_logged_with_its_own_source(self):
        self.asteroid_inside_shield_only()
        self.resolve()
        self.main_log.assert_any_call("asteroid_shielded", score=ASTEROID_SCORES[1])

    def test_shield_protects_the_player_from_an_asteroid_on_top_of_it(self):
        self.asteroid_on_player()
        self.assertFalse(self.resolve())
        self.assertEqual(self.hud.lives, PLAYER_START_LIVES)
        self.assertFalse(self.player.is_invulnerable())

    def test_shield_splits_big_asteroids(self):
        Asteroid(500 + SHIELD_RADIUS + 20, 300, ASTEROID_MIN_RADIUS * 3)
        self.resolve()
        self.assertEqual(len(self.asteroids), 2)

    def test_asteroid_outside_the_shield_is_left_alone(self):
        asteroid = self.far_asteroid()
        self.resolve()
        self.assertIn(asteroid, self.asteroids)
        self.assertEqual(self.hud.score, 0)

    def test_expired_shield_no_longer_destroys_asteroids(self):
        self.player.update_effects(SHIELD_DURATION_SECONDS + 1)
        asteroid = self.asteroid_inside_shield_only()
        self.resolve()
        self.assertIn(asteroid, self.asteroids)
        self.assertEqual(self.hud.score, 0)


class ResolveShotTest(CollisionTestCase):
    def test_shot_destroys_the_asteroid_it_hits(self):
        asteroid = Asteroid(800, 500, ASTEROID_MIN_RADIUS)
        shot = Shot(800, 500)
        self.assertFalse(self.resolve())
        self.assertNotIn(asteroid, self.asteroids)
        self.assertNotIn(shot, self.shots)
        self.assertEqual(self.hud.score, ASTEROID_SCORES[1])
        self.main_log.assert_any_call("asteroid_shot", score=ASTEROID_SCORES[1])

    def test_shot_that_misses_changes_nothing(self):
        asteroid = Asteroid(800, 500, ASTEROID_MIN_RADIUS)
        shot = Shot(100, 100)
        self.resolve()
        self.assertIn(asteroid, self.asteroids)
        self.assertIn(shot, self.shots)
        self.assertEqual(self.hud.score, 0)

    def test_one_asteroid_consumes_only_one_shot_per_frame(self):
        Asteroid(800, 500, ASTEROID_MIN_RADIUS)
        first = Shot(800, 500)
        second = Shot(801, 500)
        self.resolve()
        self.assertEqual(len([shot for shot in (first, second) if shot in self.shots]), 1)

    def test_big_asteroid_splits_when_shot(self):
        Asteroid(800, 500, ASTEROID_MIN_RADIUS * 3)
        Shot(800, 500)
        self.resolve()
        self.assertEqual(len(self.asteroids), 2)
        self.assertEqual(self.hud.score, ASTEROID_SCORES[3])

    def test_score_uses_the_field_multiplier(self):
        self.field = StubField(2.0)
        Asteroid(800, 500, ASTEROID_MIN_RADIUS)
        Shot(800, 500)
        self.resolve()
        self.assertEqual(self.hud.score, ASTEROID_SCORES[1] * 2)

    def test_hit_and_shot_on_the_same_asteroid_in_one_frame_do_both(self):
        asteroid = self.asteroid_on_player()
        Shot(500, 300)
        self.assertFalse(self.resolve())
        self.assertEqual(self.hud.lives, PLAYER_START_LIVES - 1)
        self.assertNotIn(asteroid, self.asteroids)
        self.assertEqual(self.hud.score, ASTEROID_SCORES[1])

    def test_each_asteroid_is_checked_against_the_shots(self):
        Asteroid(800, 500, ASTEROID_MIN_RADIUS)
        Asteroid(200, 600, ASTEROID_MIN_RADIUS)
        Shot(800, 500)
        Shot(200, 600)
        self.resolve()
        self.assertEqual(len(self.asteroids), 0)
        self.assertEqual(self.hud.score, ASTEROID_SCORES[1] * 2)


if __name__ == "__main__":
    unittest.main()
