"""
Vertex AI Deployment Helper Script
This script helps deploy the autism prediction model to Google Cloud Vertex AI
"""

import os
import sys
from google.cloud import aiplatform
from google.cloud import storage
import argparse
from datetime import datetime


def setup_vertex_ai(project_id: str, location: str = "us-central1"):
    """Initialize Vertex AI with project configuration"""
    aiplatform.init(project=project_id, location=location)
    print(f"✓ Vertex AI initialized for project: {project_id} in {location}")


def create_bucket(project_id: str, bucket_name: str, location: str = "us-central1"):
    """Create a Cloud Storage bucket for model artifacts"""
    try:
        storage_client = storage.Client(project=project_id)
        bucket = storage_client.create_bucket(bucket_name, location=location)
        print(f"✓ Created Cloud Storage bucket: {bucket_name}")
        return bucket
    except Exception as e:
        if "already exists" in str(e):
            print(f"✓ Bucket {bucket_name} already exists")
        else:
            print(f"✗ Error creating bucket: {e}")
            raise


def upload_model_artifacts(bucket_name: str, local_path: str = "."):
    """Upload model files to Cloud Storage"""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    
    files_to_upload = [
        "best_model.pkl",
        "encoders.pkl",
        "train.csv",
        "app.py",
        "requirements.txt"
    ]
    
    for file_name in files_to_upload:
        file_path = os.path.join(local_path, file_name)
        if os.path.exists(file_path):
            blob = bucket.blob(file_name)
            blob.upload_from_filename(file_path)
            print(f"✓ Uploaded {file_name} to gs://{bucket_name}/")
        else:
            print(f"⚠ File not found: {file_name}")


def deploy_to_cloud_run(project_id: str, image_uri: str, service_name: str = "autism-prediction-api"):
    """Deploy Docker image to Cloud Run"""
    import subprocess
    
    location = "us-central1"
    
    command = [
        "gcloud", "run", "deploy", service_name,
        "--image", image_uri,
        "--platform", "managed",
        "--region", location,
        "--allow-unauthenticated",
        "--memory", "2Gi",
        "--cpu", "2",
        "--port", "8000",
        "--project", project_id
    ]
    
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        print(f"✓ Cloud Run service deployed: {service_name}")
        print("\nService URL:")
        # Extract the URL from output
        for line in result.stdout.split('\n'):
            if 'https://' in line:
                print(f"  {line.strip()}")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"✗ Error deploying to Cloud Run: {e.stderr}")
        raise


def create_custom_job(project_id: str, display_name: str, container_uri: str, 
                      location: str = "us-central1"):
    """Create a custom training job in Vertex AI"""
    job = aiplatform.CustomContainerTrainingJob(
        display_name=display_name,
        container_uri=container_uri,
        project=project_id,
        location=location
    )
    
    print(f"✓ Custom training job created: {display_name}")
    return job


def deploy_model_endpoint(project_id: str, image_uri: str, display_name: str,
                         machine_type: str = "n1-standard-4",
                         location: str = "us-central1"):
    """Deploy model to Vertex AI endpoint for online predictions"""
    
    # Create a Model resource
    model = aiplatform.Model.upload(
        display_name=display_name,
        artifact_uri="gs://your-bucket/model",  # Update with actual path
        serving_container_image_uri=image_uri,
        serving_container_ports=[8000],
        project=project_id,
        location=location
    )
    
    print(f"✓ Model uploaded: {model.display_name}")
    
    # Create endpoint
    endpoint = model.deploy(
        machine_type=machine_type,
        accelerator_type="NVIDIA_TESLA_T4",
        accelerator_count=0,  # Set to 1 if you want GPU
    )
    
    print(f"✓ Model deployed to endpoint: {endpoint.display_name}")
    return endpoint


def test_endpoint(endpoint_url: str, test_data: dict):
    """Test the deployed endpoint"""
    import requests
    import json
    
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(endpoint_url, json=test_data, headers=headers, timeout=10)
        if response.status_code == 200:
            print(f"✓ Endpoint test successful!")
            print(f"  Response: {json.dumps(response.json(), indent=2)}")
            return response.json()
        else:
            print(f"✗ Endpoint returned status {response.status_code}")
            print(f"  Response: {response.text}")
    except Exception as e:
        print(f"✗ Error testing endpoint: {e}")


def main():
    parser = argparse.ArgumentParser(description="Deploy Autism Prediction Model to Vertex AI")
    parser.add_argument("--project-id", required=True, help="Google Cloud Project ID")
    parser.add_argument("--image-uri", required=True, help="Docker image URI from Artifact Registry")
    parser.add_argument("--bucket-name", help="Cloud Storage bucket name (optional)")
    parser.add_argument("--deploy-cloud-run", action="store_true", help="Deploy to Cloud Run")
    parser.add_argument("--deploy-endpoint", action="store_true", help="Deploy to Vertex AI endpoint")
    parser.add_argument("--location", default="us-central1", help="GCP region")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Autism Prediction Model - Vertex AI Deployment")
    print("=" * 60)
    print()
    
    # Setup
    setup_vertex_ai(args.project_id, args.location)
    print()
    
    # Create bucket if specified
    if args.bucket_name:
        try:
            create_bucket(args.project_id, args.bucket_name, args.location)
            upload_model_artifacts(args.bucket_name)
            print()
        except Exception as e:
            print(f"⚠ Skipping bucket creation: {e}")
    
    # Deploy options
    if args.deploy_cloud_run:
        print("Deploying to Cloud Run...")
        deploy_to_cloud_run(args.project_id, args.image_uri)
        print()
    
    if args.deploy_endpoint:
        print("Deploying to Vertex AI endpoint...")
        endpoint = deploy_model_endpoint(
            args.project_id,
            args.image_uri,
            "autism-prediction-model",
            location=args.location
        )
        print()
        print(f"Endpoint ID: {endpoint.name}")
    
    print("=" * 60)
    print("Deployment completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
