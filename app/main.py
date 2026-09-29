import os

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")

import logging
import time
import uuid
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app import config, service
from app.schemas import (
    DetectorName, ErrorResponse, FaceArea, HealthResponse,
    ModelName, VerifyBase64Request, VerifyResponse,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("face-verify")

ERROR_RESPONSES = {
    400: {"model": ErrorResponse},
    413: {"model": ErrorResponse},
    422: {"model": ErrorResponse},
    500: {"model": ErrorResponse},
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    service.warmup()
    yield


app = FastAPI(
    title="Face Verify API",
    version="1.0.0",
    description="Checks whether two face images show the same person (DeepFace).",
    lifespan=lifespan,
)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request.state.request_id = uuid.uuid4().hex
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    return response


def _error(request: Request, status: int, code: str, message: str) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    return JSONResponse(
        status_code=status,
        content={"error": {"code": code, "message": message, "request_id": request_id}},
    )


@app.exception_handler(service.APIError)
async def api_error_handler(request: Request, exc: service.APIError):
    return _error(request, exc.status_code, exc.code, exc.message)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    message = "; ".join(
        f"{'.'.join(str(p) for p in err['loc'])}: {err['msg']}" for err in exc.errors()
    )
    return _error(request, 422, "INVALID_REQUEST", message)


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error")
    return _error(request, 500, "INTERNAL_ERROR", "Unexpected server error")


def _run_verify(request: Request, img1, img2, model: str, detector: str, threshold) -> VerifyResponse:
    start = time.perf_counter()
    r = service.verify(img1, img2, model, detector, threshold)
    areas = r.get("facial_areas", {})
    return VerifyResponse(
        request_id=request.state.request_id,
        same_person=bool(r["verified"]),
        distance=round(float(r["distance"]), 4),
        threshold=float(r["threshold"]),
        confidence=float(r["confidence"]) if r.get("confidence") is not None else None,
        model=model,
        detector=detector,
        distance_metric=config.DISTANCE_METRIC,
        face_areas={
            name: FaceArea(x=int(a["x"]), y=int(a["y"]), w=int(a["w"]), h=int(a["h"]))
            for name, a in (("image1", areas.get("img1")), ("image2", areas.get("img2")))
            if a
        },
        processing_time_ms=int((time.perf_counter() - start) * 1000),
    )


@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(status="ok", model=config.MODEL_NAME, detector=config.DETECTOR_BACKEND)


@app.post("/v1/verify", response_model=VerifyResponse, responses=ERROR_RESPONSES)
def verify_upload(
    request: Request,
    image1: UploadFile = File(..., description="First face image (JPEG/PNG)"),
    image2: UploadFile = File(..., description="Second face image (JPEG/PNG)"),
    model: ModelName = Form(config.MODEL_NAME),
    detector: DetectorName = Form(config.DETECTOR_BACKEND),
    threshold: Optional[float] = Form(None, gt=0, le=2),
):
    img1 = service.decode_image(image1.file.read(config.MAX_IMAGE_BYTES + 1), "image1")
    img2 = service.decode_image(image2.file.read(config.MAX_IMAGE_BYTES + 1), "image2")
    return _run_verify(request, img1, img2, model, detector, threshold)


@app.post("/v1/verify/base64", response_model=VerifyResponse, responses=ERROR_RESPONSES)
def verify_base64(request: Request, body: VerifyBase64Request):
    img1 = service.decode_image(service.decode_base64(body.image1, "image1"), "image1")
    img2 = service.decode_image(service.decode_base64(body.image2, "image2"), "image2")
    return _run_verify(request, img1, img2, body.model, body.detector, body.threshold)


# uvicorn app.main:app --host 0.0.0.0 --port 8000