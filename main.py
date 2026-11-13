import pygame
import sys
from math import ceil
from constants import *
from logger import log_state, log_event
from player import Player
from asteroid import Asteroid
from asteroidfield import AsteroidField
from shot import Shot
from hud import Hud
from explosion import ExplosionParticle


def load_background():
    image = pygame.image.load(BACKGROUND_IMAGE_PATH).convert()
    width, height = image.get_size()
    scale = max(SCREEN_WIDTH / width, SCREEN_HEIGHT / height)
    scaled = pygame.transform.smoothscale(image, (ceil(width * scale), ceil(height * scale)))
    rect = pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
    rect.center = scaled.get_rect().center
    return scaled.subsurface(rect)


def main():
    print(f"Starting Asteroids with pygame version: {pygame.version.ver}")
    print(f"Screen width: {SCREEN_WIDTH}")
    print(f"Screen height: {SCREEN_HEIGHT}")

    pygame.init()
    clock = pygame.time.Clock()
    dt = 0.0

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    background = load_background()

    updatable = pygame.sprite.Group()
    drawable = pygame.sprite.Group()
    asteroids = pygame.sprite.Group()
    shots = pygame.sprite.Group()

    Player.containers = (updatable, drawable)
    Asteroid.containers = (asteroids, updatable, drawable)
    AsteroidField.containers = (updatable)
    Shot.containers = (shots, updatable, drawable)
    ExplosionParticle.containers = (updatable, drawable)

    player = Player(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
    asteroid_field = AsteroidField(asteroids)
    hud = Hud()


    while True:
        log_state()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
        updatable.update(dt)
        for asteroid in asteroids:
            if not player.is_invulnerable() and asteroid.collides_with(player):
                log_event("player_hit")
                hud.lose_life()
                if hud.is_game_over():
                    print("Game over!")
                    print(f"Final score: {hud.score}")
                    sys.exit()
                player.respawn()
            for shot in shots:
                if shot.collides_with(asteroid):
                    points = asteroid.get_score()
                    log_event("asteroid_shot", score=points)
                    hud.add_score(points)
                    shot.kill()
                    asteroid.split()
                    break
        screen.blit(background, (0, 0))
        for object in drawable:
            object.draw(screen)
        hud.draw(screen)
        pygame.display.flip()
        dt = clock.tick(60) / 1000


if __name__ == "__main__":
    main()
