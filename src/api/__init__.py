"""
API package for IAM Policy Classifier.

Exports the FastAPI application instance so it can be referenced as:

    uvicorn src.api.main:app --reload
    # or imported in tests:
    from src.api import app
"""

from src.api.main import app

__all__ = ["app"]
