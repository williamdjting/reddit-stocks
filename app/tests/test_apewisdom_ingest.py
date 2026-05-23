"""Unit tests for apewisdom_ingest.py."""
from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from pipeline import apewisdom_ingest
from pipeline.apewisdom_ingest import StageResult, fetch_page, run


class TestFetchPage:
    def test_returns_results_on_success(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"results": [{"ticker": "RKLB", "mentions": 120}]}
        mock_resp.raise_for_status = MagicMock()
        session = MagicMock()
        session.get.return_value = mock_resp

        result = fetch_page(1, session)

        assert result == [{"ticker": "RKLB", "mentions": 120}]

    def test_returns_empty_list_on_empty_results(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"results": []}
        mock_resp.raise_for_status = MagicMock()
        session = MagicMock()
        session.get.return_value = mock_resp

        assert fetch_page(1, session) == []

    def test_returns_none_on_http_error(self):
        session = MagicMock()
        session.get.side_effect = Exception("connection refused")

        assert fetch_page(1, session) is None


class TestRun:
    def _make_page_response(self, tickers: list[str]):
        return [
            {"ticker": t, "mentions": 50, "mentions_24h_ago": 200, "rank": i + 1, "upvotes": 100}
            for i, t in enumerate(tickers)
        ]

    def test_successful_ingest_writes_records(self, mock_db):
        pages = [
            self._make_page_response(["RKLB", "ACHR"]),
            [],  # empty page = end
        ]
        with patch.object(apewisdom_ingest, "fetch_page", side_effect=pages):
            result = run(snapshot_date=date(2026, 5, 23), db=mock_db)

        assert result.records_written == 2
        assert result.stale is False
        assert result.errors == []
        mock_db.table.assert_called_with("apewisdom_snapshots")

    def test_idempotent_upsert_called_with_correct_conflict_key(self, mock_db):
        pages = [self._make_page_response(["RKLB"]), []]
        with patch.object(apewisdom_ingest, "fetch_page", side_effect=pages):
            run(snapshot_date=date(2026, 5, 23), db=mock_db)

        upsert_call = mock_db.table.return_value.upsert
        _, kwargs = upsert_call.call_args
        assert kwargs["on_conflict"] == "ticker,snapshot_date"

    def test_three_consecutive_failures_marks_stale(self, mock_db):
        with patch.object(apewisdom_ingest, "fetch_page", return_value=None):
            with patch("time.sleep"):
                result = run(snapshot_date=date(2026, 5, 23), db=mock_db)

        assert result.stale is True
        assert len(result.errors) == 1

    def test_empty_ticker_rows_are_filtered_out(self, mock_db):
        pages = [[{"ticker": "", "mentions": 10}, {"ticker": "RKLB", "mentions": 50}], []]
        with patch.object(apewisdom_ingest, "fetch_page", side_effect=pages):
            result = run(snapshot_date=date(2026, 5, 23), db=mock_db)

        upsert_records = mock_db.table.return_value.upsert.call_args[0][0]
        assert all(r["ticker"] for r in upsert_records)
        assert result.records_written == 1

    def test_tickers_are_uppercased(self, mock_db):
        pages = [[{"ticker": "rklb", "mentions": 50, "rank": 1, "upvotes": 10}], []]
        with patch.object(apewisdom_ingest, "fetch_page", side_effect=pages):
            run(snapshot_date=date(2026, 5, 23), db=mock_db)

        upsert_records = mock_db.table.return_value.upsert.call_args[0][0]
        assert upsert_records[0]["ticker"] == "RKLB"

    def test_uses_today_as_default_snapshot_date(self, mock_db):
        pages = [[{"ticker": "RKLB", "mentions": 50, "rank": 1, "upvotes": 10}], []]
        with patch.object(apewisdom_ingest, "fetch_page", side_effect=pages):
            run(db=mock_db)

        upsert_records = mock_db.table.return_value.upsert.call_args[0][0]
        assert upsert_records[0]["snapshot_date"] == str(date.today())
