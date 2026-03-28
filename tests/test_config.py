"""Tests for lambdas.common.config module."""

import time
from unittest.mock import patch, MagicMock

import pytest

from lambdas.common.config import get_param, clear_cache, soundcloud_client_id, _CACHE_TTL_SECONDS


class TestGetParam:
    def setup_method(self) -> None:
        clear_cache()

    @patch("lambdas.common.config._get_ssm")
    def test_fetches_from_ssm(self, mock_ssm_factory: MagicMock) -> None:
        mock_client = MagicMock()
        mock_client.get_parameter.return_value = {
            "Parameter": {"Value": "test-value"}
        }
        mock_ssm_factory.return_value = mock_client

        result = get_param("/xomcloud/test/KEY")
        assert result == "test-value"
        mock_client.get_parameter.assert_called_once_with(
            Name="/xomcloud/test/KEY", WithDecryption=True
        )

    @patch("lambdas.common.config._get_ssm")
    def test_caches_result(self, mock_ssm_factory: MagicMock) -> None:
        """Fix #7: Verify caching works (and uses TTL, not lru_cache)."""
        mock_client = MagicMock()
        mock_client.get_parameter.return_value = {
            "Parameter": {"Value": "cached-value"}
        }
        mock_ssm_factory.return_value = mock_client

        # First call fetches from SSM
        result1 = get_param("/xomcloud/test/KEY")
        # Second call should use cache
        result2 = get_param("/xomcloud/test/KEY")

        assert result1 == result2 == "cached-value"
        assert mock_client.get_parameter.call_count == 1

    @patch("lambdas.common.config._get_ssm")
    @patch("lambdas.common.config.time")
    def test_cache_expires_after_ttl(self, mock_time: MagicMock, mock_ssm_factory: MagicMock) -> None:
        mock_client = MagicMock()
        mock_client.get_parameter.side_effect = [
            {"Parameter": {"Value": "old-value"}},
            {"Parameter": {"Value": "new-value"}},
        ]
        mock_ssm_factory.return_value = mock_client

        # First call at t=0
        mock_time.monotonic.return_value = 0.0
        result1 = get_param("/xomcloud/test/KEY")
        assert result1 == "old-value"

        # Second call after TTL expires
        mock_time.monotonic.return_value = _CACHE_TTL_SECONDS + 1.0
        result2 = get_param("/xomcloud/test/KEY")
        assert result2 == "new-value"
        assert mock_client.get_parameter.call_count == 2

    def test_clear_cache(self) -> None:
        # Should not raise
        clear_cache()


class TestSoundcloudClientId:
    def setup_method(self) -> None:
        clear_cache()

    @patch.dict("os.environ", {"SOUNDCLOUD_CLIENT_ID": "env-client-id"})
    def test_returns_from_env(self) -> None:
        result = soundcloud_client_id()
        assert result == "env-client-id"

    @patch.dict("os.environ", {}, clear=True)
    @patch("lambdas.common.config._get_ssm")
    def test_raises_on_missing_client_id(self, mock_ssm_factory: MagicMock) -> None:
        """Fix #11: Should raise, not silently return None."""
        mock_client = MagicMock()
        mock_client.get_parameter.return_value = {
            "Parameter": {"Value": ""}
        }
        mock_ssm_factory.return_value = mock_client

        with pytest.raises(ValueError, match="client_id is not configured"):
            soundcloud_client_id()
