"""Tests for lambdas.authorizer.handler module."""

import importlib
import jwt
import pytest
from unittest.mock import patch

# Import the handler module directly to avoid __init__.py shadowing
_handler_mod = importlib.import_module("lambdas.authorizer.handler")
handler = _handler_mod.handler
decode_token = _handler_mod.decode_token
generate_policy = _handler_mod.generate_policy
_mask_sub = _handler_mod._mask_sub

# Patch target: the api_secret_key reference inside the handler module
_MOD_PATH = "lambdas.authorizer.handler"

TEST_SECRET = "test-secret-key"


def _patch_secret():
    """Patch api_secret_key in the handler module's namespace."""
    return patch.object(_handler_mod, "api_secret_key", return_value=TEST_SECRET)


class TestMaskSub:
    def test_masks_long_sub(self) -> None:
        """Fix #22: User sub should be masked in logs."""
        result = _mask_sub("user-1234-abcd-5678")
        assert result == "user***78"

    def test_masks_short_sub(self) -> None:
        result = _mask_sub("abc")
        assert result == "ab***"


class TestGeneratePolicy:
    def test_allow_policy(self) -> None:
        policy = generate_policy("Allow", "arn:aws:execute-api:*")
        assert policy["policyDocument"]["Statement"][0]["Effect"] == "Allow"

    def test_deny_policy(self) -> None:
        policy = generate_policy("Deny", "arn:aws:execute-api:*")
        assert policy["policyDocument"]["Statement"][0]["Effect"] == "Deny"

    def test_custom_principal(self) -> None:
        policy = generate_policy("Allow", "*", principal="user-123")
        assert policy["principalId"] == "user-123"


class TestDecodeToken:
    def test_valid_token(self) -> None:
        with _patch_secret():
            token = jwt.encode({"sub": "user-1"}, TEST_SECRET, algorithm="HS256")
            result = decode_token(f"Bearer {token}")
            assert result is not None
            assert result["sub"] == "user-1"

    def test_invalid_token_returns_none(self) -> None:
        with _patch_secret():
            result = decode_token("Bearer invalid.token.here")
            assert result is None

    def test_expired_token_returns_none(self) -> None:
        import time
        with _patch_secret():
            token = jwt.encode(
                {"sub": "user-1", "exp": int(time.time()) - 100},
                TEST_SECRET,
                algorithm="HS256"
            )
            result = decode_token(f"Bearer {token}")
            assert result is None


class TestHandler:
    """Fix #5: Handler should raise Exception('Unauthorized') on auth failure."""

    def test_missing_token_raises(self) -> None:
        with _patch_secret():
            with pytest.raises(Exception, match="Unauthorized"):
                handler({"methodArn": "arn:aws:execute-api:*"}, None)

    def test_missing_arn_raises(self) -> None:
        with _patch_secret():
            with pytest.raises(Exception, match="Unauthorized"):
                handler({"authorizationToken": "Bearer abc"}, None)

    def test_invalid_token_raises(self) -> None:
        with _patch_secret():
            with pytest.raises(Exception, match="Unauthorized"):
                handler({
                    "methodArn": "arn:aws:execute-api:*",
                    "authorizationToken": "Bearer bad.token"
                }, None)

    def test_valid_token_returns_allow(self) -> None:
        with _patch_secret():
            token = jwt.encode({"sub": "user-42"}, TEST_SECRET, algorithm="HS256")
            result = handler({
                "methodArn": "arn:aws:execute-api:us-east-1:123:abc/*/GET/download",
                "authorizationToken": f"Bearer {token}"
            }, None)
            assert result["policyDocument"]["Statement"][0]["Effect"] == "Allow"
            assert result["principalId"] == "user-42"
