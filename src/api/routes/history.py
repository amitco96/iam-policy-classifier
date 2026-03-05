"""
History API endpoints for IAM Policy Classifier.

Stores and retrieves classification history in DynamoDB, keyed by
session_id (device-local UUID) and entry_id (per-classification UUID).

Endpoints:
    GET    /history/{session_id}              - list all entries, newest first
    POST   /history/{session_id}              - save a new entry
    DELETE /history/{session_id}/{entry_id}   - delete one entry
    DELETE /history/{session_id}              - clear all entries for a session
"""

import json
import logging
from typing import Any, Dict, List

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from src.config import settings
from src.models.schemas import ClassificationResult

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/history", tags=["History"])

# Module-level DynamoDB resource — boto3 handles connection pooling internally.
_dynamodb = boto3.resource("dynamodb", region_name=settings.DYNAMODB_REGION)
_table = _dynamodb.Table(settings.DYNAMODB_TABLE)


# ============================================================================
# Schemas
# ============================================================================

class SaveHistoryRequest(BaseModel):
    """Body for POST /history/{session_id}."""
    entry_id: str
    savedAt: str
    result: ClassificationResult
    policy_json: Dict[str, Any]


class HistoryEntryResponse(BaseModel):
    """Single history entry returned to the client."""
    id: str
    savedAt: str
    result: ClassificationResult
    policyJson: Dict[str, Any]


# ============================================================================
# DynamoDB helpers
# ============================================================================

def _to_item(session_id: str, req: SaveHistoryRequest) -> dict:
    """Convert a save request into a DynamoDB item."""
    return {
        "session_id": session_id,
        "entry_id": req.entry_id,
        "savedAt": req.savedAt,
        # Store complex objects as JSON strings to avoid DynamoDB Decimal issues.
        "result_json": json.dumps(req.result.model_dump(mode="json")),
        "policy_json": json.dumps(req.policy_json),
    }


def _from_item(item: dict) -> HistoryEntryResponse:
    """Reconstruct a HistoryEntryResponse from a raw DynamoDB item."""
    return HistoryEntryResponse(
        id=item["entry_id"],
        savedAt=item["savedAt"],
        result=ClassificationResult.model_validate(json.loads(item["result_json"])),
        policyJson=json.loads(item["policy_json"]),
    )


def _dynamo_error(exc: Exception, operation: str) -> HTTPException:
    logger.error("DynamoDB %s failed: %s", operation, exc)
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=f"History service unavailable: {operation} failed",
    )


# ============================================================================
# Routes
# ============================================================================

@router.get(
    "/{session_id}",
    response_model=List[HistoryEntryResponse],
    summary="Get history for a session",
)
async def get_history(session_id: str) -> List[HistoryEntryResponse]:
    """Return all saved entries for *session_id*, sorted newest first."""
    try:
        response = _table.query(
            KeyConditionExpression=Key("session_id").eq(session_id)
        )
    except (BotoCoreError, ClientError) as exc:
        raise _dynamo_error(exc, "Query") from exc

    entries = [_from_item(item) for item in response.get("Items", [])]
    entries.sort(key=lambda e: e.savedAt, reverse=True)
    return entries


@router.post(
    "/{session_id}",
    response_model=HistoryEntryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Save a classification to history",
)
async def save_history(
    session_id: str, body: SaveHistoryRequest
) -> HistoryEntryResponse:
    """Persist a classification result for *session_id*."""
    item = _to_item(session_id, body)
    try:
        _table.put_item(Item=item)
    except (BotoCoreError, ClientError) as exc:
        raise _dynamo_error(exc, "PutItem") from exc

    logger.info(
        "History entry saved",
        extra={"session_id": session_id, "entry_id": body.entry_id},
    )
    return _from_item(item)


@router.delete(
    "/{session_id}/{entry_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete one history entry",
)
async def delete_entry(session_id: str, entry_id: str) -> None:
    """Delete a single history entry by its composite key."""
    try:
        _table.delete_item(
            Key={"session_id": session_id, "entry_id": entry_id}
        )
    except (BotoCoreError, ClientError) as exc:
        raise _dynamo_error(exc, "DeleteItem") from exc

    logger.info(
        "History entry deleted",
        extra={"session_id": session_id, "entry_id": entry_id},
    )


@router.delete(
    "/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Clear all history for a session",
)
async def clear_session(session_id: str) -> None:
    """Delete every history entry for *session_id*."""
    try:
        response = _table.query(
            KeyConditionExpression=Key("session_id").eq(session_id),
            ProjectionExpression="session_id, entry_id",
        )
        items = response.get("Items", [])
        if not items:
            return

        # BatchWriteItem supports up to 25 delete requests per call.
        with _table.batch_writer() as batch:
            for item in items:
                batch.delete_item(
                    Key={"session_id": item["session_id"], "entry_id": item["entry_id"]}
                )
    except (BotoCoreError, ClientError) as exc:
        raise _dynamo_error(exc, "BatchDelete") from exc

    logger.info(
        "Session history cleared",
        extra={"session_id": session_id, "deleted": len(items)},
    )
