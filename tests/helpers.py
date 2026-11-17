import unittest
from unittest import mock

import pygame

from asteroid import Asteroid
from explosion import ExplosionParticle


def solid_texture():
    texture = pygame.Surface((64, 64), pygame.SRCALPHA)
    texture.fill((255, 255, 255, 255))
    return texture


class AsteroidTestCase(unittest.TestCase):
    def setUp(self):
        self.asteroids = pygame.sprite.Group()
        self.particles = pygame.sprite.Group()
        self.enterContext(mock.patch.object(Asteroid, "texture", solid_texture(), create=True))
        self.enterContext(mock.patch.object(Asteroid, "shapes", {}))
        self.enterContext(mock.patch.object(Asteroid, "containers", (self.asteroids,), create=True))
        self.enterContext(mock.patch.object(ExplosionParticle, "containers", (self.particles,), create=True))
        self.log_event = self.enterContext(mock.patch("asteroid.log_event"))
        Asteroid.generate_shapes()

    def logged_events(self):
        return [call.args[0] for call in self.log_event.call_args_list]
