from __future__ import annotations

import jwt
from lambdas.common import get_logger, api_secret_key

log = get_logger(__name__)


def _mask_sub(sub: str) -> str:
    """Mask a user sub for safe logging. Shows first 4 and last 2 chars."""
    s = str(sub)
    if len(s) <= 6:
        return s[:2] + "***"
    return s[:4] + "***" + s[-2:]


def generate_policy(effect: str, resource: str, principal: str = "xomcloud") -> dict:
    """Generate an IAM policy for API Gateway."""
    return {
        "principalId": principal,
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [{
                "Action": "execute-api:Invoke",
                "Effect": effect,
                "Resource": resource
            }]
        }
    }


def decode_token(token: str) -> dict | None:
    """Decode and validate a JWT token."""
    try:
        clean_token = token.replace("Bearer ", "").strip()
        return jwt.decode(clean_token, api_secret_key(), algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        log.warning("Token expired")
        return None
    except jwt.InvalidTokenError:
        log.warning("Invalid token presented")
        return None


def handler(event: dict, context) -> dict:
    """Lambda authorizer handler for XOMCLOUD API.

    Raises Exception('Unauthorized') on auth failure so API Gateway
    returns a proper 401 instead of a cached Deny policy.
    """
    method_arn = event.get("methodArn", "")
    auth_token = event.get("authorizationToken", "")

    if not method_arn:
        log.warning("Missing method ARN")
        raise Exception("Unauthorized")

    if not auth_token:
        log.warning("Missing authorization token")
        raise Exception("Unauthorized")

    # Decode and validate JWT
    user = decode_token(auth_token)
    if user:
        user_sub = str(user.get("sub", "xomcloud"))
        log.info("Authorized user: %s", _mask_sub(user_sub))
        return generate_policy("Allow", method_arn, principal=user_sub)

    log.warning("Authorization denied - invalid token")
    raise Exception("Unauthorized")
