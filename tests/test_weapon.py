import unittest

from constants import WEAPON_DURATION_SECONDS, WEAPON_KIND, WEAPON_MAX_LEVEL
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
        player.update_effects(WEAPON_DURATION_SECONDS - 1)
        self.assertEqual(player.weapon_level, 2)

    def test_pickup_after_decay_raises_level_and_refreshes_timer(self):
        player = Player(0, 0)
        player.weapon_level = 3
        player.add_effect(WEAPON_KIND, WEAPON_DURATION_SECONDS)
        player.update_effects(WEAPON_DURATION_SECONDS)
        player.update_effects(WEAPON_DURATION_SECONDS - 5)
        player.upgrade_weapon()
        self.assertEqual(player.weapon_level, 3)
        self.assertEqual(player.active_effects[WEAPON_KIND], WEAPON_DURATION_SECONDS)

    def test_hit_keeps_level_and_timer(self):
        player = Player(0, 0)
        player.weapon_level = 3
        player.add_effect(WEAPON_KIND, 12.0)
        player.start_invulnerability()
        self.assertEqual(player.weapon_level, 3)
        self.assertEqual(player.active_effects[WEAPON_KIND], 12.0)
