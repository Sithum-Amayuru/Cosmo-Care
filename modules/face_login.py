import threading
import time

import cv2
from streamlit_webrtc import VideoProcessorBase

from modules.expression_model import FacialExpressionClassifier


class FaceDetectionProcessor(VideoProcessorBase):
    """Detect face presence for demo login and estimate expressions after login."""

    REQUIRED_DETECTION_SECONDS = 3.0
    LOST_FACE_GRACE_SECONDS = 1.25
    EXPRESSION_EVERY_N_FRAMES = 5

    def __init__(self):
        self._lock = threading.Lock()
        self._face_detected = False
        self._face_count = 0
        self._first_seen_at = None
        self._last_seen_at = None
        self._login_ready = False
        self._expression_enabled = False
        self._expression_label = "Waiting"
        self._expression_confidence = 0.0
        self._expression_status = "disabled"
        self._frame_number = 0
        self._classifier = FacialExpressionClassifier()
        self._cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )

    def set_expression_enabled(self, enabled):
        """Enable expression estimation only after the user has logged in."""
        with self._lock:
            self._expression_enabled = bool(enabled)
            if not enabled:
                self._expression_label = "Waiting"
                self._expression_confidence = 0.0
                self._expression_status = "disabled"

    @property
    def face_status(self):
        """Return a thread-safe snapshot of login and expression status."""
        now = time.monotonic()
        with self._lock:
            if (
                not self._login_ready
                and self._last_seen_at is not None
                and now - self._last_seen_at > self.LOST_FACE_GRACE_SECONDS
            ):
                self._first_seen_at = None
                self._last_seen_at = None

            if self._login_ready:
                elapsed = self.REQUIRED_DETECTION_SECONDS
            elif self._first_seen_at is not None and self._last_seen_at is not None:
                elapsed = max(0.0, self._last_seen_at - self._first_seen_at)
            else:
                elapsed = 0.0

            return (
                self._face_detected,
                self._face_count,
                self._login_ready,
                elapsed,
                self._expression_label,
                self._expression_confidence,
                self._expression_status,
            )

    def recv(self, frame):
        image = frame.to_ndarray(format="bgr24")
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = self._cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(70, 70),
        )

        now = time.monotonic()
        with self._lock:
            self._face_detected = len(faces) > 0
            self._face_count = len(faces)

            if len(faces) > 0:
                if self._first_seen_at is None:
                    self._first_seen_at = now
                self._last_seen_at = now

                # Once the three-second check passes, it remains passed for
                # this camera session even if later frames miss the face.
                if now - self._first_seen_at >= self.REQUIRED_DETECTION_SECONDS:
                    self._login_ready = True

            elif (
                not self._login_ready
                and self._last_seen_at is not None
                and now - self._last_seen_at > self.LOST_FACE_GRACE_SECONDS
            ):
                self._first_seen_at = None
                self._last_seen_at = None

            expression_enabled = self._expression_enabled

        if len(faces) > 0:
            # Use the largest detected face for the live expression estimate.
            x, y, w, h = max(faces, key=lambda box: box[2] * box[3])
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 220, 120), 2)
            cv2.putText(
                image,
                "FACE DETECTED",
                (x, max(25, y - 10)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (0, 220, 120),
                2,
            )

            if expression_enabled:
                self._frame_number += 1
                if self._frame_number % self.EXPRESSION_EVERY_N_FRAMES == 0:
                    try:
                        label, confidence = self._classifier.predict(gray[y:y + h, x:x + w])
                        with self._lock:
                            self._expression_label = label
                            self._expression_confidence = confidence
                            self._expression_status = "ready"
                    except Exception as exc:
                        with self._lock:
                            self._expression_status = f"error:{type(exc).__name__}"
                with self._lock:
                    label = self._expression_label
                    status = self._expression_status
                if status == "ready":
                    cv2.putText(
                        image,
                        f"Expression estimate: {label}",
                        (x, min(image.shape[0] - 10, y + h + 25)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.55,
                        (255, 220, 0),
                        2,
                    )
            else:
                with self._lock:
                    self._expression_status = "disabled"
        elif expression_enabled:
            with self._lock:
                self._expression_status = "waiting_for_face"
                self._expression_label = "Waiting"
                self._expression_confidence = 0.0

        return frame.from_ndarray(image, format="bgr24")
