import base64
from typing import List
import uvicorn
import cv2
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from ultralytics import YOLO

app = FastAPI(title="Wildfire Detection API")

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

def predict_image(imagestr: str):
    image = decode_image(imagestr)
    return model.predict(image, device='cpu')[0]

@app.get('/api/health')
async def public():
    return {"message": "The wildfire-detection API is alive."}

@app.post("/api/predict", response_model=PredictionResponse)
def predict(request: InferenceRequest):
    result = predict_image(request.image)
    
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
def annotate(request: InferenceRequest):
    result = predict_image(request.image)
    
    annotated_frame = result.plot()
    
    base64_annotated = encode_image(annotated_frame)
    
    return AnnotationResponse(
        uuid=request.uuid,
        annotated_image=base64_annotated
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)