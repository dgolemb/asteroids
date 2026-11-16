import pygame
from shape import Shape
from constants import SHOT_RADIUS, WEAPON_SHOT_SCALE_PER_LEVEL, SCREEN_WIDTH, SCREEN_HEIGHT


class Shot(Shape):
    textures: list[pygame.Surface] = []

    def __init__(self, x: float, y: float, level: int = 0) -> None:
        super().__init__(x, y, SHOT_RADIUS * (1 + WEAPON_SHOT_SCALE_PER_LEVEL * level))
        self.level = level

    def rotated_image(self) -> pygame.Surface:
        texture = self.textures[self.level]
        if self.velocity.length_squared() == 0:
            return texture
        return pygame.transform.rotate(texture, -pygame.Vector2(0, -1).angle_to(self.velocity))

    def bounding_radius(self) -> float:
        width, height = self.textures[self.level].get_size()
        return pygame.Vector2(width, height).length() / 2

    def get_mask(self) -> pygame.Mask:
        return pygame.mask.from_surface(self.rotated_image())

    def draw(self, screen: pygame.Surface) -> None:
        rotated = self.rotated_image()
        screen.blit(rotated, rotated.get_rect(center=(round(self.position.x), round(self.position.y))))

    def update(self, dt: float) -> None:
        self.position += self.velocity * dt
        if self.is_off_screen():
            self.kill()

    def is_off_screen(self) -> bool:
        return (
            self.position.x < -self.radius
            or self.position.x > SCREEN_WIDTH + self.radius
            or self.position.y < -self.radius
            or self.position.y > SCREEN_HEIGHT + self.radius
        )