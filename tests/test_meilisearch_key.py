from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.meilisearch_key import (
    SEARCH_KEY_ACTIONS,
    SEARCH_KEY_INDEXES,
    provision_search_key,
    write_key_file,
)


def _key(**overrides):
    values = {
        "key": "scoped-search-key",
        "actions": list(SEARCH_KEY_ACTIONS),
        "indexes": list(SEARCH_KEY_INDEXES),
        "expires_at": None,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


class FakeClient:
    def __init__(self, *, healthy=True, existing_key=None):
        self.healthy = healthy
        self.existing_key = existing_key
        self.created_with = None

    def is_healthy(self):
        return self.healthy

    def get_key(self, _key_uid):
        return self.existing_key

    def create_key(self, options):
        self.created_with = options
        return _key()


def test_provision_search_key_reuses_existing_key():
    client = FakeClient(existing_key=_key())

    result = provision_search_key(client, "key-uid", max_attempts=1)

    assert result == "scoped-search-key"
    assert client.created_with is None


def test_provision_search_key_creates_expected_scope(monkeypatch):
    client = FakeClient()

    class NotFoundError(Exception):
        status_code = 404

    monkeypatch.setattr("scripts.meilisearch_key.MeilisearchApiError", NotFoundError)

    def missing_key(_key_uid):
        raise NotFoundError()

    client.get_key = missing_key

    result = provision_search_key(client, "key-uid", max_attempts=1)

    assert result == "scoped-search-key"
    assert client.created_with == {
        "uid": "key-uid",
        "name": "SCOT API search key",
        "description": "Searches and maintains documents in the SCOT entries index",
        "actions": sorted(SEARCH_KEY_ACTIONS),
        "indexes": sorted(SEARCH_KEY_INDEXES),
        "expiresAt": None,
    }


def test_provision_search_key_retries_until_healthy():
    client = FakeClient(existing_key=_key())
    health_results = iter((False, True))
    client.is_healthy = lambda: next(health_results)
    delays = []

    result = provision_search_key(
        client,
        "key-uid",
        max_attempts=2,
        retry_seconds=3,
        sleep=delays.append,
    )

    assert result == "scoped-search-key"
    assert delays == [3]


def test_provision_search_key_rejects_unexpected_scope():
    client = FakeClient(existing_key=_key(actions=["*"]))

    with pytest.raises(RuntimeError, match="does not have the expected scope"):
        provision_search_key(client, "key-uid", max_attempts=1)


def test_write_key_file_limits_permissions(tmp_path: Path):
    key_path = tmp_path / "search-api-key"

    write_key_file(key_path, "secret-value")

    assert key_path.read_text(encoding="utf-8") == "secret-value"
    assert key_path.stat().st_mode & 0o777 == 0o600
