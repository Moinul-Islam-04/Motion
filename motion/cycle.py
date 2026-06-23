"""Drive Cmd+Tab-style app cycling from open/closed hand states."""

import time


class CycleController:
    """Turns a stream of hand-open states into held Cmd+Tab app cycling.

    Close your hand (fist) to open the macOS app switcher and start cycling;
    while your hand stays closed it advances one app every `cycle_interval`
    seconds. Open your hand to release Cmd and land on the highlighted app.

    The switcher must expose forward()/backward() (which hold Cmd and tap Tab)
    and close() (which releases Cmd to commit) — see actions.AppSwitcher.

    Args:
        reverse:        Cycle backwards (Cmd+Shift+Tab) instead of forwards.
        cycle_interval: Seconds between advances while the fist is held.
        lost_timeout:   If the hand vanishes mid-cycle for this long, commit
                        anyway so Cmd never gets stuck down.
    """

    def __init__(self, switcher, reverse=False, cycle_interval=0.8, lost_timeout=1.0):
        self.switcher = switcher
        self.reverse = reverse
        self.cycle_interval = cycle_interval
        self.lost_timeout = lost_timeout
        self.active = False
        self._last_step = 0.0
        self._last_seen = 0.0

    def _step(self):
        if self.reverse:
            self.switcher.backward()
        else:
            self.switcher.forward()

    def update(self, hand_open, hand_present, now=None):
        """Advance the state machine one frame.

        Returns "engage", "step", "commit", or None.
        `hand_open` is True/False/None (None = ambiguous), per hand.hand_open.
        """
        now = time.time() if now is None else now
        if hand_present:
            self._last_seen = now

        if not self.active:
            # A fist opens the switcher and takes the first step.
            if hand_present and hand_open is False:
                self.active = True
                self._step()
                self._last_step = now
                return "engage"
            return None

        # Active: opening the hand commits the current selection.
        if hand_present and hand_open is True:
            self._commit()
            return "commit"
        # Safety: hand lost for too long -> commit so Cmd isn't left held.
        if now - self._last_seen > self.lost_timeout:
            self._commit()
            return "commit"
        # Still fisted: keep advancing at a readable pace. Ambiguous = hold.
        if hand_open is False and now - self._last_step >= self.cycle_interval:
            self._step()
            self._last_step = now
            return "step"
        return None

    def _commit(self):
        self.switcher.close()
        self.active = False
