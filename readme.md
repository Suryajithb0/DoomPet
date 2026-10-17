# DOOM.exe — Desktop Pet

A sprite-animated desktop pet built with Python and PySide6.

## Features

- **Walk animation** — 8-frame cycle as the pet roams your desktop
- **Sit animation** — 4-frame resting loop when stationary
- **Attack animation** — 8-frame magic attack triggered by left-click
- **Drag & drop** — grab and move the pet anywhere on screen
- **Right-click menu** — Pause/Resume movement and Quit
- **Ambient green flames** — subtle particle magic from the staff while idle
- **Always on top** — frameless, transparent, stays visible

## Sprite Assets

```
pet/walk/1.png   … 8.png    (walk cycle)
pet/sit/1.png    … 4.png    (sitting/resting)
pet/attack/1.png … 8.png    (attack sequence)
```

## Setup

### Prerequisites

- Python 3.10+

### Activate the existing virtual environment

```bash
# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1

# Windows (Command Prompt)
.\.venv\Scripts\activate.bat
```

### Install dependencies (if needed)

```bash
pip install -r requirements.txt
```

## Run

```powershell
# Option 1: Run directly with the venv's Python (no activation needed)
.\.venv\Scripts\python.exe main.py

# Option 2: Activate first, then run
.\.venv\Scripts\Activate.ps1
python main.py
```

> **Note:** If PowerShell blocks `.ps1` scripts, either use Option 1 or run this once to fix it:
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
> ```

## Controls

| Input | Action |
|-------|--------|
| **Left-click** | Trigger attack animation |
| **Left-click + drag** | Move the pet (does not trigger attack) |
| **Right-click** | Context menu: Pause/Resume, Quit |

## Configuration

Sprite size is configurable at the top of `main.py`:

```python
SPRITE_WIDTH  = 128
SPRITE_HEIGHT = 128
```

Change these values to resize the pet proportionally.
