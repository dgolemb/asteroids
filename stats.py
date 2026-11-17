from constants import ASTEROID_KINDS, ASTEROID_KIND_NAMES, SHIELD_KIND, WEAPON_KIND, HEART_KIND


class GameStats:
    def __init__(self) -> None:
        self.asteroids_destroyed = {kind: 0 for kind in range(1, ASTEROID_KINDS + 1)}
        self.powerups_collected = {SHIELD_KIND: 0, WEAPON_KIND: 0, HEART_KIND: 0}
        self.play_time = 0.0
        self.level = 1

    def add_time(self, dt: float) -> None:
        self.play_time += dt

    def record_asteroid(self, kind: int) -> None:
        self.asteroids_destroyed[kind] = self.asteroids_destroyed.get(kind, 0) + 1

    def record_powerup(self, kind: str) -> None:
        self.powerups_collected[kind] = self.powerups_collected.get(kind, 0) + 1

    def set_level(self, level: int) -> None:
        self.level = max(self.level, level)

    def format_time(self) -> str:
        total_seconds = int(self.play_time)
        return f"{total_seconds // 60:02d}:{total_seconds % 60:02d}"

    def summary_lines(self) -> list[str]:
        asteroids = ", ".join(
            f"{ASTEROID_KIND_NAMES.get(kind, kind)} {count}"
            for kind, count in sorted(self.asteroids_destroyed.items())
        )
        powerups = ", ".join(f"{kind} {count}" for kind, count in self.powerups_collected.items())
        return [
            f"Time: {self.format_time()}   Level: {self.level}",
            f"Asteroids destroyed: {asteroids}",
            f"Powerups collected: {powerups}",
        ]
