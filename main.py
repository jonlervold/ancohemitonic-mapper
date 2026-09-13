#!/usr/bin/env python3
"""Ancohemitonic Mapper: remap C-major white keys to a selected 7-note mode."""

import logging
import os
import sys

import PySimpleGUI as sg
import rtmidi  # noqa: F401  # load CoreMIDI the same way EWI Breath Filter does

from modes import DEFAULT_MODE_LABEL, MODE_LABELS, MODE_NAMES
from notes import DEFAULT_ROOT, NOTE_NAMES
from presets import EMPTY_SLOT_LABEL, SLOT_COUNT, empty_slots, parse_slots, serialize_slots
from transformer import MidiTransformer, log_midi_environment

APP_NAME = "Ancohemitonic Mapper"

LOG_DIR = os.path.join(os.path.expanduser("~"), "Library", "Logs")
LOG_PATH = os.path.join(LOG_DIR, "Ancohemitonic Mapper.log")

PRESET_FILE_TYPES = (("Text Files", "*.txt"), ("All Files", "*.*"))


def setup_logging():
    os.makedirs(LOG_DIR, exist_ok=True)
    handlers = [logging.StreamHandler(sys.stderr)]
    try:
        handlers.append(logging.FileHandler(LOG_PATH, encoding="utf-8"))
    except OSError:
        pass
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=handlers,
    )


def refresh_devices(window, transformer):
    inputs = transformer.list_inputs()
    outputs = transformer.list_outputs()
    logging.info("Detected MIDI inputs: %s", inputs)
    logging.info("Detected MIDI outputs: %s", outputs)

    current_in = window["-DEVICE-"].get()
    if current_in in inputs:
        selected_in = current_in
    else:
        selected_in = transformer.default_input(inputs) or ""
    window["-DEVICE-"].update(values=inputs, value=selected_in)

    current_out = window["-OUTPUT-"].get()
    if current_out in outputs:
        selected_out = current_out
    else:
        selected_out = transformer.default_output(outputs) or ""
    window["-OUTPUT-"].update(values=outputs, value=selected_out)

    current_control = window["-CONTROL-DEVICE-"].get()
    if current_control in inputs:
        selected_control = current_control
    else:
        selected_control = ""
    window["-CONTROL-DEVICE-"].update(values=inputs, value=selected_control)
    return inputs, outputs


def set_running_ui(window, running):
    window["-DEVICE-"].update(disabled=running)
    window["-OUTPUT-"].update(disabled=running)
    window["-REFRESH-"].update(disabled=running)
    window["-ASSIGN-MODES-"].update(disabled=running)
    window["-CONTROL-DEVICE-"].update(disabled=running)
    window["-START-"].update(disabled=running)
    window["-STOP-"].update(disabled=not running)


def parse_channel(value):
    try:
        channel = int(value)
    except (TypeError, ValueError):
        channel = 1
    return min(16, max(1, channel))


def apply_live_settings(window, transformer, values):
    transformer.force_channel = bool(values["-FORCE-"])
    transformer.channel = parse_channel(values["-CHANNEL-"])
    try:
        transformer.set_root(values["-ROOT-"])
    except ValueError as exc:
        window["-STATUS-"].update(str(exc))
        return False
    try:
        transformer.set_mode(values["-MODE-"])
    except ValueError as exc:
        window["-STATUS-"].update(str(exc))
        return False
    return True


def set_assign_section_visible(window, visible):
    window["-MODE-KB-SECTION-"].update(visible=visible)
    window.refresh()


def preset_root_key(pitch_class):
    return "-PRESET-ROOT-%d-" % pitch_class


def preset_mode_key(pitch_class):
    return "-PRESET-MODE-%d-" % pitch_class


def is_preset_slot_event(event):
    return isinstance(event, str) and (
        event.startswith("-PRESET-ROOT-") or event.startswith("-PRESET-MODE-")
    )


def slots_from_assign_window(assign_window):
    slots = empty_slots()
    for pitch_class in range(SLOT_COUNT):
        root = assign_window[preset_root_key(pitch_class)].get()
        mode_name = assign_window[preset_mode_key(pitch_class)].get()
        if root in (None, "", EMPTY_SLOT_LABEL):
            continue
        if mode_name in (None, "", EMPTY_SLOT_LABEL):
            continue
        slots[pitch_class] = (root, mode_name)
    return slots


def fill_assign_window(assign_window, slots):
    for pitch_class in range(SLOT_COUNT):
        slot = slots[pitch_class]
        root = slot[0] if slot else EMPTY_SLOT_LABEL
        mode_name = slot[1] if slot else EMPTY_SLOT_LABEL
        assign_window[preset_root_key(pitch_class)].update(value=root)
        assign_window[preset_mode_key(pitch_class)].update(value=mode_name)


def sync_slots_from_assign_window(assign_window, transformer, status_window):
    try:
        transformer.set_preset_slots(slots_from_assign_window(assign_window))
    except ValueError as exc:
        status_window["-STATUS-"].update(str(exc))
        return False
    return True


def build_assign_layout(slots):
    header = [
        sg.Text("Key", size=(8, 1)),
        sg.Text("Root", size=(12, 1)),
        sg.Text("Mode", size=(12, 1)),
    ]
    rows = [header]
    root_values = [EMPTY_SLOT_LABEL] + list(NOTE_NAMES)
    mode_values = [EMPTY_SLOT_LABEL] + list(MODE_NAMES)
    for pitch_class, name in enumerate(NOTE_NAMES):
        slot = slots[pitch_class] if slots else None
        root_val = slot[0] if slot else EMPTY_SLOT_LABEL
        mode_val = slot[1] if slot else EMPTY_SLOT_LABEL
        rows.append(
            [
                sg.Text(name, size=(8, 1)),
                sg.Combo(
                    root_values,
                    default_value=root_val,
                    key=preset_root_key(pitch_class),
                    size=(12, 1),
                    readonly=True,
                    enable_events=True,
                ),
                sg.Combo(
                    mode_values,
                    default_value=mode_val,
                    key=preset_mode_key(pitch_class),
                    size=(12, 1),
                    readonly=True,
                    enable_events=True,
                ),
            ]
        )
    rows.append(
        [
            sg.Button("Import...", key="-IMPORT-PRESETS-"),
            sg.Button("Export...", key="-EXPORT-PRESETS-"),
        ]
    )
    return rows


def open_assign_window(transformer):
    return sg.Window(
        "Key assignments",
        build_assign_layout(transformer.preset_slots),
        finalize=True,
        disable_minimize=True,
    )


def import_presets(transformer, assign_window, status_window):
    filename = sg.popup_get_file(
        "Import mode presets",
        file_types=PRESET_FILE_TYPES,
        no_window=True,
    )
    if not filename:
        return
    try:
        with open(filename, "r", encoding="utf-8") as handle:
            text = handle.read()
        slots = parse_slots(text)
        transformer.set_preset_slots(slots)
    except (OSError, ValueError) as exc:
        status_window["-STATUS-"].update(str(exc))
        return
    if assign_window is not None:
        fill_assign_window(assign_window, transformer.preset_slots)
    status_window["-STATUS-"].update("Imported %s" % filename)


def export_presets(transformer, assign_window, status_window):
    if assign_window is not None:
        if not sync_slots_from_assign_window(assign_window, transformer, status_window):
            return
    filename = sg.popup_get_file(
        "Export mode presets",
        save_as=True,
        default_extension=".txt",
        file_types=PRESET_FILE_TYPES,
        no_window=True,
    )
    if not filename:
        return
    try:
        with open(filename, "w", encoding="utf-8") as handle:
            handle.write(serialize_slots(transformer.preset_slots))
    except OSError as exc:
        status_window["-STATUS-"].update(str(exc))
        return
    status_window["-STATUS-"].update("Exported %s" % filename)


def build_layout():
    mode_keyboard_section = [
        [sg.Text("Mode keyboard")],
        [
            sg.Combo(
                [],
                default_value="",
                key="-CONTROL-DEVICE-",
                size=(52, 1),
                readonly=True,
            )
        ],
        [sg.Button("Edit key assignments...", key="-EDIT-ASSIGNMENTS-")],
    ]
    return [
        [sg.Text(APP_NAME, font=("Helvetica", 16))],
        [sg.Text("MIDI Input")],
        [
            sg.Combo(
                [],
                default_value="",
                key="-DEVICE-",
                size=(52, 1),
                readonly=True,
            ),
            sg.Button("Refresh", key="-REFRESH-"),
        ],
        [sg.Text("MIDI Output")],
        [
            sg.Combo(
                [],
                default_value="",
                key="-OUTPUT-",
                size=(52, 1),
                readonly=True,
            )
        ],
        [
            sg.Checkbox(
                "Assign modes to second keyboard",
                key="-ASSIGN-MODES-",
                enable_events=True,
            )
        ],
        [
            sg.pin(
                sg.Column(
                    mode_keyboard_section,
                    key="-MODE-KB-SECTION-",
                    visible=False,
                    pad=(0, 0),
                )
            )
        ],
        [sg.Text("Root")],
        [
            sg.Combo(
                NOTE_NAMES,
                default_value=DEFAULT_ROOT,
                key="-ROOT-",
                size=(52, 1),
                readonly=True,
                enable_events=True,
            )
        ],
        [sg.Text("Mode")],
        [
            sg.Combo(
                MODE_LABELS,
                default_value=DEFAULT_MODE_LABEL,
                key="-MODE-",
                size=(80, 1),
                readonly=True,
                enable_events=True,
            )
        ],
        [
            sg.Checkbox(
                "Force output channel:",
                key="-FORCE-",
                enable_events=True,
            ),
            sg.Combo(
                [str(i) for i in range(1, 17)],
                default_value="1",
                key="-CHANNEL-",
                size=(4, 1),
                readonly=True,
                enable_events=True,
            ),
        ],
        [sg.Text("Input:"), sg.Text("-", key="-INPUT-NOTE-", size=(12, 1))],
        [sg.Text("Output:"), sg.Text("-", key="-OUTPUT-NOTE-", size=(12, 1))],
        [
            sg.Button("Start", key="-START-"),
            sg.Button("Stop", key="-STOP-", disabled=True),
            sg.Button("Panic", key="-PANIC-"),
        ],
        [sg.Text("Status:"), sg.Text("Stopped", key="-STATUS-", size=(50, 1))],
    ]


def main():
    setup_logging()
    logging.info("Application startup")
    logging.info("Log file: %s", LOG_PATH)
    log_midi_environment()

    window = sg.Window(APP_NAME, build_layout(), finalize=True)
    transformer = MidiTransformer(window)
    assign_window = None
    _, outputs = refresh_devices(window, transformer)
    if outputs:
        window["-STATUS-"].update("Stopped")
    else:
        window["-STATUS-"].update("No MIDI output devices found.")
        window["-START-"].update(disabled=True)

    def close_assign_window():
        nonlocal assign_window
        if assign_window is None:
            return
        assign_window.close()
        assign_window = None

    while True:
        event_window, event, values = sg.read_all_windows()
        if event in (sg.WIN_CLOSED, None):
            if event_window is assign_window:
                close_assign_window()
                continue
            break

        if event_window is assign_window:
            if is_preset_slot_event(event):
                sync_slots_from_assign_window(assign_window, transformer, window)
            elif event == "-IMPORT-PRESETS-":
                import_presets(transformer, assign_window, window)
            elif event == "-EXPORT-PRESETS-":
                export_presets(transformer, assign_window, window)
            continue

        if event in ("-FORCE-", "-CHANNEL-", "-ROOT-", "-MODE-"):
            apply_live_settings(window, transformer, values)
        elif event == "-ASSIGN-MODES-":
            enabled = bool(values["-ASSIGN-MODES-"])
            set_assign_section_visible(window, enabled)
            if not enabled:
                close_assign_window()
        elif event == "-EDIT-ASSIGNMENTS-":
            if assign_window is None:
                assign_window = open_assign_window(transformer)
            else:
                try:
                    assign_window.bring_to_front()
                except Exception:
                    assign_window.TKroot.lift()
        elif event == "-REFRESH-":
            refresh_devices(window, transformer)
        elif event == "-START-":
            input_port = values["-DEVICE-"]
            output_port = values["-OUTPUT-"]
            if not input_port:
                window["-STATUS-"].update("No MIDI input device selected.")
                continue
            if not output_port:
                window["-STATUS-"].update("No MIDI output device selected.")
                continue
            control_port = None
            if values["-ASSIGN-MODES-"]:
                control_port = values["-CONTROL-DEVICE-"]
                if not control_port:
                    window["-STATUS-"].update("No mode keyboard selected.")
                    continue
                if control_port == input_port:
                    window["-STATUS-"].update(
                        "Mode keyboard must be a different device."
                    )
                    continue
            if not apply_live_settings(window, transformer, values):
                continue
            try:
                transformer.start(input_port, output_port, control_port)
            except Exception as exc:
                logging.exception("Failed to start")
                window["-STATUS-"].update(str(exc))
                continue
            window["-STATUS-"].update("Running → %s" % output_port)
            set_running_ui(window, True)
        elif event == "-STOP-":
            try:
                transformer.stop()
            except Exception as exc:
                logging.exception("Failed to stop")
                window["-STATUS-"].update(str(exc))
                continue
            window["-STATUS-"].update("Stopped")
            set_running_ui(window, False)
        elif event == "-PANIC-":
            try:
                transformer.panic()
            except Exception as exc:
                logging.exception("Failed to panic")
                window["-STATUS-"].update(str(exc))
                continue
            if transformer.running:
                window["-STATUS-"].update(
                    "Running → %s" % (transformer.output_port_name or values["-OUTPUT-"])
                )
            else:
                window["-STATUS-"].update("Panic sent")
        elif event == "-NOTE-":
            input_name, output_name = values[event]
            window["-INPUT-NOTE-"].update(input_name or "-")
            window["-OUTPUT-NOTE-"].update(output_name or "-")
        elif event == "-PRESET-":
            root, mode_label = values[event]
            window["-ROOT-"].update(value=root)
            window["-MODE-"].update(value=mode_label)
        elif event == "-ERROR-":
            window["-STATUS-"].update(str(values[event]))

    logging.info("Application exit")
    close_assign_window()
    try:
        transformer.close()
    except Exception:
        logging.exception("Error during shutdown")
    window.close()


if __name__ == "__main__":
    main()
