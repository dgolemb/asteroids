import unittest

import pygame

from touch import TouchBridge, neutral_state, read_window_state


class ScriptedReader:
    def __init__(self, *states):
        self.states = list(states)

    def __call__(self):
        if len(self.states) > 1:
            return self.states.pop(0)
        return self.states[0]


def state(**overrides):
    result = neutral_state()
    result.update(overrides)
    return result


class TouchBridgeTest(unittest.TestCase):
    def test_neutral_state_has_no_input(self):
        bridge = TouchBridge(neutral_state)
        bridge.poll()
        self.assertFalse(bridge.available)
        self.assertFalse(bridge.blocked)
        self.assertEqual(bridge.stick, pygame.Vector2())
        self.assertIsNone(bridge.tap)

    def test_available_and_stick_are_read(self):
        bridge = TouchBridge(ScriptedReader(state(available=True, stick_x=0.5, stick_y=-0.25)))
        bridge.poll()
        self.assertTrue(bridge.available)
        self.assertAlmostEqual(bridge.stick.x, 0.5)
        self.assertAlmostEqual(bridge.stick.y, -0.25)

    def test_stick_longer_than_one_is_clamped(self):
        bridge = TouchBridge(ScriptedReader(state(stick_x=3.0, stick_y=4.0)))
        bridge.poll()
        self.assertAlmostEqual(bridge.stick.length(), 1.0)
        self.assertAlmostEqual(bridge.stick.x, 0.6)
        self.assertAlmostEqual(bridge.stick.y, 0.8)

    def test_blocked_zeroes_the_stick(self):
        bridge = TouchBridge(ScriptedReader(state(blocked=True, stick_x=1.0, stick_y=0.0)))
        bridge.poll()
        self.assertTrue(bridge.blocked)
        self.assertEqual(bridge.stick, pygame.Vector2())

    def test_stale_tap_before_first_poll_is_ignored(self):
        bridge = TouchBridge(ScriptedReader(state(tap_serial=7, tap_x=100.0, tap_y=200.0)))
        bridge.poll()
        self.assertIsNone(bridge.tap)

    def test_new_tap_is_reported_once(self):
        bridge = TouchBridge(
            ScriptedReader(
                state(tap_serial=0),
                state(tap_serial=1, tap_x=640.0, tap_y=360.0),
                state(tap_serial=1, tap_x=640.0, tap_y=360.0),
            )
        )
        bridge.poll()
        self.assertIsNone(bridge.tap)
        bridge.poll()
        self.assertEqual(bridge.tap, pygame.Vector2(640, 360))
        bridge.poll()
        self.assertIsNone(bridge.tap)

    def test_several_taps_between_polls_report_the_latest_position(self):
        bridge = TouchBridge(
            ScriptedReader(
                state(tap_serial=0),
                state(tap_serial=3, tap_x=10.0, tap_y=20.0),
            )
        )
        bridge.poll()
        bridge.poll()
        self.assertEqual(bridge.tap, pygame.Vector2(10, 20))

    def test_create_on_desktop_reads_neutral_state(self):
        bridge = TouchBridge.create()
        bridge.poll()
        self.assertFalse(bridge.available)
        self.assertIsNone(bridge.tap)

    def test_window_reader_without_browser_returns_neutral_state(self):
        self.assertEqual(read_window_state(), neutral_state())


if __name__ == "__main__":
    unittest.main()
