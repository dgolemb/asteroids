import pygame
from circleshape import CircleShape
from constants import EXPLOSION_PARTICLE_RADIUS


class ExplosionParticle(CircleShape):
    def __init__(self, x: float, y: float, velocity: pygame.Vector2, lifetime: float) -> None:
        super().__init__(x, y, EXPLOSION_PARTICLE_RADIUS)
        self.velocity = velocity
        self.lifetime = lifetime
        self.time_left = lifetime

    def draw(self, screen: pygame.Surface) -> None:
        brightness = int(255 * max(self.time_left, 0) / self.lifetime)
        color = (brightness, brightness, brightness)
        pygame.draw.circle(screen, color, self.position, self.radius)

    def update(self, dt: float) -> None:
        self.position += self.velocity * dt
        self.time_left -= dt
        if self.time_left <= 0:
            self.kill()
