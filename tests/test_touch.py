import sys
import types
import unittest
from unittest import mock

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

    def test_short_stick_is_left_untouched(self):
        bridge = TouchBridge(ScriptedReader(state(stick_x=0.3, stick_y=-0.4)))
        bridge.poll()
        self.assertAlmostEqual(bridge.stick.x, 0.3)
        self.assertAlmostEqual(bridge.stick.y, -0.4)

    def test_stick_of_exactly_unit_length_is_left_untouched(self):
        bridge = TouchBridge(ScriptedReader(state(stick_x=-1.0, stick_y=0.0)))
        bridge.poll()
        self.assertEqual(bridge.stick, pygame.Vector2(-1, 0))

    def test_stick_just_over_unit_length_is_clamped(self):
        bridge = TouchBridge(ScriptedReader(state(stick_x=1.01, stick_y=0.0)))
        bridge.poll()
        self.assertAlmostEqual(bridge.stick.x, 1.0)

    def test_blocked_still_reports_taps(self):
        bridge = TouchBridge(
            ScriptedReader(
                state(tap_serial=0),
                state(blocked=True, tap_serial=1, tap_x=5.0, tap_y=6.0),
            )
        )
        bridge.poll()
        bridge.poll()
        self.assertEqual(bridge.tap, pygame.Vector2(5, 6))

    def test_tap_serial_that_goes_down_still_counts_as_a_new_tap(self):
        bridge = TouchBridge(
            ScriptedReader(
                state(tap_serial=5),
                state(tap_serial=1, tap_x=7.0, tap_y=8.0),
            )
        )
        bridge.poll()
        bridge.poll()
        self.assertEqual(bridge.tap, pygame.Vector2(7, 8))

    def test_stick_is_replaced_on_every_poll(self):
        bridge = TouchBridge(
            ScriptedReader(state(stick_x=1.0, stick_y=0.0), state(stick_x=0.0, stick_y=0.0))
        )
        bridge.poll()
        bridge.poll()
        self.assertEqual(bridge.stick, pygame.Vector2())


class BridgeCreationTest(unittest.TestCase):
    def test_desktop_bridge_reads_the_neutral_state(self):
        with mock.patch.object(sys, "platform", "darwin"):
            bridge = TouchBridge.create()
        self.assertIs(bridge.read_state, neutral_state)

    def test_browser_bridge_reads_the_window_state(self):
        with mock.patch.object(sys, "platform", "emscripten"):
            bridge = TouchBridge.create()
        self.assertIs(bridge.read_state, read_window_state)

    def test_desktop_bridge_polls_without_input(self):
        with mock.patch.object(sys, "platform", "linux"):
            bridge = TouchBridge.create()
        bridge.poll()
        self.assertFalse(bridge.available)
        self.assertFalse(bridge.blocked)
        self.assertEqual(bridge.stick, pygame.Vector2())
        self.assertIsNone(bridge.tap)


def fake_platform(**touch_state):
    return types.SimpleNamespace(window=types.SimpleNamespace(touch_state=types.SimpleNamespace(**touch_state)))


def browser_state(**overrides):
    values = dict(available=1, blocked=0, stick_x="0.5", stick_y="-0.25", tap_serial="4", tap_x="1", tap_y="2")
    values.update(overrides)
    return values


class WindowReaderTest(unittest.TestCase):
    def read_with(self, **overrides):
        with mock.patch.dict(sys.modules, {"platform": fake_platform(**browser_state(**overrides))}):
            return read_window_state()

    def test_without_a_browser_the_state_is_neutral(self):
        with mock.patch.dict(sys.modules, {"platform": types.SimpleNamespace()}):
            self.assertEqual(read_window_state(), neutral_state())

    def test_browser_values_are_converted_to_python_types(self):
        self.assertEqual(
            self.read_with(),
            {
                "available": True,
                "blocked": False,
                "stick_x": 0.5,
                "stick_y": -0.25,
                "tap_serial": 4,
                "tap_x": 1.0,
                "tap_y": 2.0,
            },
        )

    def test_every_field_is_read_from_its_own_key(self):
        state_read = self.read_with(
            available=0, blocked=1, stick_x=0.1, stick_y=0.2, tap_serial=3, tap_x=30.0, tap_y=40.0
        )
        self.assertEqual(
            state_read,
            {
                "available": False,
                "blocked": True,
                "stick_x": 0.1,
                "stick_y": 0.2,
                "tap_serial": 3,
                "tap_x": 30.0,
                "tap_y": 40.0,
            },
        )

    def test_numeric_fields_are_real_numbers(self):
        result = self.read_with()
        for key in ("stick_x", "stick_y", "tap_x", "tap_y"):
            self.assertIsInstance(result[key], float)
        self.assertIsInstance(result["tap_serial"], int)

    def test_garbled_value_falls_back_to_the_neutral_state(self):
        self.assertEqual(self.read_with(stick_x="not a number"), neutral_state())

    def test_missing_field_falls_back_to_the_neutral_state(self):
        incomplete = browser_state()
        del incomplete["tap_y"]
        with mock.patch.dict(sys.modules, {"platform": fake_platform(**incomplete)}):
            self.assertEqual(read_window_state(), neutral_state())

    def test_bridge_polls_the_browser_state_end_to_end(self):
        bridge = TouchBridge(read_window_state)
        with mock.patch.dict(sys.modules, {"platform": fake_platform(**browser_state(tap_serial=0))}):
            bridge.poll()
        with mock.patch.dict(sys.modules, {"platform": fake_platform(**browser_state(tap_serial=1, tap_x=9, tap_y=8))}):
            bridge.poll()
        self.assertTrue(bridge.available)
        self.assertAlmostEqual(bridge.stick.x, 0.5)
        self.assertAlmostEqual(bridge.stick.y, -0.25)
        self.assertEqual(bridge.tap, pygame.Vector2(9, 8))


if __name__ == "__main__":
    unittest.main()
