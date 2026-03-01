"""
Core business-logic package for IAM Policy Classifier.

Exports ClassificationService so callers can write:

    from src.core import ClassificationService
"""

from src.core.classifier import ClassificationService

__all__ = ["ClassificationService"]
