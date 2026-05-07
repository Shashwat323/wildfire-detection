import base64
import requests
import json
import os
import time

def test_api(path):
    url_predict = "http://" + path + ":30080/api/predict"
    url_annotate = "http://" + path + ":30080/api/annotate"
    
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
            print(f"Annotated image: {data['annotated_image']}")
            #with open("annotated_test.jpg", "wb") as f:
            #    f.write(base64.b64decode(data['annotated_image']))
            #print("Saved annotated image to annotated_test.jpg")
        else:
            print(f"Failed with status code: {response.status_code}")
            print(response.text)
    except requests.exceptions.ConnectionError:
        print("Could not connect to the server. Make sure main.py is running.")

if __name__ == "__main__":
    path = input("External IPv4 Address: ")
    test_api(path)