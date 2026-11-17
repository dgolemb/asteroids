import asyncio
import pygame
from constants import *
from logger import log_state, log_event
from player import Player
from asteroid import Asteroid
from asteroidfield import AsteroidField
from shot import Shot
from hud import Hud
from menu import Menu, GameState
from explosion import ExplosionParticle
from powerup import Powerup
from powerupspawner import PowerupSpawner
from stats import GameStats
from touch import TouchBridge


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


def destroy_asteroid(asteroid, asteroid_field, hud, stats, source):
    points = round(asteroid.get_score() * asteroid_field.score_multiplier())
    log_event(source, score=points)
    hud.add_score(points)
    stats.record_asteroid(round(asteroid.radius / ASTEROID_MIN_RADIUS))
    asteroid.split()


def shield_hits(player, asteroid):
    return player.wrapped_delta(asteroid).length() <= SHIELD_RADIUS + asteroid.radius


def apply_powerup(powerup, player, hud, stats):
    log_event("powerup_picked", kind=powerup.kind)
    stats.record_powerup(powerup.kind)
    if powerup.kind == WEAPON_KIND:
        player.upgrade_weapon()
    elif powerup.kind == HEART_KIND:
        hud.collect_heart()
    else:
        player.add_effect(powerup.kind, POWERUP_EFFECT_SECONDS[powerup.kind])
    powerup.kill()


def resolve_collisions(player, powerups, asteroids, shots, asteroid_field, hud, stats):
    for powerup in powerups:
        if powerup.collides_with(player):
            apply_powerup(powerup, player, hud, stats)
    for asteroid in asteroids:
        if player.shield_active() and shield_hits(player, asteroid):
            destroy_asteroid(asteroid, asteroid_field, hud, stats, "asteroid_shielded")
            continue
        if not player.is_invulnerable() and asteroid.collides_with(player):
            log_event("player_hit")
            hud.lose_life()
            if hud.is_game_over():
                return True
            player.start_invulnerability()
        for shot in shots:
            if shot.collides_with(asteroid):
                shot.kill()
                destroy_asteroid(asteroid, asteroid_field, hud, stats, "asteroid_shot")
                break
    return False


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
    stats = GameStats()
    return updatable, drawable, asteroids, shots, powerups, player, asteroid_field, hud, stats


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
    Shot.textures = [
        load_sprite(SHOT_TEXTURE_PATH, SHOT_TEXTURE_SCALE * (1 + WEAPON_SHOT_SCALE_PER_LEVEL * level))
        for level in range(WEAPON_MAX_LEVEL + 1)
    ]
    Powerup.textures[SHIELD_KIND] = load_pixel_sprite(POWERUP_SHIELD_TEXTURE_PATH, POWERUP_TEXTURE_SCALE)
    Powerup.textures[WEAPON_KIND] = load_pixel_sprite(POWERUP_WEAPON_TEXTURE_PATH, POWERUP_TEXTURE_SCALE)
    Powerup.textures[HEART_KIND] = load_pixel_sprite(HEART_TEXTURE_PATH, POWERUP_TEXTURE_SCALE)
    Hud.heart_full = load_pixel_sprite(HEART_TEXTURE_PATH, HUD_HEART_SCALE)
    Hud.heart_empty = load_pixel_sprite(HEART_EMPTY_TEXTURE_PATH, HUD_HEART_SCALE)

    updatable, drawable, asteroids, shots, powerups, player, asteroid_field, hud, stats = new_game()

    menu = Menu()
    bridge = TouchBridge.create()
    Player.touch = bridge
    state = GameState.MENU
    final_score = 0

    while True:
        log_state()
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                if state in (GameState.PLAYING, GameState.PAUSED):
                    print("\n".join(stats.summary_lines()))
                return
        pressed_keys = [event.key for event in events if event.type == pygame.KEYDOWN]

        bridge.poll()
        menu.touch_mode = bridge.available
        if bridge.tap is not None:
            if state in (GameState.MENU, GameState.GAME_OVER):
                pressed_keys.append(pygame.K_RETURN)
            elif state == GameState.PLAYING and menu.is_pause_button_hit(bridge.tap):
                pressed_keys.append(pygame.K_ESCAPE)
            elif state == GameState.PAUSED:
                option_index = menu.pause_option_at(bridge.tap)
                if option_index is not None:
                    menu.set_selection(option_index)
                    pressed_keys.append(pygame.K_RETURN)
        if bridge.blocked and state == GameState.PLAYING:
            menu.reset_selection()
            state = GameState.PAUSED

        if state == GameState.MENU:
            menu.update(dt)
            if pygame.K_ESCAPE in pressed_keys:
                return
            if pygame.K_RETURN in pressed_keys:
                updatable, drawable, asteroids, shots, powerups, player, asteroid_field, hud, stats = new_game()
                state = GameState.PLAYING
        elif state == GameState.GAME_OVER:
            if pygame.K_RETURN in pressed_keys:
                menu.reset_blink()
                state = GameState.MENU
        elif state == GameState.PAUSED:
            if pygame.K_ESCAPE in pressed_keys:
                state = GameState.PLAYING
            else:
                if pygame.K_w in pressed_keys:
                    menu.move_selection(-1)
                if pygame.K_s in pressed_keys:
                    menu.move_selection(1)
                if pygame.K_RETURN in pressed_keys:
                    if menu.selected_option() == MENU_OPTION_CONTINUE:
                        state = GameState.PLAYING
                    else:
                        final_score = hud.score
                        state = GameState.GAME_OVER
        elif pygame.K_ESCAPE in pressed_keys:
            menu.reset_selection()
            state = GameState.PAUSED
        else:
            updatable.update(dt)
            hud.level = asteroid_field.level
            stats.add_time(dt)
            stats.set_level(asteroid_field.level)
            if resolve_collisions(player, powerups, asteroids, shots, asteroid_field, hud, stats):
                final_score = hud.score
                state = GameState.GAME_OVER

        screen.blit(background, (0, 0))
        if state == GameState.MENU:
            menu.draw_title_screen(screen)
        elif state == GameState.GAME_OVER:
            menu.draw_game_over(screen, final_score, stats.summary_lines())
        else:
            for powerup in powerups:
                powerup.draw(screen)
            for object in drawable:
                object.draw(screen)
            player.draw_shield(screen)
            hud.draw(screen)
            if bridge.available and state == GameState.PLAYING:
                menu.draw_pause_button(screen)
            if state == GameState.PAUSED:
                menu.draw_pause_menu(screen)
        pygame.display.flip()
        dt = clock.tick(60) / 1000
        await asyncio.sleep(0)


if __name__ == "__main__":
    asyncio.run(main())
