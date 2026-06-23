"""Swipe detection from a stream of hand x-positions."""

import time
from collections import deque


class SwipeDetector:
    """Detects fast horizontal hand swipes.

    Feed it the hand's horizontal position (normalized 0..1, where 0 is the
    left edge of the frame) once per video frame. It keeps a short rolling
    window of recent positions and fires "left" or "right" when the hand
    travels far enough across that window.

    Args:
        window_seconds: How far back to look when measuring travel.
        min_distance:   Minimum horizontal travel (fraction of frame width)
                        within the window to count as a swipe.
        cooldown:       Seconds to ignore new swipes after one fires, so a
                        single gesture doesn't trigger repeatedly.
    """

    def __init__(self, window_seconds=0.4, min_distance=0.22, cooldown=1.0):
        self.window_seconds = window_seconds
        self.min_distance = min_distance
        self.cooldown = cooldown
        self._samples = deque()  # (timestamp, x)
        self._last_trigger = 0.0

    def update(self, x, now=None):
        """Add a new sample and return "left", "right", or None."""
        now = time.time() if now is None else now
        self._samples.append((now, x))

        # Drop samples older than the window.
        while self._samples and now - self._samples[0][0] > self.window_seconds:
            self._samples.popleft()

        if now - self._last_trigger < self.cooldown:
            return None
        if len(self._samples) < 2:
            return None

        start_x = self._samples[0][1]
        end_x = self._samples[-1][1]
        dx = end_x - start_x

        if abs(dx) >= self.min_distance:
            self._last_trigger = now
            self._samples.clear()
            return "right" if dx > 0 else "left"
        return None

    def in_cooldown(self, now=None):
        now = time.time() if now is None else now
        return now - self._last_trigger < self.cooldown

    def reset(self):
        """Forget recent history (e.g. when the hand leaves the frame)."""
        self._samples.clear()
