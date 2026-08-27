#!/usr/bin/env python3
"""Ancohemitonic Mapper: remap C-major white keys to a selected 7-note mode."""

import logging
import os
import sys

import PySimpleGUI as sg
import rtmidi  # noqa: F401  # load CoreMIDI the same way EWI Breath Filter does

from modes import DEFAULT_MODE_LABEL, MODE_LABELS
from notes import DEFAULT_ROOT, NOTE_NAMES
from transformer import MidiTransformer, log_midi_environment

APP_NAME = "Ancohemitonic Mapper"

LOG_DIR = os.path.join(os.path.expanduser("~"), "Library", "Logs")
LOG_PATH = os.path.join(LOG_DIR, "Ancohemitonic Mapper.log")


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
    return inputs, outputs


def set_running_ui(window, running):
    window["-DEVICE-"].update(disabled=running)
    window["-OUTPUT-"].update(disabled=running)
    window["-REFRESH-"].update(disabled=running)
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


def build_layout():
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
    _, outputs = refresh_devices(window, transformer)
    if outputs:
        window["-STATUS-"].update("Stopped")
    else:
        window["-STATUS-"].update("No MIDI output devices found.")
        window["-START-"].update(disabled=True)

    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, None):
            break

        if event in ("-FORCE-", "-CHANNEL-", "-ROOT-", "-MODE-"):
            apply_live_settings(window, transformer, values)
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
            if not apply_live_settings(window, transformer, values):
                continue
            try:
                transformer.start(input_port, output_port)
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
        elif event == "-ERROR-":
            window["-STATUS-"].update(str(values[event]))

    logging.info("Application exit")
    try:
        transformer.close()
    except Exception:
        logging.exception("Error during shutdown")
    window.close()


if __name__ == "__main__":
    main()
