terraform apply -var="project_id=YOUR_PROJECT_ID"

gcloud compute scp --recurse main.py Dockerfile requirements.txt fire-models/ wildfire-app-simple:~/ --zone us-central1-a

# SSH into the VM
gcloud compute ssh wildfire-app-simple --zone us-central1-a


sudo docker build -t wildfire-app .
sudo docker run -d -p 8000:8000 wildfire-app