import unittest

from constants import HEART_KIND, SHIELD_KIND, WEAPON_KIND
from stats import GameStats


class GameStatsTest(unittest.TestCase):
    def test_starts_empty(self):
        stats = GameStats()
        self.assertEqual(stats.asteroids_destroyed, {1: 0, 2: 0, 3: 0})
        self.assertEqual(stats.powerups_collected, {SHIELD_KIND: 0, WEAPON_KIND: 0, HEART_KIND: 0})
        self.assertEqual(stats.play_time, 0.0)
        self.assertEqual(stats.level, 1)

    def test_add_time_accumulates(self):
        stats = GameStats()
        stats.add_time(1.5)
        stats.add_time(2.0)
        self.assertAlmostEqual(stats.play_time, 3.5)

    def test_record_asteroid_counts_per_kind(self):
        stats = GameStats()
        stats.record_asteroid(2)
        stats.record_asteroid(2)
        stats.record_asteroid(3)
        self.assertEqual(stats.asteroids_destroyed, {1: 0, 2: 2, 3: 1})

    def test_record_asteroid_accepts_an_unknown_kind(self):
        stats = GameStats()
        stats.record_asteroid(7)
        self.assertEqual(stats.asteroids_destroyed[7], 1)

    def test_record_powerup_counts_per_kind(self):
        stats = GameStats()
        stats.record_powerup(HEART_KIND)
        stats.record_powerup(HEART_KIND)
        stats.record_powerup(SHIELD_KIND)
        self.assertEqual(stats.powerups_collected, {SHIELD_KIND: 1, WEAPON_KIND: 0, HEART_KIND: 2})

    def test_record_powerup_accepts_an_unknown_kind(self):
        stats = GameStats()
        stats.record_powerup("bomb")
        self.assertEqual(stats.powerups_collected["bomb"], 1)

    def test_level_only_goes_up(self):
        stats = GameStats()
        stats.set_level(4)
        stats.set_level(2)
        self.assertEqual(stats.level, 4)
        stats.set_level(5)
        self.assertEqual(stats.level, 5)

    def test_format_time_pads_minutes_and_seconds(self):
        cases = {0: "00:00", 5: "00:05", 59.9: "00:59", 60: "01:00", 61.9: "01:01", 3725: "62:05"}
        for seconds, expected in cases.items():
            with self.subTest(seconds=seconds):
                stats = GameStats()
                stats.add_time(seconds)
                self.assertEqual(stats.format_time(), expected)

    def test_summary_lines(self):
        stats = GameStats()
        stats.add_time(65)
        stats.set_level(4)
        stats.record_asteroid(1)
        stats.record_asteroid(1)
        stats.record_asteroid(2)
        stats.record_powerup(SHIELD_KIND)
        stats.record_powerup(HEART_KIND)
        stats.record_powerup(HEART_KIND)
        self.assertEqual(
            stats.summary_lines(),
            [
                "Time: 01:05   Level: 4",
                "Asteroids destroyed: small 2, medium 1, large 0",
                "Powerups collected: shield 1, weapon 0, heart 2",
            ],
        )

    def test_summary_falls_back_to_the_kind_number_for_unnamed_asteroids(self):
        stats = GameStats()
        stats.record_asteroid(7)
        self.assertTrue(stats.summary_lines()[1].endswith("large 0, 7 1"))


if __name__ == "__main__":
    unittest.main()
