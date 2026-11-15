import pygame
from shape import Shape
from constants import (
    POWERUP_RADIUS,
    POWERUP_PICKUP_SECONDS,
    POWERUP_BLINK_SECONDS,
    POWERUP_BLINK_INTERVAL_SECONDS,
)


class Powerup(Shape):
    textures: dict[str, pygame.Surface] = {}

    def __init__(self, x: float, y: float, kind: str) -> None:
        super().__init__(x, y, POWERUP_RADIUS)
        self.kind = kind
        self.time_left = POWERUP_PICKUP_SECONDS

    def update(self, dt: float) -> None:
        self.time_left -= dt
        if self.time_left <= 0:
            self.kill()

    def is_blinking(self) -> bool:
        return self.time_left <= POWERUP_BLINK_SECONDS

    def get_mask(self) -> pygame.Mask:
        return pygame.mask.from_surface(self.textures[self.kind])

    def draw(self, screen: pygame.Surface) -> None:
        if self.is_blinking() and int(self.time_left / POWERUP_BLINK_INTERVAL_SECONDS) % 2 == 1:
            return
        image = self.textures[self.kind]
        screen.blit(image, image.get_rect(center=(round(self.position.x), round(self.position.y))))
