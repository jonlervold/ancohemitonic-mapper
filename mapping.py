"""White-key to ancohemitonic-mode note mapping. No MIDI I/O."""

MAJOR_DEGREE_OFFSETS = [0, 2, 4, 5, 7, 9, 11]
WHITE_KEY_DEGREES = {
    0: 0,  # C -> degree 1
    2: 1,  # D -> degree 2
    4: 2,  # E -> degree 3
    5: 3,  # F -> degree 4
    7: 4,  # G -> degree 5
    9: 5,  # A -> degree 6
    11: 6,  # B -> degree 7
}


def mode_offsets_from_formula(formula):
    """Chromatic offsets from C for each of the seven degrees."""
    return [MAJOR_DEGREE_OFFSETS[i] + formula[i] for i in range(7)]


def build_white_key_mapping(root_pc, mode_offsets):
    """Map white-key pitch class -> offset from the input octave base."""
    return {
        pitch_class: root_pc + mode_offsets[degree]
        for pitch_class, degree in WHITE_KEY_DEGREES.items()
    }


def transform_note(input_note, root_pc, mode_offsets):
    """
    Map a physical MIDI note to the selected mode.

    Returns None for black keys. Out-of-range results are returned as-is;
    the caller decides whether to send them.
    """
    degree = WHITE_KEY_DEGREES.get(input_note % 12)
    if degree is None:
        return None
    return (input_note // 12) * 12 + root_pc + mode_offsets[degree]


def transform_note_with_mapping(input_note, white_key_mapping):
    """Lookup using a precomputed white-key mapping dict. None for black keys."""
    offset = white_key_mapping.get(input_note % 12)
    if offset is None:
        return None
    return (input_note // 12) * 12 + offset
