"""Ancohemitonic mode database ported from jontools ValidModes.tsx."""

# Authoritative copy of ancohemitonicModes from jontools/frontend/src/types/ValidModes.tsx
ANCOHEMITONIC_MODES = [
    {
        "parentScaleName": "Diatonic",
        "modes": [
            {"modeName": "Ionian/Major", "formula": [0, 0, 0, 0, 0, 0, 0]},
            {"modeName": "Dorian", "formula": [0, 0, -1, 0, 0, 0, -1]},
            {"modeName": "Phrygian", "formula": [0, -1, -1, 0, 0, -1, -1]},
            {"modeName": "Lydian", "formula": [0, 0, 0, 1, 0, 0, 0]},
            {"modeName": "Mixolydian", "formula": [0, 0, 0, 0, 0, 0, -1]},
            {"modeName": "Aeolian/Minor", "formula": [0, 0, -1, 0, 0, -1, -1]},
            {"modeName": "Locrian", "formula": [0, -1, -1, 0, -1, -1, -1]},
        ],
    },
    {
        "parentScaleName": "Melodic Minor",
        "modes": [
            {"modeName": "Melodic Minor", "formula": [0, 0, -1, 0, 0, 0, 0]},
            {"modeName": "Dorian Flat 2", "formula": [0, -1, -1, 0, 0, 0, -1]},
            {"modeName": "Lydian Augmented", "formula": [0, 0, 0, 1, 1, 0, 0]},
            {"modeName": "Lydian Dominant", "formula": [0, 0, 0, 1, 0, 0, -1]},
            {"modeName": "Mixolydian Flat 6", "formula": [0, 0, 0, 0, 0, -1, -1]},
            {"modeName": "Locrian Natural 2", "formula": [0, 0, 0, 0, -1, -1, -1]},
            {"modeName": "Altered Dominant", "formula": [0, -1, -1, -1, -1, -1, -1]},
        ],
    },
    {
        "parentScaleName": "Harmonic Minor",
        "modes": [
            {"modeName": "Harmonic Minor", "formula": [0, 0, -1, 0, 0, -1, 0]},
            {"modeName": "Locrian Natural 6", "formula": [0, -1, -1, 0, -1, 0, -1]},
            {"modeName": "Ionian Augmented", "formula": [0, 0, 0, 0, 1, 0, 0]},
            {"modeName": "Dorian Sharp 4", "formula": [0, 0, -1, 1, 0, 0, -1]},
            {"modeName": "Phrygian Dominant", "formula": [0, -1, 0, 0, 0, -1, -1]},
            {"modeName": "Lydian Sharp 2", "formula": [0, 1, 0, 1, 0, 0, 0]},
            {"modeName": "Ultralocrian", "formula": [0, -1, -1, -1, -1, -1, -2]},
        ],
    },
    {
        "parentScaleName": "Harmonic Major",
        "modes": [
            {"modeName": "Harmonic Major", "formula": [0, 0, 0, 0, 0, -1, 0]},
            {
                "modeName": "Locrian Natural 2, Natural 6",
                "formula": [0, 0, -1, 0, -1, 0, -1],
            },
            {"modeName": "Phrygian Flat 4", "formula": [0, -1, -1, -1, 0, -1, -1]},
            {
                "modeName": "Melodic Minor Sharp 4",
                "formula": [0, 0, -1, 1, 0, 0, 0],
            },
            {"modeName": "Mixolydian Flat 2", "formula": [0, -1, 0, 0, 0, 0, -1]},
            {
                "modeName": "Lydian Augmented Sharp 2",
                "formula": [0, 1, 0, 1, 1, 0, 0],
            },
            {
                "modeName": "Locrian Double-Flat 7",
                "formula": [0, -1, -1, 0, -1, -1, -2],
            },
        ],
    },
    {
        "parentScaleName": "Hungarian Major",
        "modes": [
            {"modeName": "Hungarian Major", "formula": [0, 1, 0, 1, 0, 0, -1]},
            {
                "modeName": "Ultralocrian Double-Flat 6",
                "formula": [0, -1, -1, -1, -1, -2, -2],
            },
            {
                "modeName": "Harmonic Minor Flat 5",
                "formula": [0, 0, -1, 0, -1, -1, 0],
            },
            {
                "modeName": "Altered Dominant Natural 6",
                "formula": [0, -1, -1, -1, -1, 0, -1],
            },
            {
                "modeName": "Melodic Minor Augmented",
                "formula": [0, 0, -1, 0, 1, 0, 0],
            },
            {
                "modeName": "Dorian Flat 2, Sharp 4",
                "formula": [0, -1, -1, 1, 0, 0, -1],
            },
            {
                "modeName": "Lydian Augmented Sharp 3",
                "formula": [0, 0, 1, 1, 1, 0, 0],
            },
        ],
    },
    {
        "parentScaleName": "Involution of Hungarian Major",
        "modes": [
            {
                "modeName": "Involution of Hungarian Major",
                "formula": [0, -1, 0, 1, 0, 0, -1],
            },
            {
                "modeName": "Lydian Augmented Sharp 2, Sharp 3",
                "formula": [0, 1, 1, 1, 1, 0, 0],
            },
            {
                "modeName": "Locrian Natural 2, Double-Flat 7",
                "formula": [0, 0, -1, 0, -1, -1, -2],
            },
            {
                "modeName": "Altered Double-Flat 6",
                "formula": [0, -1, -1, -1, -1, -2, -1],
            },
            {
                "modeName": "Melodic Minor Flat 5",
                "formula": [0, 0, -1, 0, -1, 0, 0],
            },
            {
                "modeName": "Phrygian Flat 4, Natural 6",
                "formula": [0, -1, -1, -1, 0, 0, -1],
            },
            {
                "modeName": "Melodic Minor Augmented Sharp 4",
                "formula": [0, 0, -1, 1, 1, 0, 0],
            },
        ],
    },
]


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _validate_modes(groups):
    for group in groups:
        parent = group["parentScaleName"]
        for mode in group["modes"]:
            name = mode["modeName"]
            formula = mode["formula"]
            if not isinstance(formula, (list, tuple)) or len(formula) != 7:
                raise ValueError(
                    "Mode %s - %s must have exactly 7 formula entries, got %r"
                    % (parent, name, formula)
                )
            if not all(_is_int(entry) for entry in formula):
                raise ValueError(
                    "Mode %s - %s formula must contain only integers, got %r"
                    % (parent, name, formula)
                )


def adjustment_to_accidentals(adjustment):
    """Port of jontools transformNoteAdjustmentToFlatsAndSharps."""
    if adjustment < 0:
        return "b" * (-adjustment)
    if adjustment > 0:
        return "#" * adjustment
    return ""


def formula_to_display(formula):
    """Port of jontools transformFormulaToFlatsAndSharps. [0, -1, ...] -> '1 b2 ...'."""
    parts = []
    for index, adjustment in enumerate(formula, start=1):
        parts.append("%s%d" % (adjustment_to_accidentals(adjustment), index))
    return " ".join(parts)


def _flatten(groups):
    flattened = []
    by_label = {}
    for group in groups:
        parent = group["parentScaleName"]
        for mode in group["modes"]:
            label = "%s - %s - %s" % (
                parent,
                mode["modeName"],
                formula_to_display(mode["formula"]),
            )
            entry = {
                "label": label,
                "parentScaleName": parent,
                "modeName": mode["modeName"],
                "formula": tuple(mode["formula"]),
            }
            flattened.append(entry)
            by_label[label] = entry
    return flattened, by_label


_validate_modes(ANCOHEMITONIC_MODES)
FLATTENED_MODES, MODE_BY_LABEL = _flatten(ANCOHEMITONIC_MODES)
MODE_LABELS = [mode["label"] for mode in FLATTENED_MODES]
DEFAULT_MODE_LABEL = "Diatonic - Ionian/Major - 1 2 3 4 5 6 7"
IONIAN_LABEL = DEFAULT_MODE_LABEL
DORIAN_LABEL = "Diatonic - Dorian - 1 2 b3 4 5 6 b7"
LYDIAN_LABEL = "Diatonic - Lydian - 1 2 3 #4 5 6 7"


def formula_for_label(label):
    try:
        return MODE_BY_LABEL[label]["formula"]
    except KeyError:
        raise ValueError("Unknown mode: %s" % label)
