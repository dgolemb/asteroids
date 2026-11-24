import random
import pygame
from constants import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    POWERUP_RADIUS,
    POWERUP_SPAWN_MIN_SECONDS,
    POWERUP_SPAWN_MAX_SECONDS,
    POWERUP_SPAWN_ATTEMPTS,
    POWERUP_STACKABLE_KINDS,
    HEART_KIND,
    HEART_SPAWN_MIN_SECONDS,
    HEART_SPAWN_MAX_SECONDS,
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
        self.spawn_timers: dict[str, float] = {}
        self.next_spawn_seconds: dict[str, float] = {}

    def random_interval(self, kind: str) -> float:
        if kind == HEART_KIND:
            return random.uniform(HEART_SPAWN_MIN_SECONDS, HEART_SPAWN_MAX_SECONDS)
        return random.uniform(POWERUP_SPAWN_MIN_SECONDS, POWERUP_SPAWN_MAX_SECONDS)

    def is_available(self, kind: str) -> bool:
        if any(powerup.kind == kind for powerup in self.powerups):
            return False
        if kind == HEART_KIND:
            return True
        return kind in POWERUP_STACKABLE_KINDS or not self.player.has_effect(kind)

    def reset_schedule(self, kind: str) -> None:
        self.spawn_timers[kind] = 0.0
        self.next_spawn_seconds[kind] = self.random_interval(kind)

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
        for kind in Powerup.textures:
            if kind not in self.spawn_timers:
                self.reset_schedule(kind)
            self.spawn_timers[kind] += dt
            if self.spawn_timers[kind] < self.next_spawn_seconds[kind]:
                continue
            if not self.is_available(kind):
                self.reset_schedule(kind)
                continue
            position = self.random_position()
            if position is None:
                continue
            self.reset_schedule(kind)
            Powerup(position.x, position.y, kind)
