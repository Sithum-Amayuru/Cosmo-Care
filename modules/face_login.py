import threading

import cv2
from streamlit_webrtc import VideoProcessorBase


class FaceDetectionProcessor(VideoProcessorBase):
    """Detect any face in browser webcam frames; does not identify people."""

    def __init__(self):
        self._lock = threading.Lock()
        self._face_detected = False
        self._face_count = 0
        self._cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )

    @property
    def face_status(self):
        with self._lock:
            return self._face_detected, self._face_count

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

        with self._lock:
            self._face_detected = len(faces) > 0
            self._face_count = len(faces)

        return frame.from_ndarray(image, format="bgr24")
