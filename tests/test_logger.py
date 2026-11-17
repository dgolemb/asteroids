import json
import re
import unittest
from unittest import mock

import pygame

import logger
from shape import Shape


def snapshot_with_groups(group_size=2):
    screen = pygame.Surface((100, 50))
    asteroids = pygame.sprite.Group(*[Shape(10 + index, 20, 5) for index in range(group_size)])
    logger.log_state()
    return screen, asteroids


def snapshot_with_a_lone_sprite():
    player = Shape(1.234, 5.678, 3)
    logger.log_state()
    return player


class LoggerTestCase(unittest.TestCase):
    def setUp(self):
        self.enterContext(mock.patch.object(logger, "_event_log_initialized", False))
        self.enterContext(mock.patch.object(logger, "_state_log_initialized", False))
        self.enterContext(mock.patch.object(logger, "_frame_count", 0))
        self.open = self.enterContext(mock.patch("logger.open", mock.mock_open(), create=True))

    def written(self):
        return [json.loads(call.args[0]) for call in self.open.return_value.write.call_args_list]


class LogEventTest(LoggerTestCase):
    def test_writes_one_json_line_per_event(self):
        logger.log_event("asteroid_split")
        logger.log_event("level_up", level=2)
        raw = [call.args[0] for call in self.open.return_value.write.call_args_list]
        self.assertTrue(all(line.endswith("\n") for line in raw))
        self.assertEqual([json.loads(line)["type"] for line in raw], ["asteroid_split", "level_up"])

    def test_details_are_merged_into_the_entry(self):
        logger.log_event("player_hit", score=250, lives=2)
        entry = self.written()[0]
        self.assertEqual(entry["type"], "player_hit")
        self.assertEqual(entry["score"], 250)
        self.assertEqual(entry["lives"], 2)

    def test_entry_has_timestamp_elapsed_and_frame(self):
        with mock.patch.object(logger, "_frame_count", 42):
            logger.log_event("tick")
        entry = self.written()[0]
        self.assertEqual(entry["frame"], 42)
        self.assertRegex(entry["timestamp"], r"^\d{2}:\d{2}:\d{2}\.\d{3}$")
        self.assertIsInstance(entry["elapsed_s"], int)
        self.assertGreaterEqual(entry["elapsed_s"], 0)

    def test_first_event_truncates_the_file_and_later_ones_append(self):
        logger.log_event("first")
        logger.log_event("second")
        logger.log_event("third")
        self.assertEqual(
            self.open.call_args_list,
            [
                mock.call("game_events.jsonl", "w"),
                mock.call("game_events.jsonl", "a"),
                mock.call("game_events.jsonl", "a"),
            ],
        )


class LogStateTest(LoggerTestCase):
    def test_writes_only_about_once_per_second(self):
        for _ in range(59):
            snapshot_with_groups()
        self.open.assert_not_called()
        snapshot_with_groups()
        self.open.assert_called_once_with("game_state.jsonl", "w")
        self.assertEqual(self.written()[0]["frame"], 60)

    def test_later_snapshots_append(self):
        for _ in range(120):
            snapshot_with_groups()
        self.assertEqual(
            self.open.call_args_list,
            [mock.call("game_state.jsonl", "w"), mock.call("game_state.jsonl", "a")],
        )

    def test_stops_logging_after_the_time_limit(self):
        with mock.patch.object(logger, "_frame_count", 961):
            snapshot_with_groups()
            self.assertEqual(logger._frame_count, 961)
        self.open.assert_not_called()

    def test_still_counts_frames_at_the_limit(self):
        with mock.patch.object(logger, "_frame_count", 960):
            snapshot_with_groups()
            self.assertEqual(logger._frame_count, 961)
        self.open.assert_not_called()

    def test_snapshot_describes_screen_and_sprite_groups(self):
        with mock.patch.object(logger, "_frame_count", 59):
            snapshot_with_groups()
        entry = self.written()[0]
        self.assertEqual(entry["screen_size"], [100, 50])
        self.assertEqual(entry["asteroids"]["count"], 2)
        self.assertEqual(
            entry["asteroids"]["sprites"][0],
            {"type": "Shape", "pos": [10.0, 20.0], "vel": [0.0, 0.0], "rad": 5},
        )

    def test_group_sample_is_limited_but_count_is_complete(self):
        with mock.patch.object(logger, "_frame_count", 59):
            snapshot_with_groups(group_size=15)
        group = self.written()[0]["asteroids"]
        self.assertEqual(group["count"], 15)
        self.assertEqual(len(group["sprites"]), 10)

    def test_lone_sprite_is_logged_when_there_are_no_groups(self):
        with mock.patch.object(logger, "_frame_count", 59):
            snapshot_with_a_lone_sprite()
        entry = self.written()[0]
        self.assertEqual(entry["player"], {"type": "Shape", "pos": [1.23, 5.68], "vel": [0.0, 0.0], "rad": 3})

    def test_timestamp_format(self):
        with mock.patch.object(logger, "_frame_count", 59):
            snapshot_with_groups()
        self.assertTrue(re.match(r"^\d{2}:\d{2}:\d{2}\.\d{3}$", self.written()[0]["timestamp"]))


if __name__ == "__main__":
    unittest.main()
