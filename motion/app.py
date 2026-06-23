"""Webcam loop: track a hand, detect swipes, switch tabs."""

import argparse
import sys

import cv2
import mediapipe as mp

from .actions import TabSwitcher
from .gesture import SwipeDetector

# Landmark 9 (middle-finger base) is a stable proxy for the palm center.
PALM_LANDMARK = 9


def run(camera=0, show_window=True, invert=False, min_distance=0.22, dry_run=False):
    hands_solution = mp.solutions.hands
    drawing = mp.solutions.drawing_utils

    cap = cv2.VideoCapture(camera)
    if not cap.isOpened():
        print(f"Could not open camera {camera}. Is another app using it?", file=sys.stderr)
        return 1

    detector = SwipeDetector(min_distance=min_distance)
    switcher = TabSwitcher()
    last_action = ""

    print("Motion is running. Swipe your hand left/right to switch tabs.")
    print("Press 'q' in the window (or Ctrl+C here) to quit.")

    with hands_solution.Hands(
        max_num_hands=1,
        model_complexity=0,
        min_detection_confidence=0.6,
        min_tracking_confidence=0.5,
    ) as hands:
        try:
            while cap.isOpened():
                ok, frame = cap.read()
                if not ok:
                    continue

                # Mirror the frame so it feels like a mirror to the user.
                frame = cv2.flip(frame, 1)
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                rgb.flags.writeable = False
                result = hands.process(rgb)

                if result.multi_hand_landmarks:
                    landmarks = result.multi_hand_landmarks[0]
                    x = landmarks.landmark[PALM_LANDMARK].x  # normalized 0..1
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
                        drawing.draw_landmarks(
                            frame, landmarks, hands_solution.HAND_CONNECTIONS
                        )
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
