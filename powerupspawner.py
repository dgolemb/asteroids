import random
import pygame
from constants import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    POWERUP_RADIUS,
    POWERUP_SPAWN_MIN_SECONDS,
    POWERUP_SPAWN_MAX_SECONDS,
    POWERUP_SPAWN_ATTEMPTS,
)
from powerup import Powerup


class PowerupSpawner(pygame.sprite.Sprite):
    def __init__(self, powerups: pygame.sprite.Group, player) -> None:
        if hasattr(self, "containers"):
            super().__init__(self.containers)
        else:
            super().__init__()
        self.powerups = powerups
        self.player = player
        self.spawn_timer = 0.0
        self.next_spawn_seconds = self.random_interval()

    def random_interval(self) -> float:
        return random.uniform(POWERUP_SPAWN_MIN_SECONDS, POWERUP_SPAWN_MAX_SECONDS)

    def available_kinds(self) -> list[str]:
        present = {powerup.kind for powerup in self.powerups}
        return [
            kind
            for kind in Powerup.textures
            if kind not in present and not self.player.has_effect(kind)
        ]

    def random_position(self) -> pygame.Vector2 | None:
        for _ in range(POWERUP_SPAWN_ATTEMPTS):
            position = pygame.Vector2(
                random.uniform(POWERUP_RADIUS, SCREEN_WIDTH - POWERUP_RADIUS),
                random.uniform(POWERUP_RADIUS, SCREEN_HEIGHT - POWERUP_RADIUS),
            )
            if all(position.distance_to(powerup.position) >= POWERUP_RADIUS * 2 for powerup in self.powerups):
                return position
        return None

    def update(self, dt: float) -> None:
        self.spawn_timer += dt
        if self.spawn_timer < self.next_spawn_seconds:
            return
        kinds = self.available_kinds()
        if not kinds:
            self.spawn_timer = 0.0
            self.next_spawn_seconds = self.random_interval()
            return
        position = self.random_position()
        if position is None:
            return
        self.spawn_timer = 0.0
        self.next_spawn_seconds = self.random_interval()
        Powerup(position.x, position.y, random.choice(kinds))
