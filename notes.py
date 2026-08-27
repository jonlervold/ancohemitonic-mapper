"""Root names and MIDI note display using combined enharmonic spellings."""

NOTE_NAMES = [
    "C",
    "C#/Db",
    "D",
    "D#/Eb",
    "E",
    "F",
    "F#/Gb",
    "G",
    "G#/Ab",
    "A",
    "A#/Bb",
    "B",
]

NOTE_NAME_TO_PC = {name: index for index, name in enumerate(NOTE_NAMES)}
DEFAULT_ROOT = "C"


def parse_root(name):
    """Return pitch class 0-11 for a root dropdown name."""
    try:
        return NOTE_NAME_TO_PC[name]
    except KeyError:
        raise ValueError("Unknown root: %s" % name)


def midi_to_name(note):
    """Return combined-name plus octave, e.g. C4 or C#/Db4. MIDI 60 is C4."""
    if note < 0 or note > 127:
        return None
    pitch_class = note % 12
    octave = (note // 12) - 1
    return "%s%s" % (NOTE_NAMES[pitch_class], octave)
