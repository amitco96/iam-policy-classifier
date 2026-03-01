# IAM Policy Classification Engine - Claude Code Instructions

## Project Overview

**Name:** IAM Policy Classifier  
**Purpose:** Production-ready AI-powered security classification engine for AWS IAM policies  
**Target Users:** Security teams, DevOps engineers, compliance auditors  
**Tech Stack:** Python (FastAPI), React (TypeScript), Docker, AWS ECS  

### Business Context
This project demonstrates full-stack AI engineering capabilities for cybersecurity portfolio. It's designed to be deployed as a production SaaS application that helps organizations identify security risks in their IAM policies.

---

## Architecture Principles

### Backend (Python/FastAPI)
- **Clean Architecture:** Separate concerns into layers (API, Core, Models, Config)
- **Type Safety:** Use Pydantic for all data models and validation
- **Async-First:** Leverage async/await for I/O operations
- **Testability:** All business logic must be unit-testable with mocked dependencies
- **Observability:** Structured logging, metrics, and health checks built-in

### Frontend (React/TypeScript)
- **Component-Based:** Small, reusable, single-responsibility components
- **Type Safety:** Strict TypeScript, no `any` types
- **Responsive Design:** Mobile-first with Tailwind CSS
- **User Experience:** Loading states, error handling, accessibility

### Infrastructure
- **Containerization:** Docker for consistency across environments
- **Infrastructure as Code:** Terraform for AWS resources
- **CI/CD:** GitHub Actions for automated testing and deployment
- **Monitoring:** Prometheus metrics, CloudWatch logs

---

## Project Structure

```
iam-policy-classifier/
├── src/                        # Backend Python code
│   ├── api/                   # FastAPI application
│   │   ├── main.py           # App initialization, middleware
│   │   └── routes/           # API endpoints
│   ├── core/                  # Business logic
│   │   ├── classifier.py     # Classification service
│   │   └── prompts.py        # LLM prompt templates
│   ├── models/                # Pydantic schemas
│   │   └── schemas.py        # Request/response models
│   ├── config/                # Configuration management
│   │   └── settings.py       # Environment-based settings
│   └── utils/                 # Helper functions
│       └── logging.py        # Logging configuration
├── tests/                     # All tests
│   ├── test_classifier.py    # Core logic tests
│   ├── test_api.py           # API integration tests
│   └── conftest.py           # Pytest fixtures
├── frontend/                  # React application
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── services/         # API client
│   │   ├── types/            # TypeScript types
│   │   └── utils/            # Helper functions
│   └── public/               # Static assets
├── deploy/                    # Deployment configs
│   ├── terraform/            # IaC for AWS
│   ├── monitoring/           # Grafana, Prometheus configs
│   └── scripts/              # Deployment scripts
├── docs/                      # Documentation
├── requirements.txt           # Python dependencies (pinned)
├── Dockerfile                 # Backend container
├── docker-compose.yml         # Local development
├── .env.example              # Environment template
├── .gitignore                # Git ignore rules
├── README.md                 # Project documentation
└── CLAUDE.md                 # This file
```

---

## Coding Standards

### Python

**Style Guide:**
- Follow PEP 8
- Use Black formatter (line length: 88)
- Use isort for import sorting
- Type hints for all function signatures

**Example:**
```python
from typing import Optional
from pydantic import BaseModel

async def classify_policy(
    policy: dict,
    provider: str = "claude"
) -> ClassificationResult:
    """
    Classify an IAM policy for security risks.
    
    Args:
        policy: The IAM policy JSON document
        provider: LLM provider to use (claude, gpt4, gemini)
        
    Returns:
        ClassificationResult with category, risk score, and recommendations
        
    Raises:
        ValueError: If policy is invalid
        APIError: If LLM API call fails
    """
    # Implementation
    pass
```

**Error Handling:**
```python
# Always use specific exceptions
try:
    result = await llm_client.classify(policy)
except APIConnectionError as e:
    logger.error(f"LLM API connection failed: {e}")
    raise ServiceUnavailableError("Classification service temporarily unavailable")
except ValidationError as e:
    logger.warning(f"Invalid policy format: {e}")
    raise BadRequestError("Invalid IAM policy format")
```

**Logging:**
```python
import logging
logger = logging.getLogger(__name__)

# Structured logging with context
logger.info(
    "Policy classified",
    extra={
        "category": result.category,
        "risk_score": result.risk_score,
        "provider": provider,
        "duration_ms": duration
    }
)
```

### TypeScript/React

**Style Guide:**
- Functional components with hooks
- Props interfaces for all components
- Descriptive variable names

**Example:**
```typescript
interface PolicyInputProps {
  onAnalyze: (policy: PolicyData) => Promise<void>;
  isLoading: boolean;
}

export const PolicyInput: React.FC<PolicyInputProps> = ({ 
  onAnalyze, 
  isLoading 
}) => {
  const [policyJson, setPolicyJson] = useState<string>('');
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    try {
      const parsed = JSON.parse(policyJson);
      await onAnalyze(parsed);
    } catch (err) {
      setError('Invalid JSON format');
    }
  };

  // Component JSX
};
```

---

## Testing Requirements

### Backend Tests

**Coverage Target:** >80%

**Unit Tests:**
```python
# tests/test_classifier.py
import pytest
from unittest.mock import Mock, patch
from src.core.classifier import ClassificationService

@pytest.fixture
def classifier():
    return ClassificationService()

@pytest.mark.asyncio
async def test_classify_compliant_policy(classifier, sample_compliant_policy):
    """Test classification of a compliant IAM policy"""
    with patch('src.core.classifier.anthropic_client') as mock_client:
        mock_client.classify.return_value = {
            "category": "compliant",
            "risk_score": 15
        }
        
        result = await classifier.classify_policy(
            sample_compliant_policy,
            provider="claude"
        )
        
        assert result.category == "compliant"
        assert result.risk_score < 30
```

**Integration Tests:**
```python
# tests/test_api.py
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_classify_endpoint_success():
    """Test successful policy classification via API"""
    response = client.post(
        "/classify",
        json={
            "policy_json": {"Version": "2012-10-17", ...},
            "provider": "claude"
        }
    )
    assert response.status_code == 200
    assert "category" in response.json()
    assert "risk_score" in response.json()
```

### Frontend Tests
- Component unit tests with React Testing Library
- Integration tests for API calls
- E2E tests (optional, later phase)

---

## API Design Principles

### RESTful Conventions
- `POST /classify` - Analyze single policy
- `POST /classify/batch` - Analyze multiple policies
- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics

### Request/Response Format
```json
// POST /classify
{
  "policy_json": {
    "Version": "2012-10-17",
    "Statement": [...]
  },
  "provider": "claude"
}

// Response
{
  "category": "overly_permissive",
  "confidence": 0.92,
  "risk_score": 75,
  "explanation": "Policy grants s3:* permissions to all resources...",
  "recommendations": [
    "Restrict S3 permissions to specific buckets",
    "Remove wildcard (*) from Resource field",
    "Implement least privilege principle"
  ],
  "provider_used": "claude",
  "analyzed_at": "2026-02-15T16:30:00Z"
}
```

### Error Responses
```json
{
  "error": {
    "code": "INVALID_POLICY",
    "message": "Policy JSON is malformed",
    "details": "Expected 'Version' field to be a string"
  }
}
```

---

## Environment Configuration

### Required Environment Variables

```bash
# LLM API Keys
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...

# Application Settings
ENVIRONMENT=development  # development, staging, production
LOG_LEVEL=INFO
API_RATE_LIMIT=10  # requests per minute

# Future: Database
# DATABASE_URL=postgresql://...

# Future: Redis Cache
# REDIS_URL=redis://...
```

### Settings Management
- Use Pydantic BaseSettings for type-safe config
- Validate required settings on startup
- Different configs for dev/staging/prod
- Never commit secrets to git

---

## LLM Integration Guidelines

### Prompt Engineering
- Store prompts in `src/core/prompts.py`
- Use clear, structured prompts with examples
- Request JSON responses for structured data
- Include few-shot examples for consistency

### Multi-Provider Support
```python
# Support multiple LLM providers with fallback
providers = ["claude", "gpt4", "gemini"]

async def classify_with_fallback(policy: dict) -> ClassificationResult:
    """Try providers in order until one succeeds"""
    for provider in providers:
        try:
            return await classify_policy(policy, provider)
        except APIError:
            logger.warning(f"{provider} failed, trying next...")
            continue
    raise AllProvidersFailedError()
```

### Rate Limiting & Costs
- Implement request rate limiting
- Add caching for repeated policies
- Log token usage for cost tracking
- Set per-user/per-IP limits

---

## Security Best Practices

### API Security
- Input validation on all endpoints
- Rate limiting to prevent abuse
- CORS configuration for production
- API key authentication (future phase)
- Request size limits

### Secrets Management
- Never hardcode API keys
- Use environment variables locally
- Use AWS Secrets Manager in production
- Rotate keys regularly

### IAM Policy Handling
- Validate policy JSON structure
- Sanitize before sending to LLM
- Don't log sensitive policy details
- Implement data retention policies

---

## Performance Requirements

### Backend
- API response time: <2s for single classification
- Batch endpoint: Handle up to 10 policies concurrently
- Health check: <100ms response time
- Support 100 concurrent requests

### Frontend
- Initial load: <3s
- Time to interactive: <5s
- Smooth UI transitions (60fps)
- Optimized bundle size (<500KB)

### Database (Future)
- Query response: <100ms for history retrieval
- Support 10,000+ stored analyses

---

## Deployment Strategy

### Local Development
```bash
# Backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
uvicorn src.api.main:app --reload

# Frontend
cd frontend
npm install
npm run dev

# Full stack with Docker
docker-compose up
```

### Production Deployment
- Docker containers on AWS ECS
- Application Load Balancer for routing
- Auto-scaling based on CPU/memory
- Blue-green deployments for zero downtime
- CloudWatch for logging and monitoring

---

## Git Workflow

### Branching Strategy
- `main` - Production-ready code
- `develop` - Integration branch (optional for solo project)
- Feature branches: `feature/classification-endpoint`
- Hotfix branches: `hotfix/critical-bug`

### Commit Messages
```
feat: Add batch classification endpoint
fix: Handle empty policy JSON gracefully
docs: Update API documentation
test: Add integration tests for classifier
refactor: Extract LLM client into separate module
perf: Implement response caching
chore: Update dependencies
```

### Pre-commit Checklist
- [ ] All tests pass: `pytest -v`
- [ ] Code formatted: `black src/ tests/`
- [ ] Imports sorted: `isort src/ tests/`
- [ ] No linting errors: `flake8 src/ tests/`
- [ ] Type checking passes: `mypy src/`

---

## Common Patterns & Anti-Patterns

### ✅ DO

**Dependency Injection:**
```python
class ClassificationService:
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        
# Easy to test with mocked client
```

**Async Operations:**
```python
async def batch_classify(policies: list[dict]) -> list[ClassificationResult]:
    tasks = [classify_policy(p) for p in policies]
    return await asyncio.gather(*tasks)
```

**Structured Logging:**
```python
logger.info("Classification completed", extra={
    "request_id": request_id,
    "category": result.category,
    "duration_ms": duration
})
```

### ❌ DON'T

**Hardcoded Values:**
```python
# Bad
API_KEY = "sk-ant-..."

# Good
API_KEY = os.getenv("ANTHROPIC_API_KEY")
```

**Blocking I/O in Async Functions:**
```python
# Bad
async def classify():
    result = requests.get(url)  # Blocking!
    
# Good
async def classify():
    async with httpx.AsyncClient() as client:
        result = await client.get(url)
```

**Broad Exception Handling:**
```python
# Bad
try:
    classify(policy)
except Exception:  # Too broad!
    pass
    
# Good
try:
    classify(policy)
except (ValidationError, APIError) as e:
    logger.error(f"Classification failed: {e}")
    raise
```

---

## Documentation Requirements

### Code Documentation
- Docstrings for all public functions/classes
- Type hints for all function signatures
- Inline comments for complex logic only
- README with setup instructions

### API Documentation
- OpenAPI/Swagger auto-generated docs
- Example requests/responses
- Error codes and handling
- Rate limiting information

### Architecture Documentation
- System architecture diagram
- Data flow diagrams
- Deployment architecture
- Security considerations

---

## Future Enhancements Roadmap

### Phase 2 (Post-MVP)
- [ ] PostgreSQL database for analysis history
- [ ] User authentication and authorization
- [ ] Per-user policy history and analytics
- [ ] Redis caching layer
- [ ] Webhook notifications for high-risk policies

### Phase 3 (Advanced Features)
- [ ] Real-time policy monitoring (AWS EventBridge integration)
- [ ] Custom policy rules engine
- [ ] Multi-cloud support (Azure, GCP IAM)
- [ ] Compliance framework mapping (SOC2, HIPAA, etc.)
- [ ] API rate limiting per user tier

### Phase 4 (Enterprise)
- [ ] SSO integration (SAML, OIDC)
- [ ] Audit logging
- [ ] Role-based access control
- [ ] White-label deployment
- [ ] SLA guarantees

---

## Troubleshooting Guide

### Common Issues

**"Module not found" errors:**
```bash
# Ensure you're in project root and venv is activated
pip install -r requirements.txt
```

**"API key not found" errors:**
```bash
# Check environment variables are set
echo $ANTHROPIC_API_KEY  # Should print your key
# If empty, set it:
export ANTHROPIC_API_KEY="sk-ant-..."
```

**Tests failing:**
```bash
# Run with verbose output
pytest -v -s

# Run specific test
pytest tests/test_classifier.py::test_classify_compliant_policy -v
```

**Docker build issues:**
```bash
# Clear Docker cache and rebuild
docker-compose down -v
docker system prune -a
docker-compose up --build
```

---

## Working with Claude Code

### Effective Prompts
- Be specific about requirements
- Reference this file for context
- Ask for tests alongside implementation
- Request explanations for complex code

### Session Management
- Start each session with brief context
- Review generated code before committing
- Test changes incrementally
- Commit after each working feature

### Code Review Checklist
- [ ] Follows project structure
- [ ] Has type hints and docstrings
- [ ] Includes unit tests
- [ ] Handles errors gracefully
- [ ] Logs important events
- [ ] No hardcoded secrets

---

## Contact & Resources

**Project Repository:** https://github.com/[username]/iam-policy-classifier  
**Documentation:** https://[deployed-url]/docs  
**Issue Tracker:** GitHub Issues  

**Key Technologies:**
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Anthropic API Docs](https://docs.anthropic.com/)
- [Pydantic Docs](https://docs.pydantic.dev/)
- [React Documentation](https://react.dev/)
- [AWS ECS Guide](https://docs.aws.amazon.com/ecs/)

---

## Project Goals

**Primary Objectives:**
1. ✅ Build production-ready security tool
2. ✅ Demonstrate full-stack AI engineering skills
3. ✅ Create impressive portfolio piece
4. ✅ Deploy to AWS for live demo
5. ✅ Document for interview discussions

**Success Metrics:**
- All tests passing (>80% coverage)
- Deployed and accessible via URL
- Sub-2s classification response time
- Professional documentation
- Demo video completed

---

**Last Updated:** 2026-02-15  
**Project Status:** In Development  
**Current Phase:** Week 1 - Backend Foundation
