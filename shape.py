import math
import pygame
from constants import SCREEN_WIDTH, SCREEN_HEIGHT


# Base class for game objects
class Shape(pygame.sprite.Sprite):
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

    def bounding_radius(self) -> float:
        return self.radius

    def get_mask(self) -> pygame.Mask:
        size = math.ceil(self.radius * 2)
        surface = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(surface, (255, 255, 255, 255), (size / 2, size / 2), self.radius)
        return pygame.mask.from_surface(surface)

    def wrapped_delta(self, other: "Shape") -> pygame.Vector2:
        dx = (other.position.x - self.position.x + SCREEN_WIDTH / 2) % SCREEN_WIDTH - SCREEN_WIDTH / 2
        dy = (other.position.y - self.position.y + SCREEN_HEIGHT / 2) % SCREEN_HEIGHT - SCREEN_HEIGHT / 2
        return pygame.Vector2(dx, dy)

    def collides_with(self, other: "Shape") -> bool:
        delta = self.wrapped_delta(other)
        if delta.length() > self.bounding_radius() + other.bounding_radius():
            return False
        self_mask = self.get_mask()
        other_mask = other.get_mask()
        self_width, self_height = self_mask.get_size()
        other_width, other_height = other_mask.get_size()
        offset = (
            round(delta.x - other_width / 2 + self_width / 2),
            round(delta.y - other_height / 2 + self_height / 2),
        )
        return self_mask.overlap(other_mask, offset) is not None