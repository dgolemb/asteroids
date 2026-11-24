import unittest
from unittest import mock

import pygame

from constants import EXPLOSION_PARTICLE_RADIUS
from explosion import ExplosionParticle


class ExplosionParticleTest(unittest.TestCase):
    def setUp(self):
        self.particles = pygame.sprite.Group()
        self.enterContext(mock.patch.object(ExplosionParticle, "containers", (self.particles,), create=True))

    def new_particle(self, velocity=(0, 0), lifetime=1.0):
        return ExplosionParticle(100, 100, pygame.Vector2(velocity), lifetime)

    def test_initial_state(self):
        particle = self.new_particle((10, 20), 0.8)
        self.assertEqual(particle.position, pygame.Vector2(100, 100))
        self.assertEqual(particle.velocity, pygame.Vector2(10, 20))
        self.assertEqual(particle.radius, EXPLOSION_PARTICLE_RADIUS)
        self.assertEqual(particle.lifetime, 0.8)
        self.assertEqual(particle.time_left, 0.8)
        self.assertIn(particle, self.particles)

    def test_update_moves_by_velocity_times_dt(self):
        particle = self.new_particle((100, -50))
        particle.update(0.2)
        self.assertEqual(particle.position, pygame.Vector2(120, 90))

    def test_update_counts_down_the_remaining_time(self):
        particle = self.new_particle(lifetime=1.0)
        particle.update(0.25)
        self.assertAlmostEqual(particle.time_left, 0.75)
        self.assertIn(particle, self.particles)

    def test_particle_disappears_when_its_time_is_up(self):
        particle = self.new_particle(lifetime=0.5)
        particle.update(0.25)
        particle.update(0.25)
        self.assertNotIn(particle, self.particles)

    def test_particle_survives_just_before_its_time_is_up(self):
        particle = self.new_particle(lifetime=0.5)
        particle.update(0.49)
        self.assertIn(particle, self.particles)

    def test_draw_fades_out_over_the_lifetime(self):
        brightness = []
        for fraction in (1.0, 0.5, 0.0):
            screen = pygame.Surface((200, 200))
            particle = self.new_particle(lifetime=1.0)
            particle.time_left = fraction
            particle.draw(screen)
            brightness.append(screen.get_at((100, 100))[0])
        self.assertEqual(brightness, [255, 127, 0])

    def test_draw_does_not_go_negative_after_expiry(self):
        screen = pygame.Surface((200, 200))
        particle = self.new_particle(lifetime=1.0)
        particle.time_left = -0.5
        particle.draw(screen)
        self.assertEqual(screen.get_at((100, 100))[:3], (0, 0, 0))


if __name__ == "__main__":
    unittest.main()
