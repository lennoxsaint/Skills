import tempfile
import unittest
from pathlib import Path

from goal_slug import choose_packet_dir, slugify
from validate_goal_skill import errors


class GoalSkillTests(unittest.TestCase):
    def test_contract_validator_passes(self):
        self.assertEqual(errors(), [])

    def test_slugify_is_bounded_and_plain(self):
        self.assertEqual(slugify("Ship: Mobile / Desktop parity!"), "ship-mobile-desktop-parity")
        self.assertLessEqual(len(slugify("A" * 100)), 64)

    def test_packet_reservation_never_overwrites(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "Workspace With Spaces"
            first = choose_packet_dir(workspace, "Ship Settings", reserve=True)
            second = choose_packet_dir(workspace, "Ship Settings", reserve=True)
            self.assertEqual(first.name, "ship-settings")
            self.assertEqual(second.name, "ship-settings-2")
            self.assertNotEqual(first, second)


if __name__ == "__main__":
    unittest.main()
