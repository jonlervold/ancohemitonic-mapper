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
3. Optionally check **Assign modes to second keyboard**, pick a different MIDI input as the **Mode keyboard**, and click **Edit key assignments...** to store up to 12 root/mode pairs on C–B.
4. Click **Start**.
5. Status should show `Running`. **Input** / **Output** update as you play white keys.

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

## 9. Second keyboard mode presets

With **Assign modes to second keyboard** unchecked, the app behaves as a single-input remapper.

When the checkbox is on:

1. Choose a **Mode keyboard** that is not the performance MIDI input.
2. Click **Edit key assignments...** to open the 12-key table. Each chromatic pitch class (`C` through `B`) can store a root and a short mode name, for example `C: D MM-1`. Leave a row as `(none)` to ignore that key.
3. Any octave of an assigned key switches Root and Mode for the performance keyboard. Held notes keep their current output pitches until released. Mode-keyboard notes and CCs are not sent to the MIDI output.

**Import...** / **Export...** in the assignment window read and write a plain text file. Unmentioned keys become empty on import. Example:

```
# Ancohemitonic Mapper mode presets
C: D MM-1
C#/Db: F Hu+3
D: E D0
```

