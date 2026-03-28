"""Tests for lambdas.download_tracks.handler validation logic."""

import json
import pytest

from lambdas.common.errors import ValidationError
from lambdas.download_tracks.handler import validate_request, _check_body_size, MAX_TRACKS


class TestValidateRequest:
    def test_valid_request(self) -> None:
        body = {
            "username": "dom",
            "tracks": [{"id": "123", "url": "https://soundcloud.com/test/track", "title": "Test"}]
        }
        tracks, username = validate_request(body)
        assert len(tracks) == 1
        assert tracks[0].id == "123"
        assert username == "dom"

    def test_empty_body_raises(self) -> None:
        with pytest.raises(ValidationError, match="body is required"):
            validate_request(None)

    def test_no_tracks_raises(self) -> None:
        with pytest.raises(ValidationError, match="At least one track"):
            validate_request({"tracks": []})

    def test_too_many_tracks_raises(self) -> None:
        tracks = [{"id": str(i)} for i in range(MAX_TRACKS + 1)]
        with pytest.raises(ValidationError, match=f"Maximum {MAX_TRACKS}"):
            validate_request({"tracks": tracks})

    def test_missing_id_raises(self) -> None:
        with pytest.raises(ValidationError, match="missing 'id'"):
            validate_request({"tracks": [{"title": "no id"}]})

    def test_track_not_dict_raises(self) -> None:
        with pytest.raises(ValidationError, match="must be an object"):
            validate_request({"tracks": ["not a dict"]})

    def test_default_username(self) -> None:
        body = {"tracks": [{"id": "1"}]}
        _, username = validate_request(body)
        assert username == "xomcloud"

    def test_url_fallback_to_api(self) -> None:
        body = {"tracks": [{"id": "999"}]}
        tracks, _ = validate_request(body)
        assert "api.soundcloud.com/tracks/999" in tracks[0].url


class TestCheckBodySize:
    def test_normal_body_passes(self) -> None:
        _check_body_size({"body": '{"tracks": []}'})

    def test_oversized_body_raises(self) -> None:
        """Fix #13: Defensive input size check."""
        huge_body = "x" * 2_000_000
        with pytest.raises(ValidationError, match="too large"):
            _check_body_size({"body": huge_body})

    def test_no_body_passes(self) -> None:
        _check_body_size({})
