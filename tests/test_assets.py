import os
import unittest
from pathlib import Path

import pygame

import constants

ROOT = Path(__file__).resolve().parent.parent
PATH_CONSTANTS = {name: getattr(constants, name) for name in dir(constants) if name.endswith("_PATH")}


class AssetPathsTest(unittest.TestCase):
    def test_there_are_path_constants_to_check(self):
        self.assertGreaterEqual(len(PATH_CONSTANTS), 8)

    def test_every_path_constant_points_to_an_existing_file(self):
        for name, value in PATH_CONSTANTS.items():
            with self.subTest(constant=name):
                self.assertTrue((ROOT / value).is_file(), value)

    def test_file_names_match_case_exactly(self):
        for name, value in PATH_CONSTANTS.items():
            with self.subTest(constant=name):
                self.assertIn(Path(value).name, os.listdir((ROOT / value).parent))

    def test_every_texture_loads_with_a_positive_size(self):
        for name, value in PATH_CONSTANTS.items():
            with self.subTest(constant=name):
                width, height = pygame.image.load(str(ROOT / value)).get_size()
                self.assertGreater(width, 0)
                self.assertGreater(height, 0)

    def test_paths_are_relative_to_the_project_root(self):
        for name, value in PATH_CONSTANTS.items():
            with self.subTest(constant=name):
                self.assertFalse(os.path.isabs(value))


if __name__ == "__main__":
    unittest.main()
