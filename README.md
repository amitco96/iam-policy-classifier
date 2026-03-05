# IAM Policy Classification Engine

AI-powered security classification engine for AWS IAM policies using multiple LLM providers (Claude, GPT).

## Overview

This engine analyzes AWS IAM policies and classifies them into security risk categories:
- ✅ **Compliant**: Follows security best practices
- ⚠️ **Needs Review**: Potential concerns requiring human review
- 🔴 **Overly Permissive**: Grants excessive permissions
- 🚨 **Insecure**: Contains critical security vulnerabilities

## Current Status

🚧 **In Development** - Converting from assignment prototype to production-ready service

### Completed
- [x] Core classification logic with multi-LLM support
- [x] Comprehensive test suite
- [x] Prompt engineering for accurate classification

### In Progress
- [ ] Production-ready API (FastAPI)
- [ ] Web dashboard
- [ ] Docker containerization
- [ ] AWS deployment
- [ ] CI/CD pipeline
- [ ] Monitoring & logging

## Running with Docker

The fastest way to run the full stack (backend + frontend) locally:

```bash
# 1. Copy the Docker env template and add your API keys
cp .env.docker.example .env
# Edit .env and set ANTHROPIC_API_KEY and/or OPENAI_API_KEY

# 2. Build and start both containers
docker-compose up --build
```

- **App (React UI):** http://localhost
- **Backend API / Swagger docs:** http://localhost:8000/docs

To stop:
```bash
docker-compose down
```

## Local Development (without Docker)
```bash
# Setup
pip install -r requirements.txt
cp .env.example .env
# Add your API keys to .env

# Run tests
pytest ai_classification_tests.py -v

# Use the classifier
python ai_classification.py
```

## Tech Stack

**Current:**
- Python 3.x
- Anthropic Claude API
- OpenAI GPT-4 API


**Planned:**
- FastAPI (REST API)
- React (Dashboard)
- PostgreSQL (Policy history)
- Docker + AWS ECS (Deployment)

## Contributing

This is a portfolio project currently under active development. Feedback and suggestions welcome!

## License

MIT
