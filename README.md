# IAM Policy Classifier

**AI-powered AWS IAM policy security analyzer with real-time classification, risk scoring, and compliance reporting**

![Python 3.11](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?logo=typescript&logoColor=white)
![AWS ECS](https://img.shields.io/badge/AWS-ECS%20Fargate-FF9900?logo=amazonaws&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

---

## Live Demo

**URL:** http://iam-classifier-alb-330518746.us-east-1.elb.amazonaws.com

> **Note:** Spin up required before use — see [Managing Infrastructure](#managing-infrastructure) below.

Paste any AWS IAM policy JSON into the analyzer and get an instant security assessment: a risk category, a 0–100 risk score, a confidence rating, a plain-English explanation of the findings, and concrete remediation recommendations. Analyze policies one at a time or upload a ZIP of up to 10 policies for batch processing. Every result is saved to your history for later review or PDF export.

---

## Key Features

- **AI-powered classification** — uses Anthropic Claude and OpenAI GPT-4 with automatic fallback between providers
- **Four risk categories** — Compliant, Needs Review, Overly Permissive, and Insecure, each with a confidence score
- **Batch analysis** — analyze up to 10 policies simultaneously via ZIP file upload
- **PDF export** — download a formatted batch results report in one click
- **Persistent history** — every analysis is stored in DynamoDB and browsable across sessions
- **Production deployment** — containerized on AWS ECS Fargate behind an Application Load Balancer
- **Structured observability** — JSON-formatted logs, `X-Request-ID` tracing, and rate limiting built in

---

## Architecture

```
                            ┌─────────────────────────────────┐
                            │                                 │
                            │         AWS ECS Fargate         │──► Anthropic API
 Browser ──► ALB ─────────► │         nginx (React SPA)       │──► OpenAI API
                            │         FastAPI (uvicorn)       │──► DynamoDB
                            │                                 │
                            └─────────────────────────────────┘
                                            │
                                    CloudWatch Logs
```

### Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS |
| Backend | Python 3.11, FastAPI, Uvicorn, Pydantic v2 |
| AI / ML | Anthropic Claude (primary), OpenAI GPT-4 (fallback) |
| Database | AWS DynamoDB (analysis history) |
| Infrastructure | AWS ECS Fargate, ALB, ECR, CloudWatch |
| CI / CD | GitHub Actions (test → build → push → deploy) |
| Containerization | Docker, Docker Compose |

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker Desktop (for Docker workflow)
- An Anthropic and/or OpenAI API key

### Clone and Set Up

```powershell
git clone https://github.com/amitco96/iam-policy-classifier.git
cd iam-policy-classifier
```

### Environment Variables

```powershell
Copy-Item .env.example .env
# Open .env and fill in your API keys
```

Required variables:

```env
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...        # optional — used as fallback
ENVIRONMENT=development
LOG_LEVEL=INFO
API_RATE_LIMIT=10
```

### Running Locally (without Docker)

```powershell
# Backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn src.api.main:app --reload
# API docs: http://localhost:8000/docs

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
# UI: http://localhost:5173
```

### Running with Docker

```powershell
docker compose up --build
```

| Service | URL |
|---|---|
| React UI | http://localhost |
| FastAPI + Swagger | http://localhost:8000/docs |

```powershell
# Stop
docker compose down
```

---

## Managing Infrastructure

The production stack runs on AWS ECS Fargate. Scale it up before a demo, down after to avoid idle costs (~$1–3/day when running).

**Prerequisites:** AWS CLI configured (`aws configure`), Docker Desktop

```powershell
# Spin up (before a demo or interview)
.\infra\manage.ps1 up

# Spin down (after — stops billing)
.\infra\manage.ps1 down
```

```bash
# Linux / macOS
./infra/manage.sh up
./infra/manage.sh down
```

**CI/CD:** Every `git push` to `main` automatically runs the full test suite and redeploys to ECS via GitHub Actions (`.github/workflows/deploy.yml`). No manual steps needed after initial infrastructure setup.

---

## Testing

```powershell
pytest tests/ -v
```

**87 tests, 0 failures** across three suites:

| Suite | Coverage |
|---|---|
| `tests/test_classification_service.py` | ClassificationService unit tests |
| `tests/test_api.py` | FastAPI endpoint integration tests |
| `tests/test_classifier.py` | Core classification logic |

---

## Project Structure

```
iam-policy-classifier/
├── src/                        # Backend (Python / FastAPI)
│   ├── api/
│   │   ├── main.py            # App init, middleware, lifespan
│   │   ├── middleware/        # Request logging, X-Request-ID
│   │   └── routes/
│   │       ├── classify.py    # POST /classify, POST /classify/batch
│   │       └── history.py     # GET /history
│   ├── core/
│   │   ├── classifier.py      # ClassificationService (Claude + GPT-4)
│   │   └── prompts.py         # LLM prompt templates
│   ├── models/
│   │   └── schemas.py         # Pydantic request/response models
│   ├── config/
│   │   └── settings.py        # Pydantic BaseSettings, env validation
│   └── utils/
│       └── logging.py         # JSON logging, setup_logging()
├── frontend/                   # Frontend (React / TypeScript)
│   └── src/
│       ├── pages/             # ClassifyPage, BatchPage, HistoryPage
│       ├── components/        # Sidebar, ResultCard
│       ├── types/             # TypeScript interfaces
│       └── utils/             # API client, session helpers
├── tests/                      # Pytest test suites (87 tests)
├── infra/                      # AWS infrastructure scripts
│   ├── manage.ps1             # Windows spin-up/down script
│   ├── manage.sh              # Linux/macOS spin-up/down script
│   └── ecs-task-definition.json
├── .github/workflows/          # GitHub Actions CI/CD
│   ├── deploy.yml             # Test → build → push ECR → deploy ECS
│   └── pr-check.yml           # PR validation
├── Dockerfile                  # Backend container
├── frontend/Dockerfile         # Frontend container (nginx)
├── docker-compose.yml          # Local full-stack setup
├── requirements.txt            # Pinned Python dependencies
└── .env.example               # Environment variable template
```

---

## Cost

The entire project — from prototype to production deployment with CI/CD — cost under $30.

| Item | Cost |
|------|------|
| Anthropic API (development + testing) | ~$25.67 |
| AWS infrastructure (ECS, ALB, ECR, DynamoDB) | ~$0.33 |
| **Total** | **~$26** |

API costs were the majority — Claude Sonnet was used for all classification calls during development and testing. Production running cost is ~$1–3/day when live (ECS Fargate + ALB), $0 when scaled down.

---

## License

MIT License — see [LICENSE](LICENSE).
