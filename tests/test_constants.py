import unittest

import constants as c


class ConstantsConsistencyTest(unittest.TestCase):
    def test_every_asteroid_kind_has_a_score_and_a_name(self):
        kinds = set(range(1, c.ASTEROID_KINDS + 1))
        self.assertEqual(set(c.ASTEROID_SCORES), kinds)
        self.assertEqual(set(c.ASTEROID_KIND_NAMES), kinds)

    def test_smaller_asteroids_are_worth_more_points(self):
        scores = [c.ASTEROID_SCORES[kind] for kind in range(1, c.ASTEROID_KINDS + 1)]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_largest_asteroid_radius_matches_the_kind_count(self):
        self.assertEqual(c.ASTEROID_MAX_RADIUS, c.ASTEROID_MIN_RADIUS * c.ASTEROID_KINDS)

    def test_asteroid_limits_are_ordered(self):
        self.assertLessEqual(c.ASTEROID_START_MAX_COUNT, c.ASTEROID_MAX_COUNT)

    def test_effect_durations_exist_for_every_timed_powerup(self):
        self.assertEqual(set(c.POWERUP_EFFECT_SECONDS), {c.SHIELD_KIND, c.WEAPON_KIND})
        for seconds in c.POWERUP_EFFECT_SECONDS.values():
            self.assertGreater(seconds, 0)

    def test_stackable_kinds_are_known_powerups(self):
        self.assertTrue(c.POWERUP_STACKABLE_KINDS <= set(c.POWERUP_EFFECT_SECONDS))

    def test_powerup_kinds_are_distinct(self):
        kinds = [c.SHIELD_KIND, c.WEAPON_KIND, c.HEART_KIND]
        self.assertEqual(len(set(kinds)), len(kinds))

    def test_extra_beams_unlock_in_order_within_the_level_range(self):
        levels = [level for level, _ in c.WEAPON_EXTRA_BEAMS]
        self.assertEqual(levels, sorted(levels))
        for level in levels:
            self.assertGreaterEqual(level, 1)
            self.assertLessEqual(level, c.WEAPON_MAX_LEVEL)

    def test_lives_are_consistent(self):
        self.assertGreater(c.PLAYER_START_LIVES, 0)
        self.assertGreaterEqual(c.PLAYER_MAX_LIVES, c.PLAYER_START_LIVES)

    def test_spawn_windows_are_ordered(self):
        self.assertLess(c.HEART_SPAWN_MIN_SECONDS, c.HEART_SPAWN_MAX_SECONDS)
        self.assertLess(c.POWERUP_SPAWN_MIN_SECONDS, c.POWERUP_SPAWN_MAX_SECONDS)

    def test_explosion_ranges_are_ordered(self):
        self.assertLessEqual(c.EXPLOSION_PARTICLE_COUNT_MIN, c.EXPLOSION_PARTICLE_COUNT_MAX)
        self.assertLessEqual(c.EXPLOSION_PARTICLE_LIFETIME_MIN_SECONDS, c.EXPLOSION_PARTICLE_LIFETIME_MAX_SECONDS)
        self.assertLessEqual(c.EXPLOSION_PARTICLE_SPEED_MIN, c.EXPLOSION_PARTICLE_SPEED_MAX)

    def test_menu_offers_continue_and_exit(self):
        self.assertEqual(c.MENU_OPTIONS, (c.MENU_OPTION_CONTINUE, c.MENU_OPTION_EXIT))

    def test_thrust_alignment_threshold_is_a_sensible_angle(self):
        self.assertGreater(c.TOUCH_THRUST_ALIGNMENT_DEGREES, 0)
        self.assertLess(c.TOUCH_THRUST_ALIGNMENT_DEGREES, 90)

    def test_shield_covers_the_ship(self):
        self.assertGreater(c.SHIELD_RADIUS, c.PLAYER_RADIUS)


if __name__ == "__main__":
    unittest.main()
