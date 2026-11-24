import unittest

from constants import SHIELD_KIND, WEAPON_DURATION_SECONDS, WEAPON_KIND, WEAPON_MAX_LEVEL
from player import Player


class WeaponDecayTest(unittest.TestCase):
    def test_expiry_lowers_level_by_one_and_restarts_timer(self):
        player = Player(0, 0)
        player.weapon_level = 3
        player.add_effect(WEAPON_KIND, WEAPON_DURATION_SECONDS)
        player.update_effects(WEAPON_DURATION_SECONDS)
        self.assertEqual(player.weapon_level, 2)
        self.assertEqual(player.active_effects[WEAPON_KIND], WEAPON_DURATION_SECONDS)

    def test_expiry_at_level_one_removes_effect(self):
        player = Player(0, 0)
        player.upgrade_weapon()
        player.update_effects(WEAPON_DURATION_SECONDS)
        self.assertEqual(player.weapon_level, 0)
        self.assertFalse(player.has_effect(WEAPON_KIND))

    def test_level_decays_step_by_step_to_zero(self):
        player = Player(0, 0)
        player.weapon_level = WEAPON_MAX_LEVEL
        player.add_effect(WEAPON_KIND, WEAPON_DURATION_SECONDS)
        for expected in range(WEAPON_MAX_LEVEL - 1, -1, -1):
            player.update_effects(WEAPON_DURATION_SECONDS)
            self.assertEqual(player.weapon_level, expected)
        self.assertFalse(player.has_effect(WEAPON_KIND))

    def test_partial_time_does_not_lower_level(self):
        player = Player(0, 0)
        player.weapon_level = 2
        player.add_effect(WEAPON_KIND, WEAPON_DURATION_SECONDS)
        player.update_effects(WEAPON_DURATION_SECONDS - 0.5)
        self.assertEqual(player.weapon_level, 2)
        self.assertAlmostEqual(player.active_effects[WEAPON_KIND], 0.5)

    def test_level_drops_on_the_frame_the_timer_reaches_zero(self):
        player = Player(0, 0)
        player.weapon_level = 2
        player.add_effect(WEAPON_KIND, WEAPON_DURATION_SECONDS)
        player.update_effects(WEAPON_DURATION_SECONDS - 0.5)
        player.update_effects(0.5)
        self.assertEqual(player.weapon_level, 1)

    def test_a_long_frame_lowers_the_level_only_once(self):
        player = Player(0, 0)
        player.weapon_level = 3
        player.add_effect(WEAPON_KIND, WEAPON_DURATION_SECONDS)
        player.update_effects(WEAPON_DURATION_SECONDS * 5)
        self.assertEqual(player.weapon_level, 2)

    def test_decay_leaves_other_effects_alone(self):
        player = Player(0, 0)
        player.weapon_level = 1
        player.add_effect(WEAPON_KIND, 1)
        player.add_effect(SHIELD_KIND, 10)
        player.update_effects(2)
        self.assertEqual(player.weapon_level, 0)
        self.assertAlmostEqual(player.active_effects[SHIELD_KIND], 8)

    def test_effect_without_a_weapon_level_does_not_go_below_zero(self):
        player = Player(0, 0)
        player.add_effect(WEAPON_KIND, 1)
        player.update_effects(2)
        self.assertEqual(player.weapon_level, 0)
        self.assertFalse(player.has_effect(WEAPON_KIND))


class WeaponUpgradeTest(unittest.TestCase):
    def test_first_pickup_gives_level_one_and_a_full_timer(self):
        player = Player(0, 0)
        player.upgrade_weapon()
        self.assertEqual(player.weapon_level, 1)
        self.assertEqual(player.active_effects[WEAPON_KIND], WEAPON_DURATION_SECONDS)
        self.assertTrue(player.has_effect(WEAPON_KIND))

    def test_every_pickup_raises_the_level_by_one(self):
        player = Player(0, 0)
        levels = []
        for _ in range(WEAPON_MAX_LEVEL):
            player.upgrade_weapon()
            levels.append(player.weapon_level)
        self.assertEqual(levels, list(range(1, WEAPON_MAX_LEVEL + 1)))

    def test_level_is_capped_at_the_maximum(self):
        player = Player(0, 0)
        for _ in range(WEAPON_MAX_LEVEL + 3):
            player.upgrade_weapon()
        self.assertEqual(player.weapon_level, WEAPON_MAX_LEVEL)

    def test_pickup_at_the_maximum_still_refreshes_the_timer(self):
        player = Player(0, 0)
        player.weapon_level = WEAPON_MAX_LEVEL
        player.add_effect(WEAPON_KIND, 3)
        player.upgrade_weapon()
        self.assertEqual(player.weapon_level, WEAPON_MAX_LEVEL)
        self.assertEqual(player.active_effects[WEAPON_KIND], WEAPON_DURATION_SECONDS)

    def test_pickup_in_the_middle_of_the_timer_refreshes_it(self):
        player = Player(0, 0)
        player.upgrade_weapon()
        player.update_effects(WEAPON_DURATION_SECONDS - 0.5)
        player.upgrade_weapon()
        self.assertEqual(player.weapon_level, 2)
        self.assertEqual(player.active_effects[WEAPON_KIND], WEAPON_DURATION_SECONDS)

    def test_fresh_player_has_no_weapon_upgrade(self):
        player = Player(0, 0)
        self.assertEqual(player.weapon_level, 0)
        self.assertFalse(player.has_effect(WEAPON_KIND))

    def test_pickup_after_decay_raises_level_and_refreshes_timer(self):
        player = Player(0, 0)
        player.weapon_level = 3
        player.add_effect(WEAPON_KIND, WEAPON_DURATION_SECONDS)
        player.update_effects(WEAPON_DURATION_SECONDS)
        player.update_effects(WEAPON_DURATION_SECONDS - 5)
        player.upgrade_weapon()
        self.assertEqual(player.weapon_level, 3)
        self.assertEqual(player.active_effects[WEAPON_KIND], WEAPON_DURATION_SECONDS)


class WeaponAfterHitTest(unittest.TestCase):
    def test_hit_keeps_level_and_timer(self):
        player = Player(0, 0)
        player.weapon_level = 3
        player.add_effect(WEAPON_KIND, 12.0)
        player.start_invulnerability()
        self.assertEqual(player.weapon_level, 3)
        self.assertEqual(player.active_effects[WEAPON_KIND], 12.0)

    def test_weapon_keeps_decaying_during_invulnerability(self):
        player = Player(0, 0)
        player.weapon_level = 2
        player.add_effect(WEAPON_KIND, 1.0)
        player.start_invulnerability()
        player.update_effects(1.0)
        self.assertEqual(player.weapon_level, 1)


if __name__ == "__main__":
    unittest.main()
