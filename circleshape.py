import math
import pygame
from constants import SCREEN_WIDTH, SCREEN_HEIGHT


# Base class for game objects
class CircleShape(pygame.sprite.Sprite):
    containers: tuple[pygame.sprite.Group, ...]

    def __init__(self, x: float, y: float, radius: float) -> None:
        # we will be using this later
        if hasattr(self, "containers"):
            super().__init__(*self.containers)
        else:
            super().__init__()

        self.position: pygame.Vector2 = pygame.Vector2(x, y)
        self.velocity = pygame.Vector2(0, 0)
        self.radius = radius

    def draw(self, screen: pygame.Surface) -> None:
        # must override
        pass

    def update(self, dt: float) -> None:
        # must override
        pass

    def wrap_position(self) -> None:
        self.position.x %= SCREEN_WIDTH
        self.position.y %= SCREEN_HEIGHT

    def ghost_offsets(self, extent: float | None = None) -> list[pygame.Vector2]:
        if extent is None:
            extent = self.radius
        x_offsets = [0.0]
        if self.position.x < extent:
            x_offsets.append(SCREEN_WIDTH)
        if self.position.x > SCREEN_WIDTH - extent:
            x_offsets.append(-SCREEN_WIDTH)
        y_offsets = [0.0]
        if self.position.y < extent:
            y_offsets.append(SCREEN_HEIGHT)
        if self.position.y > SCREEN_HEIGHT - extent:
            y_offsets.append(-SCREEN_HEIGHT)
        return [pygame.Vector2(dx, dy) for dx in x_offsets for dy in y_offsets]

    def collides_with(self, other: "CircleShape") -> bool:
        dx = abs(self.position.x - other.position.x) % SCREEN_WIDTH
        dx = min(dx, SCREEN_WIDTH - dx)
        dy = abs(self.position.y - other.position.y) % SCREEN_HEIGHT
        dy = min(dy, SCREEN_HEIGHT - dy)
        return math.hypot(dx, dy) <= self.radius + other.radius