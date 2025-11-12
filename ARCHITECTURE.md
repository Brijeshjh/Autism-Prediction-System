# Deployment Architecture & Flow

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Local Development                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ best_model   │  │ encoders.pkl │  │  train.csv   │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│         │                 │                  │               │
│         └─────────────────┼──────────────────┘               │
│                           ↓                                  │
│                    ┌──────────────┐                          │
│                    │   app.py     │ (FastAPI)               │
│                    │ (localhost)  │                          │
│                    └──────────────┘                          │
│                           │                                  │
│         ┌─────────────────┴─────────────────┐               │
│         ↓                                   ↓                │
│    ┌─────────┐                        ┌──────────┐          │
│    │ Docker  │                        │Streamlit │          │
│    │ Build   │                        │(Frontend)│          │
│    └────┬────┘                        └──────────┘          │
│         │                                   │                │
└─────────┼───────────────────────────────────┼────────────────┘
          ↓                                   │
┌─────────────────────────────────────────────┼────────────────┐
│              Google Cloud Platform           │                │
│                                              │                │
│  ┌──────────────────────────────────────┐   │                │
│  │      Artifact Registry                │   │                │
│  │  (Docker Image Repository)            │   │                │
│  │                                      │   │                │
│  │  🐳 autism-prediction-api:latest    │   │                │
│  └────────────────┬─────────────────────┘   │                │
│                   │                         │                │
│                   ↓                         ↓                │
│  ┌──────────────────────────────────────┐  ┌──────────────┐  │
│  │          Cloud Run Service           │  │   Streamlit  │  │
│  │  (Managed Serverless Container)      │  │   Frontend   │  │
│  │                                      │  │   (Optional) │  │
│  │  ✓ FastAPI App                      │  └──────┬───────┘  │
│  │  ✓ Auto-scaling                     │         │          │
│  │  ✓ Load balancing                   │         │          │
│  │  ✓ Public HTTPS URL                 │         │          │
│  └────────────────┬─────────────────────┘         │          │
│                   │                               │          │
│                   └───────────────┬───────────────┘          │
│                                   ↓                          │
│                  ┌────────────────────────────┐              │
│                  │  https://your-api.run.app  │              │
│                  │      (Public Endpoint)     │              │
│                  └────────────────────────────┘              │
└──────────────────────────────────────────────────────────────┘
                           ↑
                           │
                    ┌──────────────┐
                    │   Browser /  │
                    │   Client App │
                    └──────────────┘
```

## Deployment Flow

```
Step 1: Prepare
┌─────────────────────────────────────┐
│ - Google Cloud Account              │
│ - Google Cloud SDK installed        │
│ - Docker installed                  │
│ - Project authenticated             │
└────────────┬────────────────────────┘
             ↓
Step 2: Build Docker Image
┌─────────────────────────────────────┐
│ docker build -t $imageUri .         │
│                                     │
│ Creates container with:             │
│ - Your ML model                     │
│ - FastAPI application               │
│ - All dependencies                  │
└────────────┬────────────────────────┘
             ↓
Step 3: Push to Artifact Registry
┌─────────────────────────────────────┐
│ docker push $imageUri               │
│                                     │
│ Uploads to:                         │
│ us-central1-docker.pkg.dev/         │
│  $projectId/repo/image:latest       │
└────────────┬────────────────────────┘
             ↓
Step 4: Deploy to Cloud Run
┌─────────────────────────────────────┐
│ gcloud run deploy autism-prediction │
│                                     │
│ Sets up:                            │
│ - Service account                   │
│ - Load balancer                     │
│ - Public HTTPS endpoint             │
│ - Auto-scaling                      │
└────────────┬────────────────────────┘
             ↓
Step 5: Get URL & Test
┌─────────────────────────────────────┐
│ https://autism-prediction-api-...   │
│         .run.app                    │
│                                     │
│ API is now live! 🎉                 │
└─────────────────────────────────────┘
```

## Request Flow (Runtime)

```
User Input (Streamlit)
      │
      ↓
┌─────────────────────────────────┐
│  Package Data as JSON           │
│  {                              │
│    "A1_Score": 1,              │
│    "A2_Score": 1,              │
│    ...                         │
│  }                              │
└────────────┬────────────────────┘
             │
             ↓
    HTTPS Request to Cloud Run
  POST /predict HTTP/1.1
  Host: your-api.run.app
  Content-Type: application/json
  
  {...payload...}
             │
             ↓
┌─────────────────────────────────┐
│   Cloud Run Service             │
│   (Receives request)            │
└────────────┬────────────────────┘
             │
             ↓
┌─────────────────────────────────┐
│   FastAPI Router                │
│   (Routes to /predict)          │
└────────────┬────────────────────┘
             │
             ↓
┌─────────────────────────────────┐
│   Data Preprocessing            │
│   - Encoding                    │
│   - Scaling                     │
│   - Validation                  │
└────────────┬────────────────────┘
             │
             ↓
┌─────────────────────────────────┐
│   ML Model Prediction           │
│   (best_model.pkl)              │
│   - Input: processed features   │
│   - Output: 0 or 1              │
└────────────┬────────────────────┘
             │
             ↓
┌─────────────────────────────────┐
│   Format Response               │
│   {                             │
│     "prediction": "Yes ASD",   │
│     "prediction_code": 1       │
│   }                             │
└────────────┬────────────────────┘
             │
             ↓
    HTTPS Response (200 OK)
  Content-Type: application/json
  
  {...response...}
             │
             ↓
User sees result in Streamlit ✓
```

## File Organization

```
Your Project Directory
│
├── 📄 app.py                      ← FastAPI application
├── 📄 stream_app.py               ← Streamlit frontend
├── 📦 best_model.pkl              ← ML model
├── 📦 encoders.pkl                ← Feature encoders
├── 📊 train.csv                   ← Training data
│
├── 🐳 Dockerfile                  ← Container definition (NEW)
├── .dockerignore                  ← Docker optimization (NEW)
│
├── 📄 requirements.txt             ← Base dependencies
├── 📄 requirements-gcp.txt         ← GCP dependencies (NEW)
│
├── 🚀 deploy.ps1                  ← Automated deployment (NEW)
├── 📄 deploy_vertex_ai.py         ← Advanced deployment (NEW)
│
├── 📚 QUICKSTART_DEPLOYMENT.md    ← 5-min guide (NEW)
├── 📚 VERTEX_AI_DEPLOYMENT.md     ← Full guide (NEW)
├── 📚 DEPLOYMENT_SETUP.md         ← Overview (NEW)
│
└── Myenv/                         ← Virtual environment
```

## Technology Stack

```
┌────────────────────────────────────────────────────┐
│              Local Development Stack                │
├────────────────────────────────────────────────────┤
│  • Python 3.11                                     │
│  • FastAPI (API framework)                         │
│  • Uvicorn (ASGI server)                           │
│  • Scikit-learn (ML model)                         │
│  • Pandas/NumPy (Data processing)                  │
│  • Streamlit (Frontend)                            │
└────────────────────────────────────────────────────┘
                          ↓
┌────────────────────────────────────────────────────┐
│               Containerization Layer                │
├────────────────────────────────────────────────────┤
│  • Docker (Container runtime)                      │
│  • Python 3.11 slim image                          │
│  • Multi-layer optimization                        │
└────────────────────────────────────────────────────┘
                          ↓
┌────────────────────────────────────────────────────┐
│            Google Cloud Platform Stack              │
├────────────────────────────────────────────────────┤
│  • Artifact Registry (Container storage)           │
│  • Cloud Run (Serverless compute)                  │
│  • Cloud Build (CI/CD)                             │
│  • Cloud Logging (Monitoring)                      │
│  • Cloud Trace (Performance)                       │
│  • Vertex AI (ML platform - optional)              │
└────────────────────────────────────────────────────┘
```

## Scaling & Performance

```
Single Request (< 1 second)
User Request → Cloud Run Container → Response
             |
             └─→ Auto-scaled to 1 instance

Multiple Requests (Peak Traffic)
Request 1 → Instance 1 ┐
Request 2 → Instance 2 ├─→ Load Balanced
Request 3 → Instance 3 │
Request 4 → Instance 4 ┘
             |
             └─→ Auto-scales to N instances
                (up to 1000 concurrent by default)
```

## Cost Breakdown (Monthly Example)

```
100,000 Requests per Month:

Compute: 100k × 0.00005 USD (per request) = $5
Memory:  100k × 512MB × 0.0000041 USD     = $0.41
Storage: ~500MB in registry               = $0.50
                                      ────────────
                          Total = ~$5.91/month

First 2 million requests/month are FREE!
Plus $0 while idle! (Cost only when processing)
```
