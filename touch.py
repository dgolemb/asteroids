import sys

import pygame


def neutral_state() -> dict:
    return {
        "available": False,
        "blocked": False,
        "stick_x": 0.0,
        "stick_y": 0.0,
        "tap_serial": 0,
        "tap_x": 0.0,
        "tap_y": 0.0,
    }


def read_window_state() -> dict:
    import platform

    try:
        raw = platform.window.touch_state
        return {
            "available": bool(raw.available),
            "blocked": bool(raw.blocked),
            "stick_x": float(raw.stick_x),
            "stick_y": float(raw.stick_y),
            "tap_serial": int(raw.tap_serial),
            "tap_x": float(raw.tap_x),
            "tap_y": float(raw.tap_y),
        }
    except Exception:
        return neutral_state()


class TouchBridge:
    def __init__(self, read_state):
        self.read_state = read_state
        self.available = False
        self.blocked = False
        self.stick = pygame.Vector2()
        self.tap = None
        self.last_tap_serial = None

    @classmethod
    def create(cls) -> "TouchBridge":
        if sys.platform == "emscripten":
            return cls(read_window_state)
        return cls(neutral_state)

    def poll(self) -> None:
        state = self.read_state()
        self.available = state["available"]
        self.blocked = state["blocked"]
        self.stick = pygame.Vector2(state["stick_x"], state["stick_y"])
        if self.blocked:
            self.stick = pygame.Vector2()
        elif self.stick.length_squared() > 1:
            self.stick.scale_to_length(1)
        self.tap = None
        serial = state["tap_serial"]
        if self.last_tap_serial is not None and serial != self.last_tap_serial:
            self.tap = pygame.Vector2(state["tap_x"], state["tap_y"])
        self.last_tap_serial = serial
