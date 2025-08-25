#!/bin/bash

# Grace Irvine Ministry Scheduler - Deployment Script
# This script deploys the application to Google Cloud Run

set -e

# Configuration
PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-grace-irvine-ministry}"
REGION="${GOOGLE_CLOUD_REGION:-us-central1}"
SERVICE_NAME="${CLOUD_RUN_SERVICE_NAME:-ministry-scheduler}"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "🚀 Grace Irvine Ministry Scheduler - Deployment Script"
echo "=================================================="
echo "Project ID: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo "Service Name: ${SERVICE_NAME}"
echo "Image: ${IMAGE_NAME}"
echo ""

# Check if required environment variables are set
if [[ -z "${PROJECT_ID}" ]]; then
    echo "❌ Error: GOOGLE_CLOUD_PROJECT environment variable is required"
    exit 1
fi

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ Error: gcloud CLI is not installed"
    echo "Please install gcloud CLI: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker is not installed"
    echo "Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

echo "📋 Checking prerequisites..."

# Authenticate with gcloud (if not already authenticated)
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
    echo "🔐 Authenticating with Google Cloud..."
    gcloud auth login
fi

# Set the project
echo "🔧 Setting Google Cloud project..."
gcloud config set project ${PROJECT_ID}

# Enable required APIs
echo "🔌 Enabling required Google Cloud APIs..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

# Build and push the Docker image
echo "🐳 Building Docker image..."
docker build -t ${IMAGE_NAME}:latest .

echo "📤 Pushing Docker image to Google Container Registry..."
docker push ${IMAGE_NAME}:latest

# Deploy to Cloud Run
echo "☁️ Deploying to Google Cloud Run..."

# Create .env file for Cloud Run if it doesn't exist
if [[ ! -f ".env" && -f "env.example" ]]; then
    echo "📝 Creating .env file from env.example..."
    cp env.example .env
    echo "⚠️  Please update .env file with your actual configuration"
fi

# Deploy with environment variables
gcloud run deploy ${SERVICE_NAME} \
    --image=${IMAGE_NAME}:latest \
    --platform=managed \
    --region=${REGION} \
    --allow-unauthenticated \
    --port=8080 \
    --memory=1Gi \
    --cpu=1 \
    --min-instances=0 \
    --max-instances=10 \
    --timeout=300 \
    --concurrency=100 \
    --env-vars-file=.env \
    --set-env-vars="GOOGLE_CLOUD_PROJECT=${PROJECT_ID}" \
    --set-env-vars="CLOUD_RUN_SERVICE_NAME=${SERVICE_NAME}" \
    --quiet

# Get the service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --platform=managed --region=${REGION} --format="value(status.url)")

echo ""
echo "✅ Deployment completed successfully!"
echo "🌐 Service URL: ${SERVICE_URL}"
echo "📊 Health Check: ${SERVICE_URL}/health"
echo "📚 API Documentation: ${SERVICE_URL}/docs"
echo "📅 Calendar Subscription: ${SERVICE_URL}/calendar-subscription"
echo ""
echo "🔧 Next steps:"
echo "1. Update your .env file with production values"
echo "2. Upload your Google service account JSON to configs/"
echo "3. Test the deployment by visiting ${SERVICE_URL}"
echo "4. Set up your Google Sheets with the correct ID"
echo "5. Configure notification recipients in configs/settings.yaml"
echo ""
echo "📖 For more information, see the documentation."
