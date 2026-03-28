import boto3
import os
import time
import threading
from typing import Optional

_ssm = None
PRODUCT = "xomcloud"

# TTL-based cache for SSM parameters (supports secret rotation)
_cache: dict[str, tuple[str, float]] = {}
_cache_lock = threading.Lock()
_CACHE_TTL_SECONDS = 300  # 5 minutes


def _get_ssm():
    """Get SSM client (lazy initialization)."""
    global _ssm
    if _ssm is None:
        _ssm = boto3.client("ssm")
    return _ssm


def get_param(name: str, decrypt: bool = True) -> str:
    """Get a parameter from SSM Parameter Store (cached with TTL)."""
    now = time.monotonic()

    with _cache_lock:
        if name in _cache:
            value, fetched_at = _cache[name]
            if now - fetched_at < _CACHE_TTL_SECONDS:
                return value

    response = _get_ssm().get_parameter(Name=name, WithDecryption=decrypt)
    value = response["Parameter"]["Value"]

    with _cache_lock:
        _cache[name] = (value, now)

    return value


def clear_cache() -> None:
    """Clear the SSM parameter cache. Useful for testing."""
    with _cache_lock:
        _cache.clear()


# NOTE: AWS access keys should NOT be fetched from SSM.
# Lambda execution roles provide credentials automatically via IAM.
# The previous aws_access_key() and aws_secret_key() functions have been
# removed. If you need AWS credentials, configure the Lambda execution
# role with the appropriate IAM permissions.


def soundcloud_client_id() -> str:
    """Get SoundCloud client ID from SSM or environment.

    Raises ValueError if the client ID cannot be resolved.
    """
    value = os.environ.get("SOUNDCLOUD_CLIENT_ID") or get_param(f"/{PRODUCT}/soundcloud/CLIENT_ID")
    if not value:
        raise ValueError("SoundCloud client_id is not configured")
    return value


def soundcloud_client_secret() -> str:
    """Get SoundCloud client secret from SSM or environment."""
    return os.environ.get("SOUNDCLOUD_CLIENT_SECRET") or get_param(f"/{PRODUCT}/soundcloud/CLIENT_SECRET")


def api_secret_key() -> str:
    """Get API secret key from SSM or environment."""
    return os.environ.get("API_SECRET_KEY") or get_param(f"/{PRODUCT}/api/API_SECRET_KEY")
