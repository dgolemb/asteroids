import unittest

import pygame

from constants import SCREEN_HEIGHT, SCREEN_WIDTH
from shape import Shape


class WrapPositionTest(unittest.TestCase):
    def test_wraps_both_axes_back_onto_the_screen(self):
        shape = Shape(-1, SCREEN_HEIGHT + 1, 5)
        shape.wrap_position()
        self.assertEqual(shape.position, pygame.Vector2(SCREEN_WIDTH - 1, 1))

    def test_position_inside_the_screen_is_unchanged(self):
        shape = Shape(100, 200, 5)
        shape.wrap_position()
        self.assertEqual(shape.position, pygame.Vector2(100, 200))

    def test_position_on_the_far_edge_wraps_to_zero(self):
        shape = Shape(SCREEN_WIDTH, SCREEN_HEIGHT, 5)
        shape.wrap_position()
        self.assertEqual(shape.position, pygame.Vector2(0, 0))


class WrappedDeltaTest(unittest.TestCase):
    def test_plain_delta_inside_the_screen(self):
        delta = Shape(100, 100, 10).wrapped_delta(Shape(130, 60, 10))
        self.assertEqual(delta, pygame.Vector2(30, -40))

    def test_takes_the_shortest_path_across_the_horizontal_edge(self):
        delta = Shape(5, 100, 10).wrapped_delta(Shape(SCREEN_WIDTH - 5, 100, 10))
        self.assertEqual(delta, pygame.Vector2(-10, 0))

    def test_takes_the_shortest_path_across_the_vertical_edge(self):
        delta = Shape(100, SCREEN_HEIGHT - 5, 10).wrapped_delta(Shape(100, 5, 10))
        self.assertEqual(delta, pygame.Vector2(0, 10))

    def test_is_antisymmetric(self):
        first = Shape(5, 700, 10)
        second = Shape(SCREEN_WIDTH - 20, 10, 10)
        self.assertEqual(first.wrapped_delta(second), -second.wrapped_delta(first))


class GhostOffsetsTest(unittest.TestCase):
    def test_no_ghosts_away_from_the_edges(self):
        self.assertEqual(Shape(640, 360, 10).ghost_offsets(), [pygame.Vector2(0, 0)])

    def test_left_edge_adds_a_ghost_on_the_right(self):
        offsets = Shape(5, 360, 10).ghost_offsets()
        self.assertCountEqual(offsets, [pygame.Vector2(0, 0), pygame.Vector2(SCREEN_WIDTH, 0)])

    def test_right_edge_adds_a_ghost_on_the_left(self):
        offsets = Shape(SCREEN_WIDTH - 5, 360, 10).ghost_offsets()
        self.assertCountEqual(offsets, [pygame.Vector2(0, 0), pygame.Vector2(-SCREEN_WIDTH, 0)])

    def test_top_edge_adds_a_ghost_below(self):
        offsets = Shape(640, 5, 10).ghost_offsets()
        self.assertCountEqual(offsets, [pygame.Vector2(0, 0), pygame.Vector2(0, SCREEN_HEIGHT)])

    def test_bottom_edge_adds_a_ghost_above(self):
        offsets = Shape(640, SCREEN_HEIGHT - 5, 10).ghost_offsets()
        self.assertCountEqual(offsets, [pygame.Vector2(0, 0), pygame.Vector2(0, -SCREEN_HEIGHT)])

    def test_corner_produces_four_copies(self):
        offsets = Shape(2, 2, 10).ghost_offsets()
        self.assertCountEqual(
            offsets,
            [
                pygame.Vector2(0, 0),
                pygame.Vector2(SCREEN_WIDTH, 0),
                pygame.Vector2(0, SCREEN_HEIGHT),
                pygame.Vector2(SCREEN_WIDTH, SCREEN_HEIGHT),
            ],
        )

    def test_extent_overrides_the_radius(self):
        shape = Shape(50, 360, 10)
        self.assertEqual(len(shape.ghost_offsets()), 1)
        self.assertEqual(len(shape.ghost_offsets(60)), 2)

    def test_position_exactly_at_the_extent_has_no_ghost(self):
        self.assertEqual(len(Shape(10, 360, 10).ghost_offsets()), 1)


class MaskTest(unittest.TestCase):
    def test_bounding_radius_defaults_to_the_radius(self):
        self.assertEqual(Shape(0, 0, 12).bounding_radius(), 12)

    def test_mask_is_a_filled_circle_sized_to_the_diameter(self):
        mask = Shape(0, 0, 10).get_mask()
        self.assertEqual(mask.get_size(), (20, 20))
        self.assertGreater(mask.count(), 0)
        self.assertEqual(mask.get_at((10, 10)), 1)
        self.assertEqual(mask.get_at((0, 0)), 0)


class CollidesWithTest(unittest.TestCase):
    def test_overlapping_shapes_collide(self):
        self.assertTrue(Shape(100, 100, 10).collides_with(Shape(115, 100, 10)))

    def test_distant_shapes_do_not_collide(self):
        self.assertFalse(Shape(100, 100, 10).collides_with(Shape(140, 100, 10)))

    def test_collision_is_symmetric(self):
        first = Shape(100, 100, 10)
        second = Shape(115, 105, 10)
        self.assertEqual(first.collides_with(second), second.collides_with(first))

    def test_shapes_collide_across_the_screen_edge(self):
        self.assertTrue(Shape(5, 100, 10).collides_with(Shape(SCREEN_WIDTH - 5, 100, 10)))

    def test_shapes_do_not_collide_across_the_screen_edge_when_far_apart(self):
        self.assertFalse(Shape(5, 100, 10).collides_with(Shape(SCREEN_WIDTH - 60, 100, 10)))

    def test_circles_within_bounding_distance_but_diagonal_do_not_touch(self):
        first = Shape(100, 100, 10)
        second = Shape(100 + 14, 100 + 14, 10)
        self.assertLessEqual(first.wrapped_delta(second).length(), 20)
        self.assertFalse(first.collides_with(second))


if __name__ == "__main__":
    unittest.main()
