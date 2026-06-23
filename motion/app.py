"""Webcam loop: track a hand, detect swipes, switch tabs.

Uses the MediaPipe Tasks API (HandLandmarker), which replaced the legacy
mp.solutions.hands API in recent MediaPipe releases.
"""

import argparse
import sys
import time

import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

from .actions import TabSwitcher
from .gesture import SwipeDetector
from .model import ensure_model

# Landmark 9 (middle-finger base) is a stable proxy for the palm center.
PALM_LANDMARK = 9


def _build_landmarker():
    base_options = mp_python.BaseOptions(model_asset_path=ensure_model())
    options = vision.HandLandmarkerOptions(
        base_options=base_options,
        num_hands=1,
        running_mode=vision.RunningMode.VIDEO,
        min_hand_detection_confidence=0.6,
        min_tracking_confidence=0.5,
    )
    return vision.HandLandmarker.create_from_options(options)


def _draw(frame, landmarks):
    h, w = frame.shape[:2]
    for lm in landmarks:
        cv2.circle(frame, (int(lm.x * w), int(lm.y * h)), 4, (0, 255, 0), -1)
    palm = landmarks[PALM_LANDMARK]
    cv2.circle(frame, (int(palm.x * w), int(palm.y * h)), 12, (255, 0, 0), 2)


def run(camera=0, show_window=True, invert=False, min_distance=0.22, dry_run=False):
    cap = cv2.VideoCapture(camera)
    if not cap.isOpened():
        print(f"Could not open camera {camera}. Is another app using it?", file=sys.stderr)
        return 1

    landmarker = _build_landmarker()
    detector = SwipeDetector(min_distance=min_distance)
    switcher = TabSwitcher()
    last_action = ""
    start = time.time()
    last_ts = -1

    print("Motion is running. Swipe your hand left/right to switch tabs.")
    print("Press 'q' in the window (or Ctrl+C here) to quit.")

    try:
        while cap.isOpened():
            ok, frame = cap.read()
            if not ok:
                continue

            # Mirror the frame so it feels like a mirror to the user.
            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

            # VIDEO mode needs a monotonically increasing timestamp in ms.
            ts = int((time.time() - start) * 1000)
            if ts <= last_ts:
                ts = last_ts + 1
            last_ts = ts

            result = landmarker.detect_for_video(mp_image, ts)

            if result.hand_landmarks:
                landmarks = result.hand_landmarks[0]
                x = landmarks[PALM_LANDMARK].x  # normalized 0..1
                swipe = detector.update(x)

                if swipe:
                    # In the mirrored frame, moving your hand to your right
                    # increases x. "right" -> next tab by default.
                    go_next = (swipe == "right") != invert
                    if go_next:
                        last_action = "Next tab  ->"
                        if not dry_run:
                            switcher.next_tab()
                    else:
                        last_action = "<- Prev tab"
                        if not dry_run:
                            switcher.prev_tab()
                    print(last_action)

                if show_window:
                    _draw(frame, landmarks)
            else:
                detector.reset()

            if show_window:
                status = "COOLDOWN" if detector.in_cooldown() else "READY"
                cv2.putText(frame, f"{status}  {last_action}", (12, 32),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                cv2.imshow("Motion", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
    except KeyboardInterrupt:
        pass
    finally:
        landmarker.close()
        cap.release()
        cv2.destroyAllWindows()
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="Swipe between tabs with your webcam.")
    parser.add_argument("--camera", type=int, default=0, help="Camera index (default 0).")
    parser.add_argument("--no-window", action="store_true", help="Run without the preview window.")
    parser.add_argument("--invert", action="store_true", help="Swap swipe direction.")
    parser.add_argument("--min-distance", type=float, default=0.22,
                        help="Swipe sensitivity: smaller = more sensitive (default 0.22).")
    parser.add_argument("--dry-run", action="store_true",
                        help="Detect and print swipes without sending keystrokes.")
    args = parser.parse_args(argv)

    return run(
        camera=args.camera,
        show_window=not args.no_window,
        invert=args.invert,
        min_distance=args.min_distance,
        dry_run=args.dry_run,
    )
