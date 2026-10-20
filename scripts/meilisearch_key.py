"""Provision the least-privilege Meilisearch key used by SCOT-API."""

import logging
import os
import time
from collections.abc import Callable
from pathlib import Path

import meilisearch
from meilisearch.errors import MeilisearchApiError, MeilisearchError

SEARCH_KEY_ACTIONS = frozenset(
    {
        "search",
        "documents.add",
        "documents.delete",
    }
)
SEARCH_KEY_INDEXES = frozenset({"entries"})
logger = logging.getLogger(__name__)


def _get_or_create_key(client: meilisearch.Client, key_uid: str):
    try:
        return client.get_key(key_uid)
    except MeilisearchApiError as exc:
        if exc.status_code != 404:
            raise

    options = {
        "uid": key_uid,
        "name": "SCOT API search key",
        "description": "Searches and maintains documents in the SCOT entries index",
        "actions": sorted(SEARCH_KEY_ACTIONS),
        "indexes": sorted(SEARCH_KEY_INDEXES),
        "expiresAt": None,
    }
    try:
        return client.create_key(options)
    except MeilisearchApiError as exc:
        # Multiple API replicas can reach this step concurrently. If another
        # replica created the stable UID first, retrieve that key instead.
        if exc.status_code != 409:
            raise
        return client.get_key(key_uid)


def _validate_key_scope(key) -> None:
    if (
        frozenset(key.actions) != SEARCH_KEY_ACTIONS
        or frozenset(key.indexes) != SEARCH_KEY_INDEXES
        or key.expires_at is not None
    ):
        raise RuntimeError(
            "Existing SCOT API Meilisearch key does not have the expected scope"
        )


def provision_search_key(
    client: meilisearch.Client,
    key_uid: str,
    *,
    max_attempts: int = 120,
    retry_seconds: float = 5,
    sleep: Callable[[float], None] = time.sleep,
) -> str:
    """Wait for Meilisearch and idempotently return the scoped API key."""
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")

    last_error: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            if client.is_healthy():
                key = _get_or_create_key(client, key_uid)
                _validate_key_scope(key)
                return key.key
            last_error = RuntimeError("Meilisearch is not healthy")
        except MeilisearchApiError as exc:
            if exc.status_code in {400, 401, 403}:
                raise RuntimeError(
                    "Meilisearch rejected the search-key provisioning request"
                ) from exc
            last_error = exc
        except MeilisearchError as exc:
            last_error = exc

        if attempt < max_attempts:
            if attempt == 1 or attempt % 12 == 0:
                logger.warning(
                    "Meilisearch search-key provisioning attempt %d/%d failed; retrying",
                    attempt,
                    max_attempts,
                )
            sleep(retry_seconds)

    raise RuntimeError(
        f"Unable to provision the Meilisearch API key after {max_attempts} attempts"
    ) from last_error


def write_key_file(path: Path, key: str) -> None:
    """Write the key with permissions limited to the pod's runtime user."""
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as key_file:
        key_file.write(key)
    path.chmod(0o600)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    host = os.environ["SEARCH_HOST"]
    master_key = os.environ["MEILI_MASTER_KEY"]
    key_uid = os.environ["SEARCH_API_KEY_UID"]
    key_path = Path(os.environ["SEARCH_API_KEY_FILE"])
    max_attempts = int(os.environ.get("SEARCH_KEY_MAX_ATTEMPTS", "120"))
    retry_seconds = float(os.environ.get("SEARCH_KEY_RETRY_SECONDS", "5"))

    client = meilisearch.Client(host, master_key)
    key = provision_search_key(
        client,
        key_uid,
        max_attempts=max_attempts,
        retry_seconds=retry_seconds,
    )
    write_key_file(key_path, key)


if __name__ == "__main__":
    main()
