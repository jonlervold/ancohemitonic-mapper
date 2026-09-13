"""Parse and serialize 12 pitch-class root/mode assignments."""

from modes import MODE_BY_NAME
from notes import NOTE_NAME_TO_PC, NOTE_NAMES

SLOT_COUNT = 12
EMPTY_SLOT_LABEL = "(none)"
PRESET_FILE_HEADER = "# Ancohemitonic Mapper mode presets"


def empty_slots():
    return [None] * SLOT_COUNT


def serialize_slots(slots):
    """Return a human-editable text file for assigned slots only."""
    if len(slots) != SLOT_COUNT:
        raise ValueError("Expected %d preset slots" % SLOT_COUNT)
    lines = [PRESET_FILE_HEADER]
    for pitch_class, slot in enumerate(slots):
        if slot is None:
            continue
        root, mode_name = slot
        lines.append("%s: %s %s" % (NOTE_NAMES[pitch_class], root, mode_name))
    return "\n".join(lines) + "\n"


def parse_slots(text):
    """Parse a preset file. Unmentioned keys become empty. Raises ValueError on bad input."""
    slots = empty_slots()
    seen = set()
    for line_no, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            raise ValueError(
                "Line %d: expected 'Key: Root Mode', got %r" % (line_no, raw)
            )
        key_text, rest = line.split(":", 1)
        key = key_text.strip()
        rest = rest.strip()
        if key not in NOTE_NAME_TO_PC:
            raise ValueError("Line %d: unknown key %r" % (line_no, key))
        parts = rest.split()
        if len(parts) != 2:
            raise ValueError(
                "Line %d: expected 'Root Mode' after the key, got %r" % (line_no, rest)
            )
        root, mode_name = parts
        if root not in NOTE_NAME_TO_PC:
            raise ValueError("Line %d: unknown root %r" % (line_no, root))
        if mode_name not in MODE_BY_NAME:
            raise ValueError("Line %d: unknown mode %r" % (line_no, mode_name))
        pitch_class = NOTE_NAME_TO_PC[key]
        if pitch_class in seen:
            raise ValueError("Line %d: duplicate key %r" % (line_no, key))
        seen.add(pitch_class)
        slots[pitch_class] = (root, mode_name)
    return slots
