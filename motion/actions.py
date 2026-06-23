"""Turn detected swipes into keyboard shortcuts sent to the focused app."""

import time

from pynput.keyboard import Controller, Key


class TabSwitcher:
    """Switches tabs in the focused app via Ctrl+Tab / Ctrl+Shift+Tab.

    Works in Chrome, VS Code, most terminals, and many other apps.
    """

    label_forward = "Next tab  ->"
    label_backward = "<- Prev tab"

    def __init__(self):
        self.keyboard = Controller()

    def forward(self):
        with self.keyboard.pressed(Key.ctrl):
            self._tap(Key.tab)

    def backward(self):
        with self.keyboard.pressed(Key.ctrl, Key.shift):
            self._tap(Key.tab)

    def _tap(self, key):
        self.keyboard.press(key)
        self.keyboard.release(key)

    def tick(self):
        """Called every frame; nothing to do for tab switching."""

    def close(self):
        """Called on shutdown; nothing to release for tab switching."""


class AppSwitcher:
    """Switches apps the way Cmd+Tab does on macOS.

    macOS only cycles through the app list while Cmd is held — a lone Cmd+Tab
    just toggles the two most recent apps. So we hold Cmd down across swipes,
    tap Tab (or Shift+Tab) per swipe to move the selection, and release Cmd
    after a short pause to commit, exactly like letting go of Cmd+Tab.

    Args:
        hold_timeout: Seconds of no swiping before Cmd is released (commit).
                      Keep this longer than the swipe cooldown so the switcher
                      stays open between consecutive swipes.
    """

    label_forward = "Next app  ->"
    label_backward = "<- Prev app"

    def __init__(self, hold_timeout=1.5):
        self.keyboard = Controller()
        self.hold_timeout = hold_timeout
        self._cmd_held = False
        self._last_action = 0.0

    def _ensure_cmd(self):
        if not self._cmd_held:
            self.keyboard.press(Key.cmd)
            self._cmd_held = True

    def _tap(self, key):
        self.keyboard.press(key)
        self.keyboard.release(key)

    def forward(self):
        self._ensure_cmd()
        self._tap(Key.tab)
        self._last_action = time.time()

    def backward(self):
        self._ensure_cmd()
        with self.keyboard.pressed(Key.shift):
            self._tap(Key.tab)
        self._last_action = time.time()

    def tick(self):
        """Release Cmd (commit the selection) once swiping pauses."""
        if self._cmd_held and time.time() - self._last_action > self.hold_timeout:
            self.close()

    def close(self):
        if self._cmd_held:
            self.keyboard.release(Key.cmd)
            self._cmd_held = False
