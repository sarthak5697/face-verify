import base64
import binascii
import logging
import threading

import cv2
import numpy as np
from deepface import DeepFace

from app import config

logger = logging.getLogger(__name__)

# TensorFlow models aren't reliably thread-safe; run one verification at a time.
_lock = threading.Lock()


class APIError(Exception):
    def __init__(self, status_code: int, code: str, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


def decode_base64(data: str, name: str) -> bytes:
    if data.startswith("data:"):
        data = data.split(",", 1)[-1]
    try:
        return base64.b64decode(data, validate=True)
    except (binascii.Error, ValueError):
        raise APIError(400, "INVALID_IMAGE", f"{name} is not valid base64")


def decode_image(data: bytes, name: str) -> np.ndarray:
    if not data:
        raise APIError(400, "INVALID_IMAGE", f"{name} is empty")
    if len(data) > config.MAX_IMAGE_BYTES:
        raise APIError(413, "IMAGE_TOO_LARGE", f"{name} exceeds {config.MAX_IMAGE_BYTES // (1024 * 1024)} MB")
    img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise APIError(400, "INVALID_IMAGE", f"{name} is not a readable image (use JPEG or PNG)")
    return img


def warmup() -> None:
    """Load the default model and detector at startup so the first request isn't slow."""
    logger.info("Warming up %s + %s ...", config.MODEL_NAME, config.DETECTOR_BACKEND)
    blank = np.zeros((224, 224, 3), dtype=np.uint8)
    try:
        DeepFace.verify(
            blank, blank,
            model_name=config.MODEL_NAME,
            detector_backend=config.DETECTOR_BACKEND,
            enforce_detection=False,
        )
        logger.info("Warmup complete")
    except Exception:
        logger.exception("Warmup failed; models will load on first request")


def verify(img1: np.ndarray, img2: np.ndarray, model: str, detector: str, threshold) -> dict:
    with _lock:
        try:
            return DeepFace.verify(
                img1_path=img1,
                img2_path=img2,
                model_name=model,
                detector_backend=detector,
                distance_metric=config.DISTANCE_METRIC,
                threshold=threshold,
            )
        except ValueError as e:
            reason = str(e.__cause__ or e)
            if "could not be detected" in reason.lower():
                which = "image1" if "img1" in str(e) else "image2"
                raise APIError(422, "NO_FACE_DETECTED", f"No face detected in {which}")
            raise APIError(400, "PROCESSING_ERROR", reason)