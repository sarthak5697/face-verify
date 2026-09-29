import os

MODEL_NAME = os.getenv("FACE_MODEL", "ArcFace")
DETECTOR_BACKEND = os.getenv("FACE_DETECTOR", "retinaface")
DISTANCE_METRIC = "cosine"
MAX_IMAGE_BYTES = int(os.getenv("MAX_IMAGE_MB", "10")) * 1024 * 1024