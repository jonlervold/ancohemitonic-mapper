"""Live MIDI transformer: white keys to ancohemitonic mode, routed to a MIDI output."""

import logging
import sys

import rtmidi

from mapping import build_white_key_mapping, mode_offsets_from_formula, transform_note_with_mapping
from modes import DEFAULT_MODE_LABEL, formula_for_label, label_for_mode_name
from notes import DEFAULT_ROOT, midi_to_name, parse_root
from presets import SLOT_COUNT, empty_slots

CLIENT_NAME = "Ancohemitonic Mapper"
CONTROL_CLIENT_NAME = "Ancohemitonic Mapper Control"
PREFERRED_OUTPUT_NAMES = (
    "IAC Driver Entonal Out",
    "IAC Driver Bus 1",
)

STATUS_NOTE_OFF = 0x80
STATUS_NOTE_ON = 0x90
STATUS_POLY_AT = 0xA0
STATUS_CC = 0xB0
STATUS_PROGRAM = 0xC0
STATUS_CHANNEL_PRESSURE = 0xD0
STATUS_PITCH_BEND = 0xE0
STATUS_SYSTEM = 0xF0

CC_ALL_NOTES_OFF = 123

CHANNEL_MESSAGE_LENGTHS = {
    STATUS_NOTE_OFF: 3,
    STATUS_NOTE_ON: 3,
    STATUS_POLY_AT: 3,
    STATUS_CC: 3,
    STATUS_PROGRAM: 2,
    STATUS_CHANNEL_PRESSURE: 2,
    STATUS_PITCH_BEND: 3,
}


def _api_description(api):
    try:
        return "%s (%s, id=%s)" % (
            rtmidi.get_api_display_name(api),
            rtmidi.get_api_name(api),
            api,
        )
    except Exception:
        return "id=%s" % api


def _configured_api():
    """Use CoreMIDI explicitly on macOS instead of RtMidi's backend auto-selection."""
    if sys.platform != "darwin":
        return rtmidi.API_UNSPECIFIED

    core_midi = rtmidi.API_MACOSX_CORE
    compiled = list(rtmidi.get_compiled_api() or [])
    if core_midi not in compiled:
        available = ", ".join(_api_description(api) for api in compiled) or "none"
        raise RuntimeError(
            "python-rtmidi was built without CoreMIDI support; available backends: %s"
            % available
        )
    return core_midi


def log_midi_environment():
    """Log runtime MIDI backend details for troubleshooting."""
    try:
        compiled = list(rtmidi.get_compiled_api() or [])
        descriptions = [_api_description(api) for api in compiled]
    except Exception:
        logging.exception("Could not inspect compiled MIDI backends")
        descriptions = []
    logging.info(
        "MIDI runtime: python=%s executable=%s platform=%s frozen=%s rtmidi=%s",
        sys.version.replace("\n", " "),
        sys.executable,
        sys.platform,
        bool(getattr(sys, "frozen", False)),
        getattr(rtmidi, "__version__", "unknown"),
    )
    logging.info("Compiled MIDI backends: %s", descriptions or ["none reported"])
    try:
        logging.info("Selected MIDI backend policy: %s", _api_description(_configured_api()))
    except Exception:
        logging.exception("CoreMIDI backend validation failed")


class MidiTransformer:
    def __init__(self, window):
        self.window = window
        self.midi_in = None
        self.midi_control_in = None
        self.midi_out = None
        self.output_port_name = None
        self.force_channel = False
        self.channel = 1
        self.running = False
        self.active_notes = {}
        self._used_out_channels = set()
        self.preset_slots = empty_slots()
        self.root_pc = parse_root(DEFAULT_ROOT)
        self.mode_offsets = tuple(mode_offsets_from_formula(formula_for_label(DEFAULT_MODE_LABEL)))
        self._mapping = build_white_key_mapping(self.root_pc, self.mode_offsets)

    def set_root(self, root_name):
        self.root_pc = parse_root(root_name)
        self._rebuild_mapping()

    def set_mode(self, mode_label):
        formula = formula_for_label(mode_label)
        self.mode_offsets = tuple(mode_offsets_from_formula(formula))
        self._rebuild_mapping()

    def set_preset_slot(self, pitch_class, root=None, mode_name=None):
        if pitch_class < 0 or pitch_class >= SLOT_COUNT:
            raise ValueError("Preset slot must be 0-11")
        if not root or not mode_name:
            self.preset_slots[pitch_class] = None
            return
        parse_root(root)
        label_for_mode_name(mode_name)
        self.preset_slots[pitch_class] = (root, mode_name)

    def set_preset_slots(self, slots):
        if len(slots) != SLOT_COUNT:
            raise ValueError("Expected %d preset slots" % SLOT_COUNT)
        validated = empty_slots()
        for pitch_class, slot in enumerate(slots):
            if slot is None:
                continue
            root, mode_name = slot
            parse_root(root)
            label_for_mode_name(mode_name)
            validated[pitch_class] = (root, mode_name)
        self.preset_slots = validated

    def _rebuild_mapping(self):
        self._mapping = build_white_key_mapping(self.root_pc, self.mode_offsets)

    def list_inputs(self):
        probe = None
        try:
            probe = rtmidi.MidiIn(rtapi=_configured_api(), name=CLIENT_NAME)
            logging.info(
                "MIDI input scan backend: %s",
                _api_description(probe.get_current_api()),
            )
            ports = list(probe.get_ports() or [])
        except Exception:
            logging.exception("Failed to list MIDI input devices")
            ports = []
        finally:
            if probe is not None:
                del probe
        return [name for name in ports if name]

    def list_outputs(self):
        probe = None
        try:
            probe = rtmidi.MidiOut(rtapi=_configured_api(), name=CLIENT_NAME)
            logging.info(
                "MIDI output scan backend: %s",
                _api_description(probe.get_current_api()),
            )
            ports = list(probe.get_ports() or [])
        except Exception:
            logging.exception("Failed to list MIDI output devices")
            ports = []
        finally:
            if probe is not None:
                del probe
        return [name for name in ports if name]

    def default_input(self, ports):
        if ports:
            return ports[0]
        return None

    def default_output(self, ports):
        for preferred in PREFERRED_OUTPUT_NAMES:
            if preferred in ports:
                return preferred
        if ports:
            return ports[0]
        return None

    def ensure_midi_out(self, port_name):
        if not port_name:
            raise ValueError("No MIDI output device selected.")

        if (
            self.midi_out is not None
            and self.midi_out.is_port_open()
            and self.output_port_name == port_name
        ):
            return

        self._close_midi_out()

        requested_api = _configured_api()
        midi_out = rtmidi.MidiOut(rtapi=requested_api, name=CLIENT_NAME)
        actual_api = midi_out.get_current_api()
        logging.info("MIDI output backend: %s", _api_description(actual_api))
        if sys.platform == "darwin" and actual_api != rtmidi.API_MACOSX_CORE:
            del midi_out
            raise RuntimeError(
                "Expected CoreMIDI but python-rtmidi selected %s"
                % _api_description(actual_api)
            )

        ports = list(midi_out.get_ports() or [])
        logging.info("Available MIDI output destinations: %s", ports)
        try:
            index = ports.index(port_name)
        except ValueError:
            del midi_out
            raise RuntimeError(
                "MIDI output %r was not found. Available outputs: %s"
                % (port_name, ports)
            )
        try:
            midi_out.open_port(index)
        except Exception:
            del midi_out
            raise
        self.midi_out = midi_out
        self.output_port_name = port_name
        logging.info("Opened MIDI output destination: %s", port_name)

    def start(self, input_port_name, output_port_name, control_port_name=None):
        if self.running:
            return
        if not input_port_name:
            raise ValueError("No MIDI input device selected.")
        if not output_port_name:
            raise ValueError("No MIDI output device selected.")
        if control_port_name:
            if control_port_name == input_port_name:
                raise ValueError("Mode keyboard must be a different device.")

        self.ensure_midi_out(output_port_name)

        midi_in = self._open_midi_in(input_port_name, CLIENT_NAME, self._callback)
        midi_control_in = None
        if control_port_name:
            try:
                midi_control_in = self._open_midi_in(
                    control_port_name,
                    CONTROL_CLIENT_NAME,
                    self._control_callback,
                )
            except Exception:
                self._close_midi_in(midi_in)
                raise

        self.midi_in = midi_in
        self.midi_control_in = midi_control_in
        self.running = True
        logging.info("Selected MIDI input: %s", input_port_name)
        logging.info("Selected MIDI output: %s", output_port_name)
        if control_port_name:
            logging.info("Selected mode keyboard: %s", control_port_name)
        logging.info("Started")

    def _open_midi_in(self, port_name, client_name, callback):
        midi_in = rtmidi.MidiIn(rtapi=_configured_api(), name=client_name)
        logging.info(
            "MIDI input backend (%s): %s",
            client_name,
            _api_description(midi_in.get_current_api()),
        )
        ports = list(midi_in.get_ports() or [])
        logging.info("Detected MIDI devices: %s", ports)
        try:
            index = ports.index(port_name)
        except ValueError:
            del midi_in
            raise ValueError("MIDI input device not found: %s" % port_name)

        try:
            midi_in.ignore_types(sysex=True, timing=True, active_sense=True)
            midi_in.open_port(index)
            midi_in.set_callback(callback)
        except Exception:
            try:
                midi_in.close_port()
            except Exception:
                pass
            del midi_in
            raise
        return midi_in

    def stop(self):
        self.panic()
        midi_in = self.midi_in
        midi_control_in = self.midi_control_in
        self.midi_in = None
        self.midi_control_in = None
        self.running = False
        self._close_midi_in(midi_in)
        self._close_midi_in(midi_control_in)
        logging.info("Stopped")

    def _close_midi_in(self, midi_in):
        if midi_in is None:
            return
        try:
            midi_in.cancel_callback()
        except Exception:
            logging.exception("Error canceling MIDI callback")
        try:
            if midi_in.is_port_open():
                midi_in.close_port()
        except Exception:
            logging.exception("Error closing MIDI input")
        del midi_in

    def _close_midi_out(self):
        midi_out = self.midi_out
        self.midi_out = None
        closed_name = self.output_port_name
        self.output_port_name = None
        if midi_out is None:
            return
        try:
            if midi_out.is_port_open():
                midi_out.close_port()
        except Exception:
            logging.exception("Error closing MIDI output")
        del midi_out
        if closed_name:
            logging.info("Closed MIDI output: %s", closed_name)

    def close(self):
        self.stop()
        self._close_midi_out()

    def panic(self):
        held = list(self.active_notes.values())
        self.active_notes.clear()
        for output_note, out_channel in held:
            self._send([STATUS_NOTE_OFF | out_channel, output_note, 0])
        channels = set(self._used_out_channels)
        self._used_out_channels.clear()
        if not channels:
            channels = set(range(16))
        for channel in sorted(channels):
            self._send([STATUS_CC | channel, CC_ALL_NOTES_OFF, 0])

    def _callback(self, event, data=None):
        try:
            message, _dt = event
            self.handle_message(message)
        except Exception as exc:
            logging.exception("MIDI callback error")
            try:
                self.window.write_event_value("-ERROR-", str(exc))
            except Exception:
                pass

    def _control_callback(self, event, data=None):
        try:
            message, _dt = event
            self.handle_control_message(message)
        except Exception as exc:
            logging.exception("Mode keyboard callback error")
            try:
                self.window.write_event_value("-ERROR-", str(exc))
            except Exception:
                pass

    def handle_message(self, message):
        if not message:
            return
        status = message[0]
        if status >= STATUS_SYSTEM:
            return
        msg_type = status & 0xF0
        needed = CHANNEL_MESSAGE_LENGTHS.get(msg_type)
        if needed is None or len(message) < needed:
            return

        in_channel = status & 0x0F
        if msg_type == STATUS_NOTE_ON:
            velocity = message[2]
            if velocity == 0:
                self._handle_note_off(in_channel, message[1])
            else:
                self._handle_note_on(in_channel, message[1], velocity)
            return
        if msg_type == STATUS_NOTE_OFF:
            self._handle_note_off(in_channel, message[1])
            return

        self._send(self._with_output_channel(message, in_channel))

    def handle_control_message(self, message):
        if not message:
            return
        status = message[0]
        if status >= STATUS_SYSTEM:
            return
        msg_type = status & 0xF0
        needed = CHANNEL_MESSAGE_LENGTHS.get(msg_type)
        if needed is None or len(message) < needed:
            return
        if msg_type != STATUS_NOTE_ON:
            return
        if message[2] == 0:
            return
        self._apply_control_note(message[1])

    def _apply_control_note(self, input_note):
        slot = self.preset_slots[input_note % 12]
        if slot is None:
            return
        root, mode_name = slot
        label = label_for_mode_name(mode_name)
        self.set_root(root)
        self.set_mode(label)
        logging.info("Mode preset %s -> %s %s", input_note % 12, root, mode_name)
        try:
            self.window.write_event_value("-PRESET-", (root, label))
        except Exception:
            pass

    def _handle_note_on(self, in_channel, input_note, velocity):
        mapping = self._mapping
        output_note = transform_note_with_mapping(input_note, mapping)
        if output_note is None:
            return
        if output_note < 0 or output_note > 127:
            logging.debug(
                "Discarding out-of-range output note %s from input %s",
                output_note,
                input_note,
            )
            return

        key = (in_channel, input_note)
        previous = self.active_notes.get(key)
        if previous is not None:
            self._send([STATUS_NOTE_OFF | previous[1], previous[0], 0])

        out_channel = self._output_channel(in_channel)
        self.active_notes[key] = (output_note, out_channel)
        self._used_out_channels.add(out_channel)
        self._send([STATUS_NOTE_ON | out_channel, output_note, velocity])
        input_name = midi_to_name(input_note)
        output_name = midi_to_name(output_note)
        try:
            self.window.write_event_value("-NOTE-", (input_name, output_name))
        except Exception:
            pass

    def _handle_note_off(self, in_channel, input_note):
        previous = self.active_notes.pop((in_channel, input_note), None)
        if previous is None:
            return
        output_note, out_channel = previous
        self._send([STATUS_NOTE_OFF | out_channel, output_note, 0])

    def _output_channel(self, in_channel):
        if self.force_channel:
            return self.channel - 1
        return in_channel

    def _with_output_channel(self, message, in_channel):
        if not self.force_channel:
            return message
        out = list(message)
        out[0] = (out[0] & 0xF0) | self._output_channel(in_channel)
        return out

    def _send(self, message):
        midi_out = self.midi_out
        if midi_out is None:
            return
        midi_out.send_message(message)
