import unittest
from unittest import mock

import pygame

from constants import (
    PLAYER_SHOOT_COOLDOWN_SECONDS,
    PLAYER_SHOT_SPEED,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    SHOT_RADIUS,
    WEAPON_MAX_LEVEL,
    WEAPON_SHOT_SCALE_PER_LEVEL,
)
from player import Player
from shot import Shot
from tests.helpers import pressed


def shot_textures():
    textures = []
    for level in range(WEAPON_MAX_LEVEL + 1):
        texture = pygame.Surface((4 + level, 10 + level), pygame.SRCALPHA)
        texture.fill((255, 255, 255, 255))
        textures.append(texture)
    return textures


class ShootingTestCase(unittest.TestCase):
    def setUp(self):
        self.shots = pygame.sprite.Group()
        self.enterContext(mock.patch.object(Shot, "textures", shot_textures()))
        self.enterContext(mock.patch.object(Shot, "containers", (self.shots,), create=True))
        self.player = Player(640, 360)

    def update_player(self, dt, *keys):
        with mock.patch("pygame.key.get_pressed", return_value=pressed(*keys)):
            self.player.update(dt)


class BeamAnglesTest(ShootingTestCase):
    def test_single_beam_below_level_two(self):
        for level in (0, 1):
            with self.subTest(level=level):
                self.player.weapon_level = level
                self.assertEqual(self.player.beam_angles(), [0])

    def test_side_beams_from_level_two(self):
        for level in (2, 3, 4):
            with self.subTest(level=level):
                self.player.weapon_level = level
                self.assertEqual(self.player.beam_angles(), [0, 90, -90])

    def test_diagonal_beams_at_level_five(self):
        self.player.weapon_level = 5
        self.assertEqual(self.player.beam_angles(), [0, 90, -90, 45, -45])


class ShootCooldownTest(ShootingTestCase):
    def test_base_cooldown_without_upgrades(self):
        self.assertAlmostEqual(self.player.shoot_cooldown(), PLAYER_SHOOT_COOLDOWN_SECONDS)

    def test_cooldown_shrinks_with_every_weapon_level(self):
        cooldowns = []
        for level in range(WEAPON_MAX_LEVEL + 1):
            self.player.weapon_level = level
            cooldowns.append(self.player.shoot_cooldown())
        self.assertEqual(cooldowns, sorted(cooldowns, reverse=True))
        self.assertEqual(len(set(cooldowns)), WEAPON_MAX_LEVEL + 1)

    def test_cooldown_formula_at_known_levels(self):
        self.player.weapon_level = 4
        self.assertAlmostEqual(self.player.shoot_cooldown(), 0.15)
        self.player.weapon_level = 5
        self.assertAlmostEqual(self.player.shoot_cooldown(), 0.3 / 2.25)


class ShootTest(ShootingTestCase):
    def test_fresh_player_fires_one_shot_from_its_position(self):
        self.player.shoot()
        self.assertEqual(len(self.shots), 1)
        shot = next(iter(self.shots))
        self.assertEqual(shot.position, pygame.Vector2(640, 360))
        self.assertEqual(shot.velocity, pygame.Vector2(0, PLAYER_SHOT_SPEED))
        self.assertEqual(shot.level, 0)

    def test_shot_follows_the_ship_rotation(self):
        self.player.rotation = 90
        self.player.shoot()
        shot = next(iter(self.shots))
        self.assertAlmostEqual(shot.velocity.x, -PLAYER_SHOT_SPEED)
        self.assertAlmostEqual(shot.velocity.y, 0)

    def test_firing_starts_the_cooldown(self):
        self.player.shoot()
        self.assertAlmostEqual(self.player.shoot_timer, PLAYER_SHOOT_COOLDOWN_SECONDS)

    def test_no_second_shot_during_the_cooldown(self):
        self.player.shoot()
        self.player.shoot()
        self.assertEqual(len(self.shots), 1)

    def test_fires_when_the_timer_is_exactly_zero(self):
        self.player.shoot_timer = 0
        self.player.shoot()
        self.assertEqual(len(self.shots), 1)

    def test_does_not_fire_while_the_timer_is_positive(self):
        self.player.shoot_timer = 0.001
        self.player.shoot()
        self.assertEqual(len(self.shots), 0)

    def test_invulnerable_player_cannot_fire(self):
        self.player.start_invulnerability()
        self.player.shoot()
        self.assertEqual(len(self.shots), 0)
        self.assertEqual(self.player.shoot_timer, 0)

    def test_every_beam_gets_a_shot_at_full_speed(self):
        self.player.weapon_level = 5
        self.player.shoot()
        self.assertEqual(len(self.shots), 5)
        for shot in self.shots:
            self.assertAlmostEqual(shot.velocity.length(), PLAYER_SHOT_SPEED)
        directions = {(round(shot.velocity.x), round(shot.velocity.y)) for shot in self.shots}
        self.assertEqual(len(directions), 5)

    def test_side_beams_fly_perpendicular_to_the_ship(self):
        self.player.weapon_level = 2
        self.player.shoot()
        velocities = sorted((round(shot.velocity.x), round(shot.velocity.y)) for shot in self.shots)
        self.assertEqual(velocities, [(-PLAYER_SHOT_SPEED, 0), (0, PLAYER_SHOT_SPEED), (PLAYER_SHOT_SPEED, 0)])

    def test_shots_carry_the_weapon_level(self):
        self.player.weapon_level = 3
        self.player.shoot()
        for shot in self.shots:
            self.assertEqual(shot.level, 3)

    def test_higher_level_shots_are_bigger(self):
        self.player.weapon_level = 3
        self.player.shoot()
        shot = next(iter(self.shots))
        self.assertAlmostEqual(shot.radius, SHOT_RADIUS * (1 + WEAPON_SHOT_SCALE_PER_LEVEL * 3))


class AutoFireTest(ShootingTestCase):
    def test_update_fires_automatically(self):
        self.update_player(1 / 60)
        self.assertEqual(len(self.shots), 1)

    def test_update_respects_the_cooldown(self):
        self.update_player(1 / 60)
        self.update_player(0.1)
        self.assertEqual(len(self.shots), 1)

    def test_update_fires_again_once_the_cooldown_has_elapsed(self):
        self.update_player(1 / 60)
        self.update_player(0.29)
        self.assertEqual(len(self.shots), 1)
        self.update_player(0.02)
        self.assertEqual(len(self.shots), 2)

    def test_upgraded_weapon_fires_faster(self):
        self.player.weapon_level = 1
        self.update_player(1 / 60)
        self.update_player(0.23)
        self.assertEqual(len(self.shots), 1)
        self.update_player(0.02)
        self.assertEqual(len(self.shots), 2)

    def test_invulnerability_pauses_auto_fire_until_it_wears_off(self):
        self.player.start_invulnerability()
        self.update_player(1.0)
        self.assertEqual(len(self.shots), 0)
        self.update_player(3.0)
        self.assertEqual(len(self.shots), 1)


class ShotTest(ShootingTestCase):
    def test_radius_grows_with_the_level(self):
        self.assertEqual(Shot(0, 0).radius, SHOT_RADIUS)
        self.assertAlmostEqual(Shot(0, 0, 2).radius, SHOT_RADIUS * (1 + WEAPON_SHOT_SCALE_PER_LEVEL * 2))

    def test_is_added_to_its_containers(self):
        shot = Shot(10, 10)
        self.assertIn(shot, self.shots)

    def test_update_moves_by_velocity_times_dt(self):
        shot = Shot(100, 100)
        shot.velocity = pygame.Vector2(200, -100)
        shot.update(0.5)
        self.assertEqual(shot.position, pygame.Vector2(200, 50))
        self.assertIn(shot, self.shots)

    def test_leaving_the_screen_kills_the_shot(self):
        cases = {
            "left": (-SHOT_RADIUS - 0.1, 100),
            "right": (SCREEN_WIDTH + SHOT_RADIUS + 0.1, 100),
            "top": (100, -SHOT_RADIUS - 0.1),
            "bottom": (100, SCREEN_HEIGHT + SHOT_RADIUS + 0.1),
        }
        for side, (x, y) in cases.items():
            with self.subTest(side=side):
                shot = Shot(x, y)
                shot.update(0)
                self.assertNotIn(shot, self.shots)

    def test_shot_exactly_on_the_margin_is_still_alive(self):
        cases = [(-SHOT_RADIUS, 100), (SCREEN_WIDTH + SHOT_RADIUS, 100), (100, -SHOT_RADIUS), (100, SCREEN_HEIGHT + SHOT_RADIUS)]
        for x, y in cases:
            with self.subTest(position=(x, y)):
                shot = Shot(x, y)
                shot.update(0)
                self.assertIn(shot, self.shots)

    def test_shot_does_not_wrap_around_the_screen(self):
        shot = Shot(SCREEN_WIDTH - 1, 100)
        shot.velocity = pygame.Vector2(100, 0)
        shot.update(1.0)
        self.assertNotIn(shot, self.shots)

    def test_unrotated_image_without_velocity(self):
        shot = Shot(0, 0, 1)
        self.assertIs(shot.rotated_image(), Shot.textures[1])

    def test_image_follows_the_flight_direction(self):
        shot = Shot(0, 0, 0)
        shot.velocity = pygame.Vector2(0, -1)
        self.assertEqual(shot.rotated_image().get_size(), (4, 10))
        shot.velocity = pygame.Vector2(1, 0)
        self.assertEqual(shot.rotated_image().get_size(), (10, 4))

    def test_bounding_radius_is_half_the_texture_diagonal(self):
        self.enterContext(mock.patch.object(Shot, "textures", [pygame.Surface((6, 8))]))
        self.assertAlmostEqual(Shot(0, 0, 0).bounding_radius(), 5.0)

    def test_mask_covers_the_texture(self):
        mask = Shot(0, 0, 0).get_mask()
        self.assertEqual(mask.count(), 4 * 10)

    def test_draw_paints_the_shot_at_its_position(self):
        screen = pygame.Surface((200, 200))
        Shot(100, 100, 0).draw(screen)
        self.assertEqual(screen.get_at((100, 100))[:3], (255, 255, 255))
        self.assertEqual(screen.get_at((10, 10))[:3], (0, 0, 0))

    def test_shots_collide_with_nearby_shapes(self):
        shot = Shot(100, 100, 0)
        other = Shot(102, 102, 0)
        self.assertTrue(shot.collides_with(other))
        self.assertFalse(shot.collides_with(Shot(300, 300, 0)))


if __name__ == "__main__":
    unittest.main()
