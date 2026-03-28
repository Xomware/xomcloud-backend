from __future__ import annotations

import json
import logging
from typing import Any, Optional

from lambdas.common.errors import AppError

logger = logging.getLogger(__name__)

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "https://xomcloud.xomware.com",
    "Access-Control-Allow-Headers": "Content-Type,Authorization",
    "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
    "Content-Type": "application/json"
}


def success(data: Any = None, status: int = 200) -> dict:
    """Build a successful API response."""
    return {
        "statusCode": status,
        "headers": CORS_HEADERS,
        "body": json.dumps({"data": data}) if data is not None else json.dumps({"success": True})
    }


def error(err: AppError | Exception, status: int = 500) -> dict:
    """Build an error API response."""
    if isinstance(err, AppError):
        return {
            "statusCode": err.status,
            "headers": CORS_HEADERS,
            "body": json.dumps({
                "error": {
                    "code": err.code,
                    "message": err.message
                }
            })
        }

    # Log the real error server-side, return generic message to client
    logger.error("Unhandled exception: %s", str(err), exc_info=True)
    return {
        "statusCode": status,
        "headers": CORS_HEADERS,
        "body": json.dumps({
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred"
            }
        })
    }


def parse_body(event: dict) -> Optional[dict]:
    """Parse JSON body from API Gateway event."""
    body = event.get("body")
    if not body:
        return None
    if isinstance(body, dict):
        return body
    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        from lambdas.common.errors import ValidationError
        raise ValidationError(f"Invalid JSON in request body: {exc.msg}")
