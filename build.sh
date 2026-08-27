#!/bin/bash
set -euo pipefail

python3 -m PyInstaller \
  --clean \
  --noconfirm \
  --windowed \
  --name "Ancohemitonic Mapper" \
  --hidden-import=rtmidi \
  --hidden-import=PySimpleGUI \
  --hidden-import=mapping \
  --hidden-import=modes \
  --hidden-import=notes \
  --hidden-import=transformer \
  --collect-all rtmidi \
  main.py
