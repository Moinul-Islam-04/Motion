"""Turn detected swipes into keyboard shortcuts sent to the focused app."""

from pynput.keyboard import Controller, Key


class TabSwitcher:
    """Sends next/previous-tab keystrokes to whichever app is in focus.

    Defaults to Ctrl+Tab / Ctrl+Shift+Tab, which moves between tabs in
    Chrome, VS Code, most terminals, and many other apps on macOS.
    """

    def __init__(self):
        self.keyboard = Controller()

    def _send(self, *modifiers, key):
        if modifiers:
            with self.keyboard.pressed(*modifiers):
                self.keyboard.press(key)
                self.keyboard.release(key)
        else:
            self.keyboard.press(key)
            self.keyboard.release(key)

    def next_tab(self):
        self._send(Key.ctrl, key=Key.tab)

    def prev_tab(self):
        self._send(Key.ctrl, Key.shift, key=Key.tab)
