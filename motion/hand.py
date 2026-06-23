"""Classify a hand as open or closed from its landmarks."""

WRIST = 0
# (fingertip, pip-joint) for index, middle, ring, pinky.
FINGERS = [(8, 6), (12, 10), (16, 14), (20, 18)]


def _dist(a, b):
    return ((a.x - b.x) ** 2 + (a.y - b.y) ** 2) ** 0.5


def count_extended_fingers(landmarks):
    """How many of the four fingers are extended (0–4).

    A finger is extended when its tip is farther from the wrist than its middle
    (PIP) joint — robust to hand rotation, unlike comparing y-coordinates.
    """
    wrist = landmarks[WRIST]
    extended = 0
    for tip, pip in FINGERS:
        if _dist(landmarks[tip], wrist) > _dist(landmarks[pip], wrist):
            extended += 1
    return extended


def hand_open(landmarks, open_threshold=3, closed_threshold=1):
    """Return True (open), False (closed/fist), or None (ambiguous).

    The gap between the thresholds is hysteresis: it keeps a hand that's
    mid-transition from flickering between states.
    """
    extended = count_extended_fingers(landmarks)
    if extended >= open_threshold:
        return True
    if extended <= closed_threshold:
        return False
    return None
