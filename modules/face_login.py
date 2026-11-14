import threading
import time

import cv2
from streamlit_webrtc import VideoProcessorBase


class FaceDetectionProcessor(VideoProcessorBase):
    """Detect face presence; this is not identity recognition."""

    REQUIRED_DETECTION_SECONDS = 3.0
    LOST_FACE_GRACE_SECONDS = 1.25

    def __init__(self):
        self._lock = threading.Lock()
        self._face_detected = False
        self._face_count = 0
        self._first_seen_at = None
        self._last_seen_at = None
        self._login_ready = False
        self._cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )

    @property
    def face_status(self):
        """Return current detection and persistent three-second login readiness."""
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

        for (x, y, w, h) in faces:
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

        now = time.monotonic()
        with self._lock:
            self._face_detected = len(faces) > 0
            self._face_count = len(faces)

            if len(faces) > 0:
                if self._first_seen_at is None:
                    self._first_seen_at = now
                self._last_seen_at = now

                # Once the three-second check passes, it stays passed for
                # this camera session even if later frames miss the face.
                if now - self._first_seen_at >= self.REQUIRED_DETECTION_SECONDS:
                    self._login_ready = True
            elif (
                not self._login_ready
                and self._last_seen_at is not None
                and now - self._last_seen_at > self.LOST_FACE_GRACE_SECONDS
            ):
                # Brief detection gaps are tolerated; longer gaps restart the check.
                self._first_seen_at = None
                self._last_seen_at = None

        return frame.from_ndarray(image, format="bgr24")
