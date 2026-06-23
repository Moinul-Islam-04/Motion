# Motion

Control your Mac with a wave of your hand. Motion uses your MacBook camera to
track your hand and switches between **apps** (or tabs) when you swipe left or
right.

By default it switches **applications**, exactly like Cmd+Tab:

- **Make a fist** to open the macOS app switcher. Motion holds Cmd down and
  cycles through your apps one at a time while your fist stays closed.
- **Open your hand** when the app you want is highlighted — Motion releases Cmd
  and lands on it.

This mirrors how Cmd+Tab actually works: macOS only walks the full app list
while Cmd is held (a single Cmd+Tab just toggles the two most recent apps), so
Motion keeps Cmd down for the duration of your fist.

Pass `--mode tabs` to switch tabs in the focused app instead: **swipe left or
right** to move between tabs (via `Ctrl+Tab` / `Ctrl+Shift+Tab`, which work in
Chrome, VS Code, terminals, and more).

## How it works

1. **Capture** — OpenCV reads frames from the webcam.
2. **Detect** — MediaPipe's `HandLandmarker` (Tasks API) finds your hand and its
   landmarks each frame. The model (~7 MB) auto-downloads to `models/` on first run.
3. **Recognize** —
   - *apps mode:* counting extended fingers tells an open hand from a fist; a
     small state machine (`cycle.py`) opens the switcher on a fist and commits
     when you open your hand.
   - *tabs mode:* a rolling window of the palm's horizontal position decides
     whether you made a fast left or right swipe (`gesture.py`).
4. **Act** — `pynput` holds/taps the right keystrokes for the focused app.

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
| `--dry-run` | Detect and print gestures without sending keystrokes (great for testing). |
| `--invert` | Reverse direction (swipe in tabs mode, cycle order in apps mode). |
| `--cycle-interval 0.6` | Apps mode: seconds between app advances while fisted (default `0.8`). |
| `--min-distance 0.18` | Tabs mode swipe sensitivity — smaller is more sensitive (default `0.22`). |
| `--no-window` | Run headless, without the preview window. |
| `--camera 1` | Use a different camera index. |

The preview window shows your hand landmarks, the extended-finger count, and a
READY/CYCLING status so you can see exactly when a fist registers.

Try a dry run first to tune the feel:

```bash
python main.py --dry-run
```

## Customizing the shortcut

The keystrokes live in `motion/actions.py`: `AppSwitcher` (Cmd+Tab cycling) and
`TabSwitcher` (`Ctrl+Tab`). Swap them for any shortcut you like — e.g.
`Cmd+Option+Right/Left` to make tab switching Chrome/Safari-specific.
