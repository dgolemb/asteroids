import asyncio
import pygame
from constants import *
from logger import log_state, log_event
from player import Player
from asteroid import Asteroid
from asteroidfield import AsteroidField
from shot import Shot
from hud import Hud
from explosion import ExplosionParticle
from powerup import Powerup
from powerupspawner import PowerupSpawner


def load_background():
    tile = pygame.image.load(BACKGROUND_IMAGE_PATH).convert()
    tile_width, tile_height = tile.get_size()
    background = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    for y in range(0, SCREEN_HEIGHT, tile_height):
        for x in range(0, SCREEN_WIDTH, tile_width):
            background.blit(tile, (x, y))
    return background


def load_sprite(path, scale):
    image = pygame.image.load(path).convert_alpha()
    width, height = image.get_size()
    return pygame.transform.smoothscale(image, (round(width * scale), round(height * scale)))


def destroy_asteroid(asteroid, asteroid_field, hud, source):
    points = round(asteroid.get_score() * asteroid_field.score_multiplier())
    log_event(source, score=points)
    hud.add_score(points)
    asteroid.split()


def shield_hits(player, asteroid):
    return player.wrapped_delta(asteroid).length() <= SHIELD_RADIUS + asteroid.radius


def load_pixel_sprite(path, scale):
    image = pygame.image.load(path).convert_alpha()
    width, height = image.get_size()
    return pygame.transform.scale(image, (width * scale, height * scale))


def new_game():
    updatable = pygame.sprite.Group()
    drawable = pygame.sprite.Group()
    asteroids = pygame.sprite.Group()
    shots = pygame.sprite.Group()
    powerups = pygame.sprite.Group()

    Player.containers = (updatable, drawable)
    Asteroid.containers = (asteroids, updatable, drawable)
    AsteroidField.containers = (updatable)
    Shot.containers = (shots, updatable, drawable)
    ExplosionParticle.containers = (updatable, drawable)
    Powerup.containers = (powerups, updatable)
    PowerupSpawner.containers = (updatable)

    player = Player(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
    asteroid_field = AsteroidField(asteroids)
    PowerupSpawner(powerups, player)
    hud = Hud()
    return updatable, drawable, asteroids, shots, powerups, player, asteroid_field, hud


async def main():
    print(f"Starting Asteroids with pygame version: {pygame.version.ver}")
    print(f"Screen width: {SCREEN_WIDTH}")
    print(f"Screen height: {SCREEN_HEIGHT}")

    pygame.init()
    clock = pygame.time.Clock()
    dt = 0.0

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    background = load_background()
    Asteroid.texture = pygame.image.load(ASTEROID_TEXTURE_PATH).convert()
    Asteroid.generate_shapes()
    Player.texture = load_sprite(PLAYER_TEXTURE_PATH, PLAYER_TEXTURE_SCALE)
    Shot.texture = load_sprite(SHOT_TEXTURE_PATH, SHOT_TEXTURE_SCALE)
    Powerup.textures[SHIELD_KIND] = load_pixel_sprite(POWERUP_SHIELD_TEXTURE_PATH, POWERUP_TEXTURE_SCALE)

    updatable, drawable, asteroids, shots, powerups, player, asteroid_field, hud = new_game()

    while True:
        log_state()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
        updatable.update(dt)
        hud.level = asteroid_field.level
        for powerup in powerups:
            if powerup.collides_with(player):
                log_event("powerup_picked", kind=powerup.kind)
                player.add_effect(powerup.kind, POWERUP_EFFECT_SECONDS[powerup.kind])
                powerup.kill()
        for asteroid in asteroids:
            if player.shield_active() and shield_hits(player, asteroid):
                destroy_asteroid(asteroid, asteroid_field, hud, "asteroid_shielded")
                continue
            if not player.is_invulnerable() and asteroid.collides_with(player):
                log_event("player_hit")
                hud.lose_life()
                if hud.is_game_over():
                    print("Game over!")
                    print(f"Final score: {hud.score}")
                    return
                player.respawn()
            for shot in shots:
                if shot.collides_with(asteroid):
                    shot.kill()
                    destroy_asteroid(asteroid, asteroid_field, hud, "asteroid_shot")
                    break
        screen.blit(background, (0, 0))
        for powerup in powerups:
            powerup.draw(screen)
        for object in drawable:
            object.draw(screen)
        player.draw_shield(screen)
        hud.draw(screen)
        pygame.display.flip()
        dt = clock.tick(60) / 1000
        await asyncio.sleep(0)


if __name__ == "__main__":
    asyncio.run(main())
