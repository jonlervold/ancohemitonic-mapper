import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from presets import empty_slots, parse_slots, serialize_slots
from notes import NOTE_NAMES


SAMPLE = """# Ancohemitonic Mapper mode presets
C: D MM-1
C#/Db: F Hu+3
D: E D0
"""


class PresetFileTests(unittest.TestCase):
    def test_round_trip(self):
        slots = parse_slots(SAMPLE)
        self.assertEqual(slots[0], ("D", "MM-1"))
        self.assertEqual(slots[1], ("F", "Hu+3"))
        self.assertEqual(slots[2], ("E", "D0"))
        self.assertIsNone(slots[3])
        self.assertEqual(parse_slots(serialize_slots(slots)), slots)

    def test_comments_and_blanks_are_ignored(self):
        text = """
# heading

C: D MM-1

# another comment
B: C D+2
"""
        slots = parse_slots(text)
        self.assertEqual(slots[0], ("D", "MM-1"))
        self.assertEqual(slots[11], ("C", "D+2"))
        self.assertTrue(all(slots[i] is None for i in range(1, 11)))

    def test_unmentioned_keys_are_empty(self):
        slots = parse_slots("G: A Hm0\n")
        self.assertEqual(len(slots), 12)
        self.assertEqual(slots[NOTE_NAMES.index("G")], ("A", "Hm0"))
        self.assertEqual(sum(slot is not None for slot in slots), 1)

    def test_unused_slots_omitted_on_export(self):
        slots = empty_slots()
        slots[0] = ("D", "MM-1")
        text = serialize_slots(slots)
        self.assertIn("C: D MM-1", text)
        self.assertNotIn("C#/Db:", text)
        self.assertTrue(text.startswith("# Ancohemitonic Mapper mode presets\n"))

    def test_replace_all_on_import(self):
        first = parse_slots("C: D MM-1\nE: F D+2\n")
        self.assertEqual(first[0], ("D", "MM-1"))
        self.assertEqual(first[4], ("F", "D+2"))
        second = parse_slots("D: E D0\n")
        self.assertIsNone(second[0])
        self.assertIsNone(second[4])
        self.assertEqual(second[2], ("E", "D0"))

    def test_invalid_line_fails(self):
        with self.assertRaisesRegex(ValueError, "Line 1"):
            parse_slots("not a preset line")

    def test_unknown_key_fails(self):
        with self.assertRaisesRegex(ValueError, "unknown key"):
            parse_slots("H: C D+2")

    def test_unknown_root_fails(self):
        with self.assertRaisesRegex(ValueError, "unknown root"):
            parse_slots("C: H D+2")

    def test_unknown_mode_fails(self):
        with self.assertRaisesRegex(ValueError, "unknown mode"):
            parse_slots("C: D Hu+4")

    def test_missing_mode_fails(self):
        with self.assertRaisesRegex(ValueError, "Root Mode"):
            parse_slots("C: D")

    def test_duplicate_key_fails(self):
        with self.assertRaisesRegex(ValueError, "duplicate key"):
            parse_slots("C: D MM-1\nC: E D0\n")


if __name__ == "__main__":
    unittest.main()
