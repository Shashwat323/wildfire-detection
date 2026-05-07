Made for use with Google Cloud Platform.

Need an existing bucket and add the following files:
fire-models/fire_m.pt
main.py
requirements.txt
Dockerfile

Navigate to the terraform/ directory and run the following commands:
terraform init
terraform apply -var="project_id=YOUR_PROJECT_ID" -var="region=REGION" -var="zone=ZONE" -var="bucket=BUCKET"

The output will be the public IPv4 address.

Wait a few minutes while the docker image builds and runs.

In a browser navigate to http://<EXTERNAL IPv4 ADDRESS>:8000

Use /api/health to check is the API is online.
METHOD: GET

Use /api/predict to predict the elements in an image.
METHOD: POST
Input:

JSON {​
"uuid": UNIQUE IDENTIFIER,​
"image":BASE64 ENCODED IMAGE​
}

Output:

JSON {​
"uuid": UNIQUE IDENTIFIER,​
"count": NUMBER OF OBJECTS DETECTED,​
"detections":LIST OF OBJECTS DETECTED,
"boxes":LIST OF LOCATIONS OF OBJECTS x,y,w,h,c WHERE:
        (x,y) IS THE CENTRE OF THE DETECTED OBJECT,
        w IS THE WIDTH OF THE RECTANGLE,
        h IS THE ​HEIGHT OF THE RECTANGLE, AND
        c IS THE CONFIDENCE LEVEL
"speed_preprocess_ms": TIME TAKEN FOR PREPROCESSING,​
"speed_inference_ms": TIME TAKEN TO PREDICT,​
"speed_postprocess_ms": TIME TAKEN TO PROCESS THE OUTPUT​
}​


Use /api/annotate to get the annotated image.
METHOD: POST
Input:

JSON {​
"uuid": UNIQUE IDENTIFIER,​
"image":BASE64 ENCODED IMAGE​
}

Output:

JSON {​
"uuid": UNIQUE IDENTIFIER,​
"image":BASE64 ENCODED IMAGE​ WITH BOXES
}