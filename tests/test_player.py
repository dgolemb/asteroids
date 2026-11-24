import unittest
from unittest import mock

import pygame

from constants import (
    PLAYER_ACCELERATION,
    PLAYER_BRAKE_DECELERATION,
    PLAYER_DECELERATION,
    PLAYER_RADIUS,
    PLAYER_SPEED,
    PLAYER_TURN_SPEED,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    SHIELD_BLINK_SECONDS,
    SHIELD_COLOR,
    SHIELD_DURATION_SECONDS,
    SHIELD_KIND,
    SHIELD_RADIUS,
    TOUCH_THRUST_ALIGNMENT_DEGREES,
    WEAPON_KIND,
)
from player import Player, move_toward_zero
from tests.helpers import pressed

DT = 1 / 60


class FakeTouch:
    def __init__(self, x=0.0, y=0.0):
        self.stick = pygame.Vector2(x, y)


def new_player():
    player = Player(640, 360)
    player.shoot_timer = 1000
    return player


class SteerTowardTest(unittest.TestCase):
    def test_nose_ends_up_pointing_along_the_vector(self):
        for direction in [(0, -1), (1, 0), (-1, 0), (0, 1), (1, 1), (-1, -2)]:
            with self.subTest(direction=direction):
                player = new_player()
                vector = pygame.Vector2(direction).normalize()
                for _ in range(120):
                    player.steer_toward(vector, DT)
                nose = pygame.Vector2(0, 1).rotate(player.rotation)
                self.assertAlmostEqual(nose.x, vector.x, places=5)
                self.assertAlmostEqual(nose.y, vector.y, places=5)

    def test_turn_per_frame_is_limited_by_turn_speed(self):
        player = new_player()
        player.steer_toward(pygame.Vector2(1, 0), DT)
        self.assertAlmostEqual(abs(player.rotation), PLAYER_TURN_SPEED * DT)

    def test_takes_the_shorter_arc(self):
        player = new_player()
        player.rotation = 170
        target = pygame.Vector2(0, 1).rotate(-170)
        player.steer_toward(target, DT)
        self.assertGreater(player.rotation, 170)

    def test_takes_the_shorter_arc_in_the_other_direction(self):
        player = new_player()
        player.rotation = -170
        target = pygame.Vector2(0, 1).rotate(170)
        player.steer_toward(target, DT)
        self.assertLess(player.rotation, -170)

    def test_stays_put_when_already_aligned(self):
        player = new_player()
        player.steer_toward(pygame.Vector2(0, 1), DT)
        self.assertAlmostEqual(player.rotation, 0.0)


class TouchThrustTest(unittest.TestCase):
    def update_with(self, player, stick, frames):
        player.touch = FakeTouch(*stick)
        with mock.patch("pygame.key.get_pressed", return_value=pressed()):
            for _ in range(frames):
                player.update(DT)

    def test_full_deflection_reaches_max_speed(self):
        player = new_player()
        self.update_with(player, (0, 1), 300)
        self.assertAlmostEqual(player.speed, PLAYER_SPEED)

    def test_light_deflection_also_reaches_max_speed(self):
        player = new_player()
        self.update_with(player, (0, 0.1), 300)
        self.assertAlmostEqual(player.speed, PLAYER_SPEED)

    def test_acceleration_uses_player_acceleration(self):
        player = new_player()
        self.update_with(player, (0, 1), 1)
        self.assertAlmostEqual(player.speed, PLAYER_ACCELERATION * DT)

    def test_no_thrust_while_the_nose_is_far_from_the_vector(self):
        player = new_player()
        self.update_with(player, (0, -1), 10)
        self.assertEqual(player.speed, 0.0)
        self.assertAlmostEqual(abs(player.rotation), PLAYER_TURN_SPEED * DT * 10)

    def test_thrust_starts_once_the_nose_is_aligned(self):
        player = new_player()
        self.update_with(player, (0, -1), 60)
        self.assertGreater(player.speed, 0.0)

    def test_thrust_starts_within_the_alignment_threshold(self):
        player = new_player()
        player.rotation = 180 - TOUCH_THRUST_ALIGNMENT_DEGREES + 1
        self.update_with(player, (0, -1), 1)
        self.assertAlmostEqual(player.speed, PLAYER_ACCELERATION * DT)

    def test_speed_coasts_down_while_turning_without_thrust(self):
        player = new_player()
        player.speed = PLAYER_SPEED
        self.update_with(player, (0, -1), 1)
        self.assertAlmostEqual(player.speed, PLAYER_SPEED - PLAYER_DECELERATION * DT)

    def test_thrust_at_exactly_the_alignment_threshold(self):
        player = new_player()
        player.speed = 100
        with mock.patch.object(player, "steer_toward", return_value=float(TOUCH_THRUST_ALIGNMENT_DEGREES)):
            player.apply_touch_thrust(pygame.Vector2(0, -1), DT)
        self.assertAlmostEqual(player.speed, 100 + PLAYER_ACCELERATION * DT)

    def test_no_thrust_just_beyond_the_alignment_threshold(self):
        player = new_player()
        player.speed = 100
        with mock.patch.object(player, "steer_toward", return_value=TOUCH_THRUST_ALIGNMENT_DEGREES + 0.01):
            player.apply_touch_thrust(pygame.Vector2(0, -1), DT)
        self.assertAlmostEqual(player.speed, 100 - PLAYER_DECELERATION * DT)

    def test_thrust_when_fully_aligned(self):
        player = new_player()
        player.speed = 100
        with mock.patch.object(player, "steer_toward", return_value=0.0):
            player.apply_touch_thrust(pygame.Vector2(0, 1), DT)
        self.assertAlmostEqual(player.speed, 100 + PLAYER_ACCELERATION * DT)

    def test_steer_toward_reports_the_remaining_misalignment(self):
        player = new_player()
        remaining = player.steer_toward(pygame.Vector2(0, -1), DT)
        self.assertAlmostEqual(remaining, 180 - PLAYER_TURN_SPEED * DT)

    def test_nose_catches_up_with_the_vector_while_thrusting(self):
        player = new_player()
        self.update_with(player, (1, 0), 120)
        nose = pygame.Vector2(0, 1).rotate(player.rotation)
        self.assertAlmostEqual(nose.x, 1.0, places=5)
        self.assertAlmostEqual(nose.y, 0.0, places=5)
        self.assertAlmostEqual(player.speed, PLAYER_SPEED)

    def test_released_stick_lets_the_ship_coast_down(self):
        player = new_player()
        player.speed = PLAYER_SPEED
        self.update_with(player, (0, 0), 300)
        self.assertEqual(player.speed, 0.0)


class KeyboardRegressionTest(unittest.TestCase):
    def test_w_accelerates_without_touch(self):
        player = new_player()
        with mock.patch("pygame.key.get_pressed", return_value=pressed(pygame.K_w)):
            player.update(DT)
        self.assertAlmostEqual(player.speed, PLAYER_ACCELERATION * DT)

    def test_d_rotates_without_touch(self):
        player = new_player()
        with mock.patch("pygame.key.get_pressed", return_value=pressed(pygame.K_d)):
            player.update(DT)
        self.assertAlmostEqual(player.rotation, PLAYER_TURN_SPEED * DT)

    def test_a_rotates_the_other_way(self):
        player = new_player()
        with mock.patch("pygame.key.get_pressed", return_value=pressed(pygame.K_a)):
            player.update(DT)
        self.assertAlmostEqual(player.rotation, -PLAYER_TURN_SPEED * DT)

    def test_s_reverses(self):
        player = new_player()
        with mock.patch("pygame.key.get_pressed", return_value=pressed(pygame.K_s)):
            player.update(DT)
        self.assertAlmostEqual(player.speed, -PLAYER_ACCELERATION * DT)

    def test_s_brakes_forward_motion_harder_than_coasting(self):
        player = new_player()
        player.speed = PLAYER_SPEED
        with mock.patch("pygame.key.get_pressed", return_value=pressed(pygame.K_s)):
            player.update(DT)
        self.assertAlmostEqual(player.speed, PLAYER_SPEED - PLAYER_BRAKE_DECELERATION * DT)

    def test_releasing_the_keys_coasts_down_gently(self):
        player = new_player()
        player.speed = PLAYER_SPEED
        with mock.patch("pygame.key.get_pressed", return_value=pressed()):
            player.update(DT)
        self.assertAlmostEqual(player.speed, PLAYER_SPEED - PLAYER_DECELERATION * DT)

    def test_w_and_s_together_cancel_out_into_coasting(self):
        player = new_player()
        player.speed = PLAYER_SPEED
        with mock.patch("pygame.key.get_pressed", return_value=pressed(pygame.K_w, pygame.K_s)):
            player.update(DT)
        self.assertAlmostEqual(player.speed, PLAYER_SPEED - PLAYER_DECELERATION * DT)

    def test_a_and_d_together_cancel_out(self):
        player = new_player()
        with mock.patch("pygame.key.get_pressed", return_value=pressed(pygame.K_a, pygame.K_d)):
            player.update(DT)
        self.assertAlmostEqual(player.rotation, 0.0)

    def test_keyboard_thrust_wins_over_the_stick(self):
        player = new_player()
        player.touch = FakeTouch(1, 0)
        with mock.patch("pygame.key.get_pressed", return_value=pressed(pygame.K_w)):
            player.update(DT)
        self.assertEqual(player.rotation, 0)
        self.assertAlmostEqual(player.speed, PLAYER_ACCELERATION * DT)

    def test_idle_touch_bridge_does_not_change_keyboard_play(self):
        player = new_player()
        player.touch = FakeTouch(0, 0)
        with mock.patch("pygame.key.get_pressed", return_value=pressed(pygame.K_w)):
            player.update(DT)
        self.assertAlmostEqual(player.speed, PLAYER_ACCELERATION * DT)


class MoveTowardZeroTest(unittest.TestCase):
    def test_positive_value_shrinks(self):
        self.assertEqual(move_toward_zero(10.0, 3.0), 7.0)

    def test_negative_value_shrinks(self):
        self.assertEqual(move_toward_zero(-10.0, 3.0), -7.0)

    def test_never_overshoots_zero(self):
        self.assertEqual(move_toward_zero(2.0, 5.0), 0.0)
        self.assertEqual(move_toward_zero(-2.0, 5.0), 0.0)

    def test_zero_stays_zero(self):
        self.assertEqual(move_toward_zero(0.0, 5.0), 0.0)


class ApplyThrustTest(unittest.TestCase):
    def test_forward_thrust_is_capped_at_top_speed(self):
        player = new_player()
        player.speed = PLAYER_SPEED - 1
        player.apply_thrust(1, 1.0)
        self.assertEqual(player.speed, PLAYER_SPEED)

    def test_reverse_thrust_is_capped_at_minus_top_speed(self):
        player = new_player()
        player.speed = -PLAYER_SPEED + 1
        player.apply_thrust(-1, 1.0)
        self.assertEqual(player.speed, -PLAYER_SPEED)

    def test_opposite_thrust_brakes_instead_of_accelerating(self):
        player = new_player()
        player.speed = 100
        player.apply_thrust(-1, DT)
        self.assertAlmostEqual(player.speed, 100 - PLAYER_BRAKE_DECELERATION * DT)

    def test_braking_stops_at_zero_instead_of_reversing(self):
        player = new_player()
        player.speed = 5
        player.apply_thrust(-1, DT)
        self.assertEqual(player.speed, 0.0)

    def test_braking_works_in_reverse_too(self):
        player = new_player()
        player.speed = -100
        player.apply_thrust(1, DT)
        self.assertAlmostEqual(player.speed, -100 + PLAYER_BRAKE_DECELERATION * DT)

    def test_no_thrust_coasts_toward_zero_from_both_sides(self):
        forward = new_player()
        forward.speed = 100
        forward.apply_thrust(0, DT)
        backward = new_player()
        backward.speed = -100
        backward.apply_thrust(0, DT)
        self.assertAlmostEqual(forward.speed, 100 - PLAYER_DECELERATION * DT)
        self.assertAlmostEqual(backward.speed, -100 + PLAYER_DECELERATION * DT)


class MoveTest(unittest.TestCase):
    def test_moves_along_the_nose_direction(self):
        player = new_player()
        player.speed = 120
        player.move(0.5)
        self.assertEqual(player.position, pygame.Vector2(640, 360 + 60))
        self.assertEqual(player.velocity, pygame.Vector2(0, 120))

    def test_rotation_changes_the_direction_of_travel(self):
        player = new_player()
        player.speed = 120
        player.rotation = 90
        player.move(0.5)
        self.assertAlmostEqual(player.position.x, 640 - 60)
        self.assertAlmostEqual(player.position.y, 360)

    def test_reverse_speed_moves_backwards(self):
        player = new_player()
        player.speed = -100
        player.move(0.5)
        self.assertAlmostEqual(player.position.y, 360 - 50)

    def test_wraps_around_the_screen(self):
        player = new_player()
        player.position = pygame.Vector2(100, SCREEN_HEIGHT - 5)
        player.speed = 100
        player.move(0.1)
        self.assertAlmostEqual(player.position.y, 5)

    def test_standing_still_does_not_move(self):
        player = new_player()
        player.move(1.0)
        self.assertEqual(player.position, pygame.Vector2(640, 360))


class ShieldTest(unittest.TestCase):
    def ring_pixels(self, screen, center):
        return [
            screen.get_at((center[0] + offset, center[1]))[:3]
            for offset in range(SHIELD_RADIUS - 3, SHIELD_RADIUS + 1)
        ]

    def draw_shield(self, time_left):
        screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        player = Player(300, 300)
        player.add_effect(SHIELD_KIND, time_left)
        player.draw_shield(screen)
        return screen

    def test_shield_is_inactive_by_default(self):
        self.assertFalse(Player(0, 0).shield_active())

    def test_shield_is_active_with_the_effect(self):
        player = Player(0, 0)
        player.add_effect(SHIELD_KIND, SHIELD_DURATION_SECONDS)
        self.assertTrue(player.shield_active())

    def test_shield_expires_with_the_effect_timer(self):
        player = Player(0, 0)
        player.add_effect(SHIELD_KIND, SHIELD_DURATION_SECONDS)
        player.update_effects(SHIELD_DURATION_SECONDS - 0.5)
        self.assertTrue(player.shield_active())
        player.update_effects(0.5)
        self.assertFalse(player.shield_active())

    def test_shield_expiry_does_not_touch_the_weapon(self):
        player = Player(0, 0)
        player.weapon_level = 3
        player.add_effect(WEAPON_KIND, 50)
        player.add_effect(SHIELD_KIND, 1)
        player.update_effects(2)
        self.assertEqual(player.weapon_level, 3)
        self.assertTrue(player.has_effect(WEAPON_KIND))

    def test_ring_is_drawn_around_the_ship(self):
        screen = self.draw_shield(SHIELD_DURATION_SECONDS)
        self.assertIn(SHIELD_COLOR, self.ring_pixels(screen, (300, 300)))
        self.assertEqual(screen.get_at((300, 300))[:3], (0, 0, 0))

    def test_nothing_is_drawn_without_the_effect(self):
        screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        Player(300, 300).draw_shield(screen)
        self.assertNotIn(SHIELD_COLOR, self.ring_pixels(screen, (300, 300)))

    def test_ring_is_hidden_in_the_dark_blink_phase(self):
        screen = self.draw_shield(0.3)
        self.assertNotIn(SHIELD_COLOR, self.ring_pixels(screen, (300, 300)))

    def test_ring_is_shown_in_the_bright_blink_phase(self):
        screen = self.draw_shield(0.1)
        self.assertIn(SHIELD_COLOR, self.ring_pixels(screen, (300, 300)))

    def test_ring_does_not_blink_before_the_warning_period(self):
        screen = self.draw_shield(SHIELD_BLINK_SECONDS + 0.3)
        self.assertIn(SHIELD_COLOR, self.ring_pixels(screen, (300, 300)))

    def test_ring_is_repeated_across_the_screen_edge(self):
        screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        player = Player(10, 300)
        player.add_effect(SHIELD_KIND, SHIELD_DURATION_SECONDS)
        player.draw_shield(screen)
        ghost_center = SCREEN_WIDTH + 10
        ghost_ring_x = ghost_center - SHIELD_RADIUS
        self.assertIn(SHIELD_COLOR, [screen.get_at((ghost_ring_x + offset, 300))[:3] for offset in range(0, 4)])


class DrawAndMaskTest(unittest.TestCase):
    def setUp(self):
        texture = pygame.Surface((40, 40), pygame.SRCALPHA)
        texture.fill((255, 255, 255, 255))
        self.enterContext(mock.patch.object(Player, "texture", texture, create=True))

    def test_bounding_radius_is_larger_than_the_hit_radius(self):
        self.assertEqual(Player(0, 0).bounding_radius(), PLAYER_RADIUS * 1.5)

    def test_draw_paints_the_ship_at_its_position(self):
        screen = pygame.Surface((200, 200))
        Player(100, 100).draw(screen)
        self.assertEqual(screen.get_at((100, 100))[:3], (255, 255, 255))
        self.assertEqual(screen.get_at((10, 10))[:3], (0, 0, 0))

    def test_draw_skips_the_dark_phase_of_the_respawn_blink(self):
        screen = pygame.Surface((200, 200))
        player = Player(100, 100)
        player.invulnerable_timer = 0.15
        player.draw(screen)
        self.assertEqual(screen.get_at((100, 100))[:3], (0, 0, 0))

    def test_draw_shows_the_bright_phase_of_the_respawn_blink(self):
        screen = pygame.Surface((200, 200))
        player = Player(100, 100)
        player.invulnerable_timer = 0.05
        player.draw(screen)
        self.assertEqual(screen.get_at((100, 100))[:3], (255, 255, 255))

    def test_mask_follows_the_texture(self):
        self.assertEqual(Player(0, 0).get_mask().count(), 40 * 40)


if __name__ == "__main__":
    unittest.main()
