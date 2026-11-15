import pygame
from shape import Shape
from constants import (
    PLAYER_RADIUS,
    PLAYER_TURN_SPEED,
    PLAYER_SPEED,
    PLAYER_ACCELERATION,
    PLAYER_DECELERATION,
    PLAYER_BRAKE_DECELERATION,
    PLAYER_SHOT_SPEED,
    PLAYER_SHOOT_COOLDOWN_SECONDS,
    PLAYER_RESPAWN_INVULNERABILITY_SECONDS,
    PLAYER_BLINK_INTERVAL_SECONDS,
    SHIELD_KIND,
    SHIELD_RADIUS,
    SHIELD_LINE_WIDTH,
    SHIELD_COLOR,
    SHIELD_BLINK_SECONDS,
    SHIELD_BLINK_INTERVAL_SECONDS,
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
)
from shot import Shot


def move_toward_zero(value: float, step: float) -> float:
    if value > 0:
        return max(0.0, value - step)
    return min(0.0, value + step)


class Player(Shape):
    texture: pygame.Surface

    def __init__(self, x: float, y: float) -> None:
        super().__init__(x, y, PLAYER_RADIUS)
        self.rotation = 0
        self.speed = 0.0
        self.shoot_timer = 0
        self.invulnerable_timer = 0
        self.active_effects: dict[str, float] = {}

    def is_invulnerable(self) -> bool:
        return self.invulnerable_timer > 0

    def add_effect(self, kind: str, duration: float) -> None:
        self.active_effects[kind] = duration

    def has_effect(self, kind: str) -> bool:
        return self.active_effects.get(kind, 0) > 0

    def update_effects(self, dt: float) -> None:
        for kind in list(self.active_effects):
            self.active_effects[kind] -= dt
            if self.active_effects[kind] <= 0:
                del self.active_effects[kind]

    def shield_active(self) -> bool:
        return self.has_effect(SHIELD_KIND)

    def draw_shield(self, screen: pygame.Surface) -> None:
        if not self.shield_active():
            return
        time_left = self.active_effects[SHIELD_KIND]
        if time_left <= SHIELD_BLINK_SECONDS and int(time_left / SHIELD_BLINK_INTERVAL_SECONDS) % 2 == 1:
            return
        for offset in self.ghost_offsets(SHIELD_RADIUS):
            center = self.position + offset
            pygame.draw.circle(
                screen,
                SHIELD_COLOR,
                (round(center.x), round(center.y)),
                SHIELD_RADIUS,
                SHIELD_LINE_WIDTH,
            )

    def respawn(self) -> None:
        self.position = pygame.Vector2(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
        self.rotation = 0
        self.velocity = pygame.Vector2(0, 0)
        self.speed = 0.0
        self.invulnerable_timer = PLAYER_RESPAWN_INVULNERABILITY_SECONDS

    def rotated_image(self) -> pygame.Surface:
        return pygame.transform.rotate(self.texture, 180 - self.rotation)

    def bounding_radius(self) -> float:
        return self.radius * 1.5

    def get_mask(self) -> pygame.Mask:
        return pygame.mask.from_surface(self.rotated_image())

    def draw(self, screen: pygame.Surface) -> None:
        if self.is_invulnerable() and int(self.invulnerable_timer / PLAYER_BLINK_INTERVAL_SECONDS) % 2 == 1:
            return
        rotated = self.rotated_image()
        for offset in self.ghost_offsets(self.bounding_radius()):
            center = self.position + offset
            screen.blit(rotated, rotated.get_rect(center=(round(center.x), round(center.y))))

    def rotate(self, dt: float) -> None:
        self.rotation += PLAYER_TURN_SPEED * dt

    def apply_thrust(self, direction: int, dt: float) -> None:
        if direction == 0:
            self.speed = move_toward_zero(self.speed, PLAYER_DECELERATION * dt)
        elif self.speed * direction < 0:
            self.speed = move_toward_zero(self.speed, PLAYER_BRAKE_DECELERATION * dt)
        else:
            self.speed += direction * PLAYER_ACCELERATION * dt
            self.speed = max(-PLAYER_SPEED, min(PLAYER_SPEED, self.speed))

    def move(self, dt: float) -> None:
        forward = pygame.Vector2(0, 1).rotate(self.rotation)
        self.velocity = forward * self.speed
        self.position += self.velocity * dt
        self.wrap_position()

    def shoot(self) -> None:
        if self.is_invulnerable():
            return
        if self.shoot_timer > 0:
            return
        else:
            self.shoot_timer = PLAYER_SHOOT_COOLDOWN_SECONDS
        shot = Shot(self.position.x, self.position.y)
        shot.velocity = pygame.Vector2(0, 1).rotate(self.rotation) * PLAYER_SHOT_SPEED

    def update(self, dt: float) -> None:
        self.shoot_timer -= dt
        self.invulnerable_timer = max(0, self.invulnerable_timer - dt)
        self.update_effects(dt)
        keys = pygame.key.get_pressed()

        if keys[pygame.K_a]:
            self.rotate(-dt)
        if keys[pygame.K_d]:
            self.rotate(dt)
        direction = 0
        if keys[pygame.K_w]:
            direction += 1
        if keys[pygame.K_s]:
            direction -= 1
        self.apply_thrust(direction, dt)
        self.move(dt)
        if keys[pygame.K_SPACE]:
            self.shoot()

    