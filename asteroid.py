import pygame
import random
from math import ceil
from logger import log_event
from circleshape import CircleShape
from explosion import ExplosionParticle
from constants import (
    LINE_WIDTH,
    ASTEROID_MIN_RADIUS,
    ASTEROID_SCORES,
    EXPLOSION_PARTICLE_COUNT_MIN,
    EXPLOSION_PARTICLE_COUNT_MAX,
    EXPLOSION_PARTICLE_LIFETIME_MIN_SECONDS,
    EXPLOSION_PARTICLE_LIFETIME_MAX_SECONDS,
    EXPLOSION_PARTICLE_SPEED_MIN,
    EXPLOSION_PARTICLE_SPEED_MAX,
    EXPLOSION_SPREAD_SCALE_PER_KIND,
    ASTEROID_ROTATION_SPEED_MAX,
)


class Asteroid(CircleShape):
    texture: pygame.Surface

    def __init__(self, x: float, y: float, radius: float) -> None:
        super().__init__(x, y, radius)
        self.rotation = random.uniform(0, 360)
        self.rotation_speed = random.uniform(-ASTEROID_ROTATION_SPEED_MAX, ASTEROID_ROTATION_SPEED_MAX)
        self.image = self.create_textured_surface()

    def create_textured_surface(self) -> pygame.Surface:
        size = ceil(self.radius * 2)
        texture_width, texture_height = self.texture.get_size()
        offset_x = random.randint(0, max(0, texture_width - size))
        offset_y = random.randint(0, max(0, texture_height - size))
        surface = pygame.Surface((size, size), pygame.SRCALPHA)
        surface.blit(self.texture, (0, 0), pygame.Rect(offset_x, offset_y, size, size))
        mask = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(mask, (255, 255, 255, 255), (size / 2, size / 2), self.radius)
        surface.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        return surface

    def draw(self, screen: pygame.Surface) -> None:
        rotated = pygame.transform.rotate(self.image, self.rotation)
        for offset in self.ghost_offsets():
            center = self.position + offset
            screen.blit(rotated, rotated.get_rect(center=(round(center.x), round(center.y))))
            pygame.draw.circle(screen, "white", center, self.radius, LINE_WIDTH)

    def update(self, dt: float) -> None:
        self.position += self.velocity * dt
        self.rotation = (self.rotation + self.rotation_speed * dt) % 360
        self.wrap_position()

    def get_score(self) -> int:
        kind = round(self.radius / ASTEROID_MIN_RADIUS)
        return ASTEROID_SCORES.get(kind, 0)

    def explode(self) -> None:
        log_event("asteroid_explosion")
        count = random.randint(EXPLOSION_PARTICLE_COUNT_MIN, EXPLOSION_PARTICLE_COUNT_MAX)
        kind = round(self.radius / ASTEROID_MIN_RADIUS)
        spread_scale = 1 + (kind - 1) * EXPLOSION_SPREAD_SCALE_PER_KIND
        for i in range(count):
            angle = i * 360 / count
            speed = random.uniform(EXPLOSION_PARTICLE_SPEED_MIN, EXPLOSION_PARTICLE_SPEED_MAX) * spread_scale
            velocity = pygame.Vector2(0, 1).rotate(angle) * speed
            lifetime = random.uniform(
                EXPLOSION_PARTICLE_LIFETIME_MIN_SECONDS,
                EXPLOSION_PARTICLE_LIFETIME_MAX_SECONDS,
            )
            ExplosionParticle(self.position.x, self.position.y, velocity, lifetime)

    def split(self) -> None:
        self.explode()
        self.kill()
        if self.radius <= ASTEROID_MIN_RADIUS:
            return
        else:
            log_event("asteroid_split")
            random_angle = random.uniform(20, 50)
            first_velocity = self.velocity.rotate(random_angle)
            second_velocity = self.velocity.rotate(-random_angle)
            new_radius = self.radius - ASTEROID_MIN_RADIUS
            first_asteroid = Asteroid(self.position.x, self.position.y, new_radius)
            first_asteroid.velocity = first_velocity * 1.2
            second_asteroid = Asteroid(self.position.x, self.position.y, new_radius)
            second_asteroid.velocity = second_velocity * 1.2