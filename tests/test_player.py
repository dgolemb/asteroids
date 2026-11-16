import unittest
from collections import defaultdict
from unittest import mock

import pygame

from constants import (
    PLAYER_ACCELERATION,
    PLAYER_SPEED,
    PLAYER_TURN_SPEED,
)
from player import Player

DT = 1 / 60


class FakeTouch:
    def __init__(self, x=0.0, y=0.0):
        self.stick = pygame.Vector2(x, y)


def pressed(*keys):
    return defaultdict(bool, {key: True for key in keys})


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

    def test_thrust_starts_immediately_while_the_nose_is_still_turning(self):
        player = new_player()
        self.update_with(player, (0, -1), 1)
        self.assertAlmostEqual(player.speed, PLAYER_ACCELERATION * DT)
        self.assertAlmostEqual(abs(player.rotation), PLAYER_TURN_SPEED * DT)

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


if __name__ == "__main__":
    unittest.main()
