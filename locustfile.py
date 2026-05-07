import base64
import uuid
import os
from locust import HttpUser, task

global path, url_predict, url_annotate, url_health
path = input("External IPv4 Address: ")
url_predict = "http://" + path + ":30080/api/predict"
url_annotate = "http://" + path + ":30080/api/annotate"
url_health = "http://" + path + ":30080/api/health"

class WildfireApiUser(HttpUser):
    def on_start(self):
        self.image_path = "demo-images/image0.jpeg"
        
        if self.image_path:
            with open(self.image_path, "rb") as image_file:
                self.image_bytes = image_file.read()
        else:
            print("Warning: No images found in demo-images/ directory.")
            self.image_bytes = None

    def get_payload(self):
        if not self.image_bytes:
            return None
            
        base64_image = base64.b64encode(self.image_bytes).decode('utf-8')
        return {
            "uuid": str(uuid.uuid4()),
            "image": base64_image
        }

    @task(3)
    def predict_endpoint(self):
        payload = self.get_payload()
        if payload:
            self.client.post(url_predict, json=payload, name="/api/predict")

    @task(1)
    def annotate_endpoint(self):
        payload = self.get_payload()
        if payload:
            self.client.post(url_annotate, json=payload, name="/api/annotate")

    @task(1)
    def health_check(self):
        self.client.get(url_health, name="/api/health")
