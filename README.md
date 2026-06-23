# Motion

Control your Mac with a wave of your hand. Motion uses your MacBook camera to
track your hand and switches between **apps** (or tabs) when you swipe left or
right.

By default it switches **applications**, exactly like Cmd+Tab: it holds Cmd
while you swipe, taps Tab per swipe to move through the app list, and releases
Cmd to commit once you pause. Pass `--mode tabs` to switch tabs in the focused
app instead (via `Ctrl+Tab` / `Ctrl+Shift+Tab`, which work in Chrome, VS Code,
terminals, and more).

## How it works

1. **Capture** — OpenCV reads frames from the webcam.
2. **Detect** — MediaPipe's `HandLandmarker` (Tasks API) finds your hand and its
   landmarks each frame. The model (~7 MB) auto-downloads to `models/` on first run.
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
| `--mode tabs` | Switch tabs instead of apps (default is `apps`). |
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

The keystrokes live in `motion/actions.py`: `AppSwitcher` (Cmd+Tab cycling) and
`TabSwitcher` (`Ctrl+Tab`). Swap them for any shortcut you like — e.g.
`Cmd+Option+Right/Left` to make tab switching Chrome/Safari-specific.
