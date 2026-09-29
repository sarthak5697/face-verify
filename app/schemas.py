from typing import Dict, Literal, Optional

from pydantic import BaseModel, Field

from app import config

ModelName = Literal["ArcFace", "Facenet512", "Facenet", "VGG-Face"]
DetectorName = Literal["retinaface", "opencv"]


class VerifyBase64Request(BaseModel):
    image1: str = Field(..., description="Base64-encoded image (raw or data URI)")
    image2: str = Field(..., description="Base64-encoded image (raw or data URI)")
    model: ModelName = config.MODEL_NAME
    detector: DetectorName = config.DETECTOR_BACKEND
    threshold: Optional[float] = Field(None, gt=0, le=2, description="Override the model's default threshold")


class FaceArea(BaseModel):
    x: int
    y: int
    w: int
    h: int


class VerifyResponse(BaseModel):
    request_id: str
    same_person: bool
    distance: float
    threshold: float
    confidence: Optional[float] = None
    model: str
    detector: str
    distance_metric: str
    face_areas: Dict[str, FaceArea]
    processing_time_ms: int


class ErrorDetail(BaseModel):
    code: str
    message: str
    request_id: Optional[str] = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


class HealthResponse(BaseModel):
    status: Literal["ok"]
    model: str
    detector: str