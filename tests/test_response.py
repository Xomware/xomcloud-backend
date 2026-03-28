"""Tests for lambdas.common.response module."""

import json
import pytest

from lambdas.common.response import success, error, parse_body, CORS_HEADERS
from lambdas.common.errors import AppError, ValidationError, DownloadError


class TestCORSHeaders:
    def test_origin_is_not_wildcard(self) -> None:
        assert CORS_HEADERS["Access-Control-Allow-Origin"] != "*"

    def test_origin_is_xomcloud(self) -> None:
        assert CORS_HEADERS["Access-Control-Allow-Origin"] == "https://xomcloud.xomware.com"


class TestSuccess:
    def test_default_returns_200(self) -> None:
        resp = success()
        assert resp["statusCode"] == 200
        body = json.loads(resp["body"])
        assert body == {"success": True}

    def test_with_data(self) -> None:
        resp = success(data={"url": "https://example.com"})
        assert resp["statusCode"] == 200
        body = json.loads(resp["body"])
        assert body["data"]["url"] == "https://example.com"

    def test_custom_status(self) -> None:
        resp = success(data="created", status=201)
        assert resp["statusCode"] == 201

    def test_includes_cors_headers(self) -> None:
        resp = success()
        for key, value in CORS_HEADERS.items():
            assert resp["headers"][key] == value


class TestError:
    def test_app_error_returns_structured_response(self) -> None:
        err = ValidationError("Missing field")
        resp = error(err)
        assert resp["statusCode"] == 400
        body = json.loads(resp["body"])
        assert body["error"]["code"] == "VALIDATION_ERROR"
        assert body["error"]["message"] == "Missing field"

    def test_generic_exception_does_not_leak_details(self) -> None:
        """Fix #6: Generic exceptions must not expose str(err) to clients."""
        err = RuntimeError("secret database connection string here")
        resp = error(err)
        assert resp["statusCode"] == 500
        body = json.loads(resp["body"])
        assert body["error"]["code"] == "INTERNAL_ERROR"
        assert body["error"]["message"] == "An unexpected error occurred"
        assert "secret" not in body["error"]["message"]

    def test_download_error(self) -> None:
        err = DownloadError("All downloads failed")
        resp = error(err)
        assert resp["statusCode"] == 500
        body = json.loads(resp["body"])
        assert body["error"]["code"] == "DOWNLOAD_ERROR"


class TestParseBody:
    def test_none_body(self) -> None:
        assert parse_body({}) is None

    def test_empty_string_body(self) -> None:
        assert parse_body({"body": ""}) is None

    def test_dict_body_passthrough(self) -> None:
        body = {"tracks": []}
        result = parse_body({"body": body})
        assert result == body

    def test_json_string_body(self) -> None:
        body = json.dumps({"tracks": [{"id": "1"}]})
        result = parse_body({"body": body})
        assert result["tracks"][0]["id"] == "1"

    def test_invalid_json_raises_validation_error(self) -> None:
        """Fix #18: Should catch JSONDecodeError specifically."""
        with pytest.raises(ValidationError, match="Invalid JSON"):
            parse_body({"body": "not valid json {"})
