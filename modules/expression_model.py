"""FER+ facial-expression estimates using OpenCV DNN.

The ONNX model is downloaded and SHA-256 verified on first use, then cached
outside the repository. Labels describe visible expression classes; they are
not psychological diagnoses.
"""
import hashlib
import os
import tempfile
import threading
import urllib.request
from pathlib import Path

import cv2
import numpy as np

MODEL_URL = "https://huggingface.co/onnxmodelzoo/emotion-ferplus-8/resolve/main/emotion-ferplus-8.onnx"
MODEL_SHA256 = "a2a2ba6a335a3b29c21acb6272f962bd3d47f84952aaffa03b60986e04efa61c"
LABELS = ("Neutral", "Happy", "Surprised", "Sad", "Angry", "Disgusted", "Fearful", "Contempt")


class FacialExpressionClassifier:
    """Load FER+ once and safely share its inference network."""

    _download_lock = threading.Lock()

    def __init__(self):
        self._net = None
        self._inference_lock = threading.Lock()

    @property
    def ready(self):
        return self._net is not None

    @classmethod
    def _model_path(cls):
        cache_dir = Path(tempfile.gettempdir()) / "cosmo-care-models"
        cache_dir.mkdir(parents=True, exist_ok=True)
        model_path = cache_dir / "emotion-ferplus-8.onnx"

        with cls._download_lock:
            if model_path.exists() and cls._sha256(model_path) == MODEL_SHA256:
                return model_path
            model_path.unlink(missing_ok=True)
            temporary_path = model_path.with_suffix(".onnx.part")
            request = urllib.request.Request(MODEL_URL, headers={"User-Agent": "CosmoCare/1.0"})
            try:
                with urllib.request.urlopen(request, timeout=90) as response:
                    with open(temporary_path, "wb") as output:
                        while True:
                            chunk = response.read(1024 * 1024)
                            if not chunk:
                                break
                            output.write(chunk)
                if cls._sha256(temporary_path) != MODEL_SHA256:
                    raise RuntimeError("Expression model failed SHA-256 verification.")
                os.replace(temporary_path, model_path)
            finally:
                temporary_path.unlink(missing_ok=True)
        return model_path

    @staticmethod
    def _sha256(path):
        digest = hashlib.sha256()
        with open(path, "rb") as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def load(self):
        """Download and initialize outside the real-time video frame callback."""
        if self._net is None:
            model_path = self._model_path()
            network = cv2.dnn.readNetFromONNX(str(model_path))
            with self._inference_lock:
                if self._net is None:
                    self._net = network

    def predict(self, face_gray):
        if not self.ready:
            raise RuntimeError("Expression model is still loading.")
        if face_gray is None or face_gray.size == 0:
            raise ValueError("No face pixels available.")

        resized = cv2.resize(face_gray, (64, 64), interpolation=cv2.INTER_AREA)
        blob = cv2.dnn.blobFromImage(
            resized, scalefactor=1.0, size=(64, 64),
            mean=(0.0,), swapRB=False, crop=False,
        )
        with self._inference_lock:
            self._net.setInput(blob)
            scores = np.asarray(self._net.forward(), dtype=np.float64).reshape(-1)

        if scores.size != len(LABELS):
            raise RuntimeError("Expression model returned an unexpected output shape.")
        scores -= np.max(scores)
        probabilities = np.exp(scores)
        probabilities /= np.sum(probabilities)
        index = int(np.argmax(probabilities))
        return LABELS[index], float(probabilities[index])
