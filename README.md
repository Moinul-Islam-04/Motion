# Motion

Control your tabs with a wave of your hand. Motion uses your MacBook camera to
track your hand and switches between tabs when you swipe left or right.

It works **system-wide** by sending keyboard shortcuts to whatever app is
focused — `Ctrl+Tab` (next tab) and `Ctrl+Shift+Tab` (previous tab), which work
in Chrome, VS Code, terminals, and most apps.

## How it works

1. **Capture** — OpenCV reads frames from the webcam.
2. **Detect** — MediaPipe Hands finds your hand and its landmarks each frame.
3. **Recognize** — a rolling window of the palm's horizontal position decides
   whether you made a fast left or right swipe.
4. **Act** — `pynput` sends the next/previous-tab keystroke to the focused app.

## Setup

Requires Python 3.10–3.12.

```bash
cd Motion
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### macOS permissions (important)

The first run will prompt for two permissions. Grant both, then restart the
terminal app you launched Motion from:

- **Camera** — System Settings → Privacy & Security → Camera → enable your
  terminal (Terminal/iTerm) or IDE.
- **Accessibility** — System Settings → Privacy & Security → Accessibility →
  enable the same app. This is required to send keystrokes to other apps.

## Usage

```bash
python main.py
```

A preview window opens showing your hand and a READY/COOLDOWN status. Swipe your
open hand left or right. Press `q` (or Ctrl+C in the terminal) to quit.

### Options

| Flag | What it does |
|------|--------------|
| `--dry-run` | Detect and print swipes without sending keystrokes (great for testing). |
| `--invert` | Swap swipe direction if left/right feel backwards. |
| `--min-distance 0.18` | Sensitivity — smaller is more sensitive (default `0.22`). |
| `--no-window` | Run headless, without the preview window. |
| `--camera 1` | Use a different camera index. |

Try a dry run first to tune the feel:

```bash
python main.py --dry-run
```

## Customizing the shortcut

The keystrokes live in `motion/actions.py` (`TabSwitcher.next_tab` /
`prev_tab`). Swap them for, say, `Cmd+Option+Right/Left` to make it
Chrome/Safari-specific, or any other shortcut you like.
