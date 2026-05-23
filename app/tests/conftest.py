"""
Shared pytest fixtures.

Integration tests that write to Supabase require SUPABASE_URL and
SUPABASE_SERVICE_KEY in the environment. Unit tests run without any DB.
"""
import os
from datetime import date
from unittest.mock import MagicMock

import pytest


@pytest.fixture()
def mock_db(mocker):
    """Return a MagicMock Supabase client for unit tests that don't hit the DB."""
    client = MagicMock()
    mocker.patch("pipeline.db.get_client", return_value=client)
    return client


@pytest.fixture()
def today() -> date:
    return date.today()


@pytest.fixture()
def sample_snapshot_row():
    return {
        "ticker": "RKLB",
        "snapshot_date": str(date.today()),
        "mention_count_24h": 120,
        "mention_count_7d": 650,
        "rank": 5,
        "upvotes": 340,
    }
