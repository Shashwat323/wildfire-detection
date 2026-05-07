import base64
import io
from typing import List
import uvicorn
import cv2
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from ultralytics import YOLO
from fastapi.concurrency import run_in_threadpool

app = FastAPI(title="Wildfire Detection API")

# Load model once at startup
MODEL_PATH = "fire-models/fire_m.pt"
model = YOLO(MODEL_PATH)

class InferenceRequest(BaseModel):
    uuid: str
    image: str

class DetectionBox(BaseModel):
    x: float
    y: float
    width: float
    height: float
    probability: float

class PredictionResponse(BaseModel):
    uuid: str
    count: int
    detections: List[str]
    boxes: List[DetectionBox]
    speed_preprocess_ms: float
    speed_inference_ms: float
    speed_postprocess_ms: float

class AnnotationResponse(BaseModel):
    uuid: str
    annotated_image: str

def decode_image(base64_string: str) -> np.ndarray:
    try:
        if "," in base64_string:
            base64_string = base64_string.split(",")[1]

        img_data = base64.b64decode(base64_string)
        nparr = np.frombuffer(img_data, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError("Could not decode image")
        return image
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image data: {str(e)}")

def encode_image(image: np.ndarray) -> str:
    _, buffer = cv2.imencode('.jpg', image, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
    base64_string = base64.b64encode(buffer).decode('utf-8')
    return base64_string

def perform_inference(image: np.ndarray):
    return model.predict(image, device='cpu', verbose=False)[0]

@app.get('/api/health')
async def health():
    return {"status": "ok", "message": "The wildfire-detection API is alive."}

@app.post("/api/predict", response_model=PredictionResponse)
async def predict(request: InferenceRequest):
    image = await run_in_threadpool(decode_image, request.image)
    result = await run_in_threadpool(perform_inference, image)

    detections = []
    boxes = []

    for box in result.boxes:
        label = result.names[int(box.cls)]
        xywh = box.xywh[0].tolist()
        conf = float(box.conf)

        detections.append(label)
        boxes.append(DetectionBox(
            x=xywh[0],
            y=xywh[1],
            width=xywh[2],
            height=xywh[3],
            probability=conf
        ))

    return PredictionResponse(
        uuid=request.uuid,
        count=len(detections),
        detections=detections,
        boxes=boxes,
        speed_preprocess_ms=result.speed['preprocess'],
        speed_inference_ms=result.speed['inference'],
        speed_postprocess_ms=result.speed['postprocess']
    )

@app.post("/api/annotate", response_model=AnnotationResponse)
async def annotate(request: InferenceRequest):
    image = await run_in_threadpool(decode_image, request.image)
    result = await run_in_threadpool(perform_inference, image)

    annotated_frame = await run_in_threadpool(result.plot)
    base64_annotated = await run_in_threadpool(encode_image, annotated_frame)

    return AnnotationResponse(
        uuid=request.uuid,
        annotated_image=base64_annotated
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)