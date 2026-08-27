# Ancohemitonic Mapper

A small macOS utility that remaps the seven white keys of a MIDI keyboard (`C D E F G A B`) to the seven degrees of a selected ancohemitonic mode and sends the result to a chosen MIDI output (typically an IAC bus).

Target: macOS 11 Big Sur (Intel or Apple Silicon). Use Python 3.11 or 3.12.

## 1. Create a virtualenv

```bash
cd "/path/to/Mac MIDI Input Transformer"
python3 -m venv venv
source venv/bin/activate
```

Use a python.org **3.11 or 3.12** installer. On an Intel Mac, use the Intel 64-bit build. Avoid Python 3.13: `python-rtmidi` 1.5.8 has no 3.13 wheels, and a source build would need Xcode.

## 2. Install requirements

```bash
pip install -r requirements.txt
```

This installs `python-rtmidi`, `PySimpleGUI`, and `PyInstaller`. Prebuilt wheels are used, so Xcode is not required.

## 3. Run from source

```bash
python3 main.py
```

1. Choose a MIDI input device and a MIDI output device (Refresh if ports changed after launch).
2. Choose Root and Mode. Physical white keys always play degrees 1–7 of that mode.
3. Click **Start**.
4. Status should show `Running`. **Input** / **Output** update as you play white keys.

Logs are written to `~/Library/Logs/Ancohemitonic Mapper.log`.

## 4. Tests

```bash
python3 -m unittest discover -s tests -t .
```

These tests cover mapping examples and MIDI bookkeeping. They do not require MIDI hardware.

## 5. Build with PyInstaller

With the venv activated:

```bash
chmod +x build.sh
./build.sh
```

This creates:

```text
dist/Ancohemitonic Mapper.app
```

Build the `.app` on the Big Sur Mac so it links against compatible system libraries.

## 6. Launch the `.app`

- Double-click `dist/Ancohemitonic Mapper.app`, or
- If Gatekeeper blocks it: Right-click the app → **Open** → **Open**.

Keep the app running while Pro Tools is listening to the selected MIDI output. Stopping in the UI disconnects the physical keyboard.

## 7. MIDI routing

```text
MIDI Keyboard
      |
      v
Ancohemitonic Mapper
      |
      v
Selected MIDI Output
(e.g. IAC Driver Entonal Out)
      |
      v
Pro Tools MIDI / Instrument Track
      |
      v
Instrument
```

The physical keyboard's raw MIDI must not also be routed to the same instrument, or both original and transformed notes will sound.

## 8. Pro Tools setup

1. In Audio MIDI Setup, open **MIDI Studio**, double-click **IAC Driver**, and enable a bus such as **Entonal Out**.
2. In the mapper, select that bus in **MIDI Output** (Refresh if needed). The app prefers **IAC Driver Entonal Out** when present.
3. In Pro Tools, open **Setup > MIDI > Input Devices** and enable the same IAC bus.
4. Click **Start** in the mapper and select your keyboard as the app's MIDI input.
5. In Pro Tools, set the instrument track's MIDI input to that IAC bus.
6. Do **not** also enable the raw keyboard port on that track.

Root and Mode can be changed while running. Already-held notes keep their original pitches until released. **Panic** sends Note Off for held notes and All Notes Off (CC123).

Use **Force output channel** only if the destination expects a specific MIDI channel (1–16). By default the incoming channel is preserved.

Black keys are ignored. Sustain, other CCs, pitch bend, aftertouch, and program change pass through.

