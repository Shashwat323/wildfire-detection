import base64
import requests
import json
import os

def test_api():
    url_predict = "http://127.0.0.1:8000/api/predict"
    url_annotate = "http://127.0.0.1:8000/api/annotate"
    
    # Path to a sample image from the demo-images folder
    sample_image_path = "demo-images/image0.jpeg"
    
    if not os.path.exists(sample_image_path):
        print(f"Sample image {sample_image_path} not found.")
        return

    with open(sample_image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')

    payload = {
        "uuid": "e4b2c1d0-8d2e-11eb-8dcd-0242ac130003",
        "image": encoded_string
    }

    print("--- Testing /api/predict ---")
    try:
        response = requests.post(url_predict, json=payload)
        if response.status_code == 200:
            print("Success!")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"Failed with status code: {response.status_code}")
            print(response.text)
    except requests.exceptions.ConnectionError:
        print("Could not connect to the server. Make sure main.py is running.")

    print("\n--- Testing /api/annotate ---")
    try:
        response = requests.post(url_annotate, json=payload)
        if response.status_code == 200:
            print("Success!")
            data = response.json()
            print(f"UUID: {data['uuid']}")
            print(f"Annotated image (first 50 chars): {data['annotated_image'][:50]}...")

            with open("annotated_test.jpg", "wb") as f:
                f.write(base64.b64decode(data['annotated_image']))
            print("Saved annotated image to annotated_test.jpg")
        else:
            print(f"Failed with status code: {response.status_code}")
            print(response.text)
    except requests.exceptions.ConnectionError:
        print("Could not connect to the server. Make sure main.py is running.")

if __name__ == "__main__":
    test_api()
