Made for use with Google Cloud Platform.

Need an existing bucket and add the following files:
fire-models/fire_m.pt
main.py
requirements.txt
Dockerfile

Navigate to the terraform/ directory and run the following commands:
terraform init
terraform apply -var="project_id=YOUR_PROJECT_ID" -var="region=REGION" -var="zone=ZONE" -var="bucket=BUCKET"