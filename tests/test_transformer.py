import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

try:
    import rtmidi  # noqa: F401
except ImportError:
    sys.modules["rtmidi"] = MagicMock()

from transformer import (
    CC_ALL_NOTES_OFF,
    PREFERRED_OUTPUT_NAMES,
    STATUS_CC,
    STATUS_CHANNEL_PRESSURE,
    STATUS_NOTE_OFF,
    STATUS_NOTE_ON,
    STATUS_PITCH_BEND,
    STATUS_POLY_AT,
    STATUS_PROGRAM,
    MidiTransformer,
)
from modes import DORIAN_LABEL, IONIAN_LABEL

C4 = 60
CS4 = 61
D4 = 62
E4 = 64
F4 = 65
G4 = 67
B4 = 71
C5 = 72
D9 = 122


class FakeMidiOut:
    def __init__(self):
        self.sent = []

    def send_message(self, message):
        self.sent.append(list(message))


class FakeWindow:
    def __init__(self):
        self.events = []

    def write_event_value(self, key, value):
        self.events.append((key, value))


def make_transformer():
    window = FakeWindow()
    transformer = MidiTransformer(window)
    transformer.midi_out = FakeMidiOut()
    return transformer, window


class MidiTransformerTests(unittest.TestCase):
    def test_default_output_prefers_entonal_iac(self):
        transformer = MidiTransformer(FakeWindow())
        ports = ["Other Output", PREFERRED_OUTPUT_NAMES[0], "IAC Driver Bus 1"]
        self.assertEqual(transformer.default_output(ports), PREFERRED_OUTPUT_NAMES[0])

    def test_selected_output_explicitly_uses_coremidi(self):
        fake_rtmidi = MagicMock()
        fake_rtmidi.API_UNSPECIFIED = 0
        fake_rtmidi.API_MACOSX_CORE = 1
        fake_rtmidi.get_compiled_api.return_value = [1]
        fake_rtmidi.get_api_display_name.return_value = "Core MIDI"
        fake_rtmidi.get_api_name.return_value = "MACOSX_CORE"

        midi_out = MagicMock()
        midi_out.get_current_api.return_value = 1
        midi_out.is_port_open.return_value = True
        midi_out.get_ports.return_value = ["Other Output", "IAC Driver Entonal Out"]
        fake_rtmidi.MidiOut.return_value = midi_out

        with (
            patch("transformer.rtmidi", fake_rtmidi),
            patch("transformer.sys.platform", "darwin"),
        ):
            transformer = MidiTransformer(FakeWindow())
            transformer.ensure_midi_out("IAC Driver Entonal Out")

        fake_rtmidi.MidiOut.assert_called_once_with(
            rtapi=1,
            name="Ancohemitonic Mapper",
        )
        midi_out.open_port.assert_called_once_with(1)
        self.assertIs(transformer.midi_out, midi_out)
        self.assertEqual(transformer.output_port_name, "IAC Driver Entonal Out")

    def test_missing_coremidi_backend_fails_clearly(self):
        fake_rtmidi = MagicMock()
        fake_rtmidi.API_UNSPECIFIED = 0
        fake_rtmidi.API_MACOSX_CORE = 1
        fake_rtmidi.get_compiled_api.return_value = [3]
        fake_rtmidi.get_api_display_name.return_value = "JACK"
        fake_rtmidi.get_api_name.return_value = "UNIX_JACK"

        with (
            patch("transformer.rtmidi", fake_rtmidi),
            patch("transformer.sys.platform", "darwin"),
        ):
            transformer = MidiTransformer(FakeWindow())
            with self.assertRaisesRegex(RuntimeError, "without CoreMIDI support"):
                transformer.ensure_midi_out("IAC Driver Entonal Out")

        fake_rtmidi.MidiOut.assert_not_called()

    def test_missing_selected_output_fails_with_available_destinations(self):
        fake_rtmidi = MagicMock()
        fake_rtmidi.API_UNSPECIFIED = 0
        midi_out = MagicMock()
        midi_out.get_current_api.return_value = 0
        midi_out.get_ports.return_value = ["Other Output"]
        fake_rtmidi.MidiOut.return_value = midi_out

        with (
            patch("transformer.rtmidi", fake_rtmidi),
            patch("transformer.sys.platform", "win32"),
        ):
            transformer = MidiTransformer(FakeWindow())
            with self.assertRaisesRegex(RuntimeError, "Missing Output"):
                transformer.ensure_midi_out("Missing Output")

        midi_out.open_port.assert_not_called()

    def test_c_ionian_note_on_preserves_velocity_and_channel(self):
        transformer, _window = make_transformer()
        transformer.set_root("C")
        transformer.set_mode(IONIAN_LABEL)
        transformer.handle_message([STATUS_NOTE_ON | 2, C4, 100])
        self.assertEqual(transformer.midi_out.sent, [[STATUS_NOTE_ON | 2, C4, 100]])

    def test_d_dorian_mapping(self):
        transformer, window = make_transformer()
        transformer.set_root("D")
        transformer.set_mode(DORIAN_LABEL)
        transformer.handle_message([STATUS_NOTE_ON, C4, 90])
        transformer.handle_message([STATUS_NOTE_ON, E4, 91])
        transformer.handle_message([STATUS_NOTE_ON, B4, 92])
        self.assertEqual(
            transformer.midi_out.sent,
            [
                [STATUS_NOTE_ON, D4, 90],
                [STATUS_NOTE_ON, F4, 91],
                [STATUS_NOTE_ON, C5, 92],
            ],
        )
        self.assertEqual(window.events[-1], ("-NOTE-", ("B4", "C5")))

    def test_black_key_is_discarded(self):
        transformer, window = make_transformer()
        transformer.handle_message([STATUS_NOTE_ON, CS4, 100])
        transformer.handle_message([STATUS_NOTE_OFF, CS4, 0])
        self.assertEqual(transformer.midi_out.sent, [])
        self.assertEqual(window.events, [])

    def test_note_on_velocity_zero_is_note_off(self):
        transformer, _window = make_transformer()
        transformer.handle_message([STATUS_NOTE_ON, C4, 80])
        transformer.handle_message([STATUS_NOTE_ON, C4, 0])
        self.assertEqual(
            transformer.midi_out.sent,
            [
                [STATUS_NOTE_ON, C4, 80],
                [STATUS_NOTE_OFF, C4, 0],
            ],
        )
        self.assertEqual(transformer.active_notes, {})

    def test_force_output_channel_for_notes_and_cc(self):
        transformer, _window = make_transformer()
        transformer.force_channel = True
        transformer.channel = 3
        transformer.handle_message([STATUS_NOTE_ON | 1, C4, 70])
        transformer.handle_message([STATUS_CC | 1, 64, 127])
        transformer.handle_message([STATUS_NOTE_OFF | 1, C4, 40])
        self.assertEqual(
            transformer.midi_out.sent,
            [
                [STATUS_NOTE_ON | 2, C4, 70],
                [STATUS_CC | 2, 64, 127],
                [STATUS_NOTE_OFF | 2, C4, 0],
            ],
        )

    def test_pass_through_non_note_messages(self):
        transformer, _window = make_transformer()
        messages = [
            [STATUS_CC, 64, 127],
            [STATUS_CC, 1, 10],
            [STATUS_PITCH_BEND, 0, 64],
            [STATUS_CHANNEL_PRESSURE, 40],
            [STATUS_POLY_AT, C4, 20],
            [STATUS_PROGRAM, 12],
        ]
        for message in messages:
            transformer.handle_message(message)
        self.assertEqual(transformer.midi_out.sent, messages)

    def test_held_note_off_uses_original_mapping_after_mode_change(self):
        transformer, _window = make_transformer()
        transformer.set_root("C")
        transformer.set_mode(IONIAN_LABEL)
        transformer.handle_message([STATUS_NOTE_ON, C4, 100])
        transformer.set_root("D")
        transformer.set_mode(DORIAN_LABEL)
        transformer.handle_message([STATUS_NOTE_OFF, C4, 0])
        self.assertEqual(
            transformer.midi_out.sent,
            [
                [STATUS_NOTE_ON, C4, 100],
                [STATUS_NOTE_OFF, C4, 0],
            ],
        )
        transformer.handle_message([STATUS_NOTE_ON, C4, 100])
        self.assertEqual(transformer.midi_out.sent[-1], [STATUS_NOTE_ON, D4, 100])

    def test_panic_sends_note_off_and_clears_active_notes(self):
        transformer, _window = make_transformer()
        transformer.handle_message([STATUS_NOTE_ON | 1, C4, 100])
        transformer.handle_message([STATUS_NOTE_ON, G4, 80])
        transformer.midi_out.sent.clear()
        transformer.panic()
        self.assertEqual(transformer.active_notes, {})
        note_offs = [msg for msg in transformer.midi_out.sent if (msg[0] & 0xF0) == STATUS_NOTE_OFF]
        self.assertEqual(
            sorted(note_offs),
            sorted(
                [
                    [STATUS_NOTE_OFF | 1, C4, 0],
                    [STATUS_NOTE_OFF, G4, 0],
                ]
            ),
        )
        cc123 = [msg for msg in transformer.midi_out.sent if msg[1] == CC_ALL_NOTES_OFF]
        self.assertIn([STATUS_CC | 1, CC_ALL_NOTES_OFF, 0], cc123)
        self.assertIn([STATUS_CC, CC_ALL_NOTES_OFF, 0], cc123)

    def test_out_of_range_output_is_discarded(self):
        transformer, window = make_transformer()
        transformer.set_root("G")
        transformer.set_mode(IONIAN_LABEL)
        transformer.handle_message([STATUS_NOTE_ON, D9, 100])
        self.assertEqual(transformer.midi_out.sent, [])
        self.assertEqual(transformer.active_notes, {})
        self.assertEqual(window.events, [])

    def test_g_ionian_example(self):
        transformer, _window = make_transformer()
        transformer.set_root("G")
        transformer.set_mode(IONIAN_LABEL)
        transformer.handle_message([STATUS_NOTE_ON, C4, 50])
        transformer.handle_message([STATUS_NOTE_ON, F4, 50])
        transformer.handle_message([STATUS_NOTE_ON, B4, 50])
        self.assertEqual(
            transformer.midi_out.sent,
            [
                [STATUS_NOTE_ON, G4, 50],
                [STATUS_NOTE_ON, C5, 50],
                [STATUS_NOTE_ON, 78, 50],  # F#/Gb5
            ],
        )

    def test_malformed_message_does_not_raise(self):
        transformer, _window = make_transformer()
        transformer.handle_message([])
        transformer.handle_message([STATUS_NOTE_ON])
        transformer.handle_message([0xF0, 1, 2])
        self.assertEqual(transformer.midi_out.sent, [])


if __name__ == "__main__":
    unittest.main()
