"""Tests for lambdas.common.errors module."""

from lambdas.common.errors import AppError, AuthError, ValidationError, DownloadError, NotFoundError


class TestAppError:
    def test_default_values(self) -> None:
        err = AppError(message="something broke")
        assert err.message == "something broke"
        assert err.status == 500
        assert err.code == "INTERNAL_ERROR"
        assert str(err) == "something broke"

    def test_is_exception(self) -> None:
        err = AppError(message="test")
        assert isinstance(err, Exception)


class TestAuthError:
    def test_defaults(self) -> None:
        err = AuthError()
        assert err.status == 401
        assert err.code == "AUTH_ERROR"
        assert err.message == "Unauthorized"

    def test_custom_message(self) -> None:
        err = AuthError("Token expired")
        assert err.message == "Token expired"


class TestValidationError:
    def test_defaults(self) -> None:
        err = ValidationError()
        assert err.status == 400
        assert err.code == "VALIDATION_ERROR"


class TestDownloadError:
    def test_defaults(self) -> None:
        err = DownloadError()
        assert err.status == 500
        assert err.code == "DOWNLOAD_ERROR"


class TestNotFoundError:
    def test_defaults(self) -> None:
        err = NotFoundError()
        assert err.status == 404
        assert err.code == "NOT_FOUND"
