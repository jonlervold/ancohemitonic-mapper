import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mapping import (
    MAJOR_DEGREE_OFFSETS,
    mode_offsets_from_formula,
    transform_note,
)
from modes import (
    DORIAN_LABEL,
    IONIAN_LABEL,
    LYDIAN_LABEL,
    formula_for_label,
    formula_to_display,
)
from notes import midi_to_name, parse_root

C4 = 60
CS4 = 61
D4 = 62
E4 = 64
F4 = 65
G4 = 67
A4 = 69
B4 = 71
C5 = 72
D9 = 122


def offsets(mode_label):
    return mode_offsets_from_formula(formula_for_label(mode_label))


class TransformNoteTests(unittest.TestCase):
    def test_c_ionian(self):
        ionian = offsets(IONIAN_LABEL)
        self.assertEqual(ionian, MAJOR_DEGREE_OFFSETS)
        root = parse_root("C")
        self.assertEqual(transform_note(C4, root, ionian), C4)
        self.assertEqual(transform_note(D4, root, ionian), D4)
        self.assertEqual(transform_note(B4, root, ionian), B4)

    def test_d_dorian(self):
        dorian = offsets(DORIAN_LABEL)
        self.assertEqual(dorian, [0, 2, 3, 5, 7, 9, 10])
        root = parse_root("D")
        self.assertEqual(transform_note(C4, root, dorian), D4)
        self.assertEqual(transform_note(D4, root, dorian), E4)
        self.assertEqual(transform_note(E4, root, dorian), F4)
        self.assertEqual(transform_note(B4, root, dorian), C5)

    def test_f_lydian(self):
        lydian = offsets(LYDIAN_LABEL)
        self.assertEqual(lydian, [0, 2, 4, 6, 7, 9, 11])
        root = parse_root("F")
        self.assertEqual(transform_note(C4, root, lydian), F4)
        self.assertEqual(transform_note(F4, root, lydian), B4)
        self.assertEqual(transform_note(B4, root, lydian), 76)  # E5

    def test_g_ionian_octave_wrap(self):
        ionian = offsets(IONIAN_LABEL)
        root = parse_root("G")
        self.assertEqual(transform_note(C4, root, ionian), G4)
        self.assertEqual(transform_note(E4, root, ionian), B4)
        self.assertEqual(transform_note(F4, root, ionian), C5)
        self.assertEqual(transform_note(B4, root, ionian), 78)  # F#/Gb5
        self.assertEqual(transform_note(C5, root, ionian), 79)  # G5

    def test_black_keys_are_none(self):
        ionian = offsets(IONIAN_LABEL)
        root = parse_root("C")
        self.assertIsNone(transform_note(CS4, root, ionian))
        self.assertIsNone(transform_note(63, root, ionian))  # D#/Eb4
        self.assertIsNone(transform_note(66, root, ionian))  # F#/Gb4

    def test_out_of_range_is_returned_not_clamped(self):
        ionian = offsets(IONIAN_LABEL)
        root = parse_root("G")
        result = transform_note(D9, root, ionian)
        self.assertEqual(result, 129)
        self.assertGreater(result, 127)


class NoteNameTests(unittest.TestCase):
    def test_combined_names(self):
        self.assertEqual(midi_to_name(C4), "C4")
        self.assertEqual(midi_to_name(CS4), "C#/Db4")
        self.assertEqual(midi_to_name(78), "F#/Gb5")
        self.assertEqual(midi_to_name(64), "E4")

    def test_out_of_range_name(self):
        self.assertIsNone(midi_to_name(-1))
        self.assertIsNone(midi_to_name(128))


class ModeDatabaseTests(unittest.TestCase):
    def test_default_ionian_formula(self):
        self.assertEqual(formula_for_label(IONIAN_LABEL), (0, 0, 0, 0, 0, 0, 0))

    def test_all_formulas_have_seven_entries(self):
        from modes import FLATTENED_MODES

        self.assertEqual(len(FLATTENED_MODES), 42)
        for mode in FLATTENED_MODES:
            self.assertEqual(len(mode["formula"]), 7)

    def test_malformed_formula_fails_clearly(self):
        from modes import _validate_modes

        with self.assertRaises(ValueError):
            _validate_modes(
                [
                    {
                        "parentScaleName": "Broken",
                        "modes": [{"modeName": "Short", "formula": [0, 0, 0]}],
                    }
                ]
            )


class FormulaDisplayTests(unittest.TestCase):
    def test_jontools_style_readouts(self):
        self.assertEqual(formula_to_display([0, 0, 0, 0, 0, 0, 0]), "1 2 3 4 5 6 7")
        self.assertEqual(
            formula_to_display([0, 0, 0, 1, 0, 0, -1]),
            "1 2 3 #4 5 6 b7",
        )
        self.assertEqual(
            formula_to_display([0, -1, -1, -1, -1, -1, -2]),
            "1 b2 b3 b4 b5 b6 bb7",
        )
        self.assertEqual(
            formula_to_display([0, 0, -1, 0, -1, 0, -1]),
            "1 2 b3 4 b5 6 b7",
        )
        self.assertEqual(
            formula_to_display([0, -1, -1, -1, -1, -2, -2]),
            "1 b2 b3 b4 b5 bb6 bb7",
        )

    def test_dropdown_labels_include_formula(self):
        from modes import MODE_BY_LABEL

        self.assertIn("Melodic Minor - Lydian Dominant - 1 2 3 #4 5 6 b7", MODE_BY_LABEL)
        self.assertIn("Harmonic Minor - Ultralocrian - 1 b2 b3 b4 b5 b6 bb7", MODE_BY_LABEL)
        self.assertIn(
            "Hungarian Major - Ultralocrian Double-Flat 6 - 1 b2 b3 b4 b5 bb6 bb7",
            MODE_BY_LABEL,
        )
        self.assertIn(IONIAN_LABEL, MODE_BY_LABEL)


if __name__ == "__main__":
    unittest.main()
