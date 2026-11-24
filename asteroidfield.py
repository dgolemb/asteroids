import random
from collections.abc import Callable

import pygame
from asteroid import Asteroid
from constants import *
from logger import log_event

Edge = tuple[pygame.Vector2, Callable[[float], pygame.Vector2]]


class AsteroidField(pygame.sprite.Sprite):
    containers: pygame.sprite.Group

    edges: list[Edge] = [
        (
            pygame.Vector2(1, 0),
            lambda y: pygame.Vector2(0, y * SCREEN_HEIGHT),
        ),
        (
            pygame.Vector2(-1, 0),
            lambda y: pygame.Vector2(SCREEN_WIDTH, y * SCREEN_HEIGHT),
        ),
        (
            pygame.Vector2(0, 1),
            lambda x: pygame.Vector2(x * SCREEN_WIDTH, 0),
        ),
        (
            pygame.Vector2(0, -1),
            lambda x: pygame.Vector2(x * SCREEN_WIDTH, SCREEN_HEIGHT),
        ),
    ]

    def __init__(self, asteroids: pygame.sprite.Group) -> None:
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.asteroids = asteroids
        self.spawn_timer = 0.0
        self.level = 1
        self.level_timer = 0.0

    def level_duration(self) -> float:
        return DIFFICULTY_FIRST_LEVEL_SECONDS + (self.level - 1) * DIFFICULTY_LEVEL_DURATION_STEP_SECONDS

    def speed_multiplier(self) -> float:
        return 1 + (self.level - 1) * DIFFICULTY_SPEED_INCREASE_PER_LEVEL

    def score_multiplier(self) -> float:
        return 1 + (self.level - 1) * DIFFICULTY_SCORE_INCREASE_PER_LEVEL

    def spawn_interval(self) -> float:
        return ASTEROID_SPAWN_RATE_SECONDS * DIFFICULTY_SPAWN_INTERVAL_FACTOR_PER_LEVEL ** (self.level - 1)

    def max_count(self) -> int:
        return min(
            ASTEROID_MAX_COUNT,
            ASTEROID_START_MAX_COUNT + (self.level - 1) * ASTEROID_MAX_COUNT_INCREASE_PER_LEVEL,
        )

    def spawn(
        self, radius: float, position: pygame.Vector2, velocity: pygame.Vector2
    ) -> None:
        asteroid = Asteroid(position.x, position.y, radius)
        asteroid.velocity = velocity

    def update(self, dt: float) -> None:
        self.level_timer += dt
        if self.level_timer >= self.level_duration():
            self.level_timer -= self.level_duration()
            self.level += 1
            log_event("level_up", level=self.level)

        self.spawn_timer += dt
        if self.spawn_timer > self.spawn_interval():
            self.spawn_timer = 0
            if len(self.asteroids) >= self.max_count():
                return

            # spawn a new asteroid at a random edge
            edge = random.choice(self.edges)
            speed = random.randint(40, 100) * self.speed_multiplier()
            velocity = edge[0] * speed
            velocity = velocity.rotate(random.randint(-30, 30))
            position = edge[1](random.uniform(0, 1))
            kind = random.randint(1, ASTEROID_KINDS)
            self.spawn(ASTEROID_MIN_RADIUS * kind, position, velocity)