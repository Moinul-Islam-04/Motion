"""Turn detected gestures into keyboard shortcuts sent to the focused app."""

import time

from pynput.keyboard import Controller, Key


class _Switcher:
    """Shared keyboard plumbing. When dry_run is set, no keys are sent."""

    def __init__(self, dry_run=False):
        self.keyboard = Controller()
        self.dry_run = dry_run

    def _tap(self, key):
        if self.dry_run:
            return
        self.keyboard.press(key)
        self.keyboard.release(key)

    def _press(self, key):
        if not self.dry_run:
            self.keyboard.press(key)

    def _release(self, key):
        if not self.dry_run:
            self.keyboard.release(key)

    def _combo(self, *modifiers, key):
        if self.dry_run:
            return
        with self.keyboard.pressed(*modifiers):
            self.keyboard.press(key)
            self.keyboard.release(key)

    def close(self):
        """Release anything still held. Overridden where needed."""


class TabSwitcher(_Switcher):
    """Switches tabs in the focused app via Ctrl+Tab / Ctrl+Shift+Tab.

    Works in Chrome, VS Code, most terminals, and many other apps.
    """

    label_forward = "Next tab  ->"
    label_backward = "<- Prev tab"

    def forward(self):
        self._combo(Key.ctrl, key=Key.tab)

    def backward(self):
        self._combo(Key.ctrl, Key.shift, key=Key.tab)


class AppSwitcher(_Switcher):
    """Switches apps the way Cmd+Tab does on macOS.

    macOS only walks the full app list while Cmd is held — a lone Cmd+Tab just
    toggles the two most recent apps. So forward()/backward() press Cmd once and
    keep it down, tapping Tab (or Shift+Tab) to move the highlight; close()
    releases Cmd to commit the selection. CycleController drives this from
    open/closed hand gestures.
    """

    label_forward = "Next app  ->"
    label_backward = "<- Prev app"

    def __init__(self, dry_run=False):
        super().__init__(dry_run=dry_run)
        self._cmd_held = False

    def _ensure_cmd(self):
        if not self._cmd_held:
            self._press(Key.cmd)
            self._cmd_held = True

    def forward(self):
        self._ensure_cmd()
        self._tap(Key.tab)

    def backward(self):
        self._ensure_cmd()
        if self.dry_run:
            return
        with self.keyboard.pressed(Key.shift):
            self.keyboard.press(Key.tab)
            self.keyboard.release(Key.tab)

    def close(self):
        if self._cmd_held:
            self._release(Key.cmd)
            self._cmd_held = False
