"""Webcam loop: track a hand, recognize gestures, switch apps or tabs.

Uses the MediaPipe Tasks API (HandLandmarker), which replaced the legacy
mp.solutions.hands API in recent MediaPipe releases.

Two interaction modes:
  apps (default) — make a fist to open the macOS app switcher and cycle through
                   apps; open your hand to land on the highlighted one.
  tabs           — swipe left/right to switch tabs in the focused app.
"""

import argparse
import sys
import time

import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

from .actions import AppSwitcher, TabSwitcher
from .cycle import CycleController
from .gesture import SwipeDetector
from .hand import count_extended_fingers, hand_open
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


def _draw(frame, landmarks, closed):
    h, w = frame.shape[:2]
    for lm in landmarks:
        cv2.circle(frame, (int(lm.x * w), int(lm.y * h)), 4, (0, 255, 0), -1)
    palm = landmarks[PALM_LANDMARK]
    color = (0, 0, 255) if closed else (255, 0, 0)  # red when fisted
    cv2.circle(frame, (int(palm.x * w), int(palm.y * h)), 12, color, 2)


def run(camera=0, show_window=True, invert=False, min_distance=0.22,
        dry_run=False, mode="apps", cycle_interval=0.8):
    cap = cv2.VideoCapture(camera)
    if not cap.isOpened():
        print(f"Could not open camera {camera}. Is another app using it?", file=sys.stderr)
        return 1

    landmarker = _build_landmarker()
    if mode == "apps":
        switcher = AppSwitcher(dry_run=dry_run)
        controller = CycleController(switcher, reverse=invert, cycle_interval=cycle_interval)
        detector = None
        print("Motion is running (app switching).")
        print("Make a FIST to open the switcher and cycle; OPEN your hand to select.")
    else:
        switcher = TabSwitcher(dry_run=dry_run)
        controller = None
        detector = SwipeDetector(min_distance=min_distance)
        print("Motion is running (tab switching). Swipe left/right to switch tabs.")
    print("Press 'q' in the window (or Ctrl+C here) to quit.")

    start = time.time()
    last_ts = -1
    last_action = ""

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
            landmarks = result.hand_landmarks[0] if result.hand_landmarks else None
            now = time.time()

            if mode == "apps":
                state = hand_open(landmarks) if landmarks is not None else None
                event = controller.update(
                    hand_open=state, hand_present=landmarks is not None, now=now)
                if event == "engage":
                    last_action = "Cycling apps..."
                    print("Cycling apps...")
                elif event == "step":
                    last_action = "Cycling apps..."
                elif event == "commit":
                    last_action = "Selected app"
                    print("Selected app")
            else:
                if landmarks is not None:
                    swipe = detector.update(landmarks[PALM_LANDMARK].x)
                    if swipe:
                        # Mirrored frame: hand moving right increases x.
                        go_next = (swipe == "right") != invert
                        if go_next:
                            last_action = switcher.label_forward
                            switcher.forward()
                        else:
                            last_action = switcher.label_backward
                            switcher.backward()
                        print(last_action)
                else:
                    detector.reset()

            if show_window:
                if landmarks is not None:
                    closed = mode == "apps" and controller.active
                    _draw(frame, landmarks, closed)
                if mode == "apps":
                    status = "CYCLING" if controller.active else "READY"
                    if landmarks is not None:
                        status += f"  fingers:{count_extended_fingers(landmarks)}"
                else:
                    status = "COOLDOWN" if detector.in_cooldown() else "READY"
                cv2.putText(frame, f"{status}  {last_action}", (12, 32),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                cv2.imshow("Motion", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
    except KeyboardInterrupt:
        pass
    finally:
        switcher.close()
        landmarker.close()
        cap.release()
        cv2.destroyAllWindows()
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="Switch apps or tabs with webcam hand gestures.")
    parser.add_argument("--mode", choices=["apps", "tabs"], default="apps",
                        help="Fist-cycle apps (Cmd+Tab) or swipe tabs (default apps).")
    parser.add_argument("--camera", type=int, default=0, help="Camera index (default 0).")
    parser.add_argument("--no-window", action="store_true", help="Run without the preview window.")
    parser.add_argument("--invert", action="store_true",
                        help="Reverse direction (swipe in tabs mode, cycle order in apps mode).")
    parser.add_argument("--min-distance", type=float, default=0.22,
                        help="Tabs mode swipe sensitivity: smaller = more sensitive (default 0.22).")
    parser.add_argument("--cycle-interval", type=float, default=0.8,
                        help="Apps mode: seconds between app advances while fisted (default 0.8).")
    parser.add_argument("--dry-run", action="store_true",
                        help="Detect and print gestures without sending keystrokes.")
    args = parser.parse_args(argv)

    return run(
        camera=args.camera,
        show_window=not args.no_window,
        invert=args.invert,
        min_distance=args.min_distance,
        dry_run=args.dry_run,
        mode=args.mode,
        cycle_interval=args.cycle_interval,
    )
