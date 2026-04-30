import base64
import io
import uuid
from typing import List

import cv2
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from ultralytics import YOLO
from PIL import Image

# Initialize FastAPI app
app = FastAPI(title="Wildfire Detection API")

# Load YOLO model
# Using fire-models/fire_m.pt as identified in the research phase
MODEL_PATH = "fire-models/fire_m.pt"
model = YOLO(MODEL_PATH)

# Request Schema
class InferenceRequest(BaseModel):
    uuid: str = Field(..., description="Unique identifier for the request")
    image: str = Field(..., description="Base64 encoded image string")

# Response Schema for /api/predict
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

# Response Schema for /api/annotate
class AnnotationResponse(BaseModel):
    uuid: str
    annotated_image: str  # Base64 encoded

def decode_image(base64_string: str) -> np.ndarray:
    try:
        # Remove metadata prefix if present (e.g., "data:image/jpeg;base64,")
        if "," in base64_string:
            base64_string = base64_string.split(",")[1]
        
        img_data = base64.b64decode(base64_string)
        img_array = np.frombuffer(img_data, np.uint8)
        image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError("Could not decode image")
        return image
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image data: {str(e)}")

def encode_image(image: np.ndarray) -> str:
    _, buffer = cv2.imencode('.jpg', image)
    base64_string = base64.b64encode(buffer).decode('utf-8')
    return base64_string

@app.post("/api/predict", response_model=PredictionResponse)
def predict(request: InferenceRequest):
    """
    Perform object detection and return structured JSON results.
    Note: Using 'def' instead of 'async def' allows FastAPI to run this blocking 
    ML task in a separate thread pool, preventing it from blocking the event loop.
    """
    image = decode_image(request.image)
    
    # Perform inference
    results = model.predict(image, device='cpu')  # device='cpu' for safety in restricted envs
    result = results[0]
    
    detections = []
    boxes = []
    
    # Extract results
    names = result.names
    for box in result.boxes:
        cls_id = int(box.cls[0])
        label = names[cls_id]
        conf = float(box.conf[0])
        
        # Get coordinates (xywh)
        # Note: box.xywh returns [x_center, y_center, width, height]
        # Request format usually expects x, y as top-left or specified. 
        # Here we provide center-based or convert to top-left if standard.
        # Ultralytics xywh is [x_center, y_center, width, height]
        # Let's provide top-left (x, y) as it's more common for "x, y, width, height"
        xyxy = box.xyxy[0].tolist()
        x1, y1, x2, y2 = xyxy
        
        detections.append(label)
        boxes.append(DetectionBox(
            x=x1,
            y=y1,
            width=x2 - x1,
            height=y2 - y1,
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
def annotate(request: InferenceRequest):
    """
    Perform object detection and return the annotated image as base64.
    """
    image = decode_image(request.image)
    
    # Perform inference
    results = model.predict(image, device='cpu')
    result = results[0]
    
    # Use Ultralytics plotting utility
    annotated_frame = result.plot()
    
    # Encode back to base64
    base64_annotated = encode_image(annotated_frame)
    
    return AnnotationResponse(
        uuid=request.uuid,
        annotated_image=base64_annotated
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
