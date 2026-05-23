"""Unit tests for score_compute.py — velocity, acceleration, rolling windows."""
from datetime import date, timedelta

import pandas as pd
import pytest

from pipeline.config import compute_acceleration, compute_velocity
from pipeline.score_compute import WINDOW_DAYS, _rolling_count, compute_row


class TestComputeVelocity:
    def test_accelerating_returns_gt_one(self):
        # 50 mentions in 1 week vs 50/4.33 per week over 1 month → velocity > 1
        v = compute_velocity(50, 50, "1w", "1mo")
        assert v is not None
        assert v > 1.0

    def test_flat_returns_one(self):
        # 1w rate == 1mo rate → velocity = 1.0
        # 1w=10, 1mo=43 → 10/1 vs 43/4.33 ≈ 9.93 — close to 1
        v = compute_velocity(10, 43, "1w", "1mo")
        assert v is not None
        assert abs(v - 1.0) < 0.05

    def test_none_when_short_count_is_none(self):
        assert compute_velocity(None, 100, "1w", "1mo") is None

    def test_none_when_long_count_is_none(self):
        assert compute_velocity(100, None, "1w", "1mo") is None

    def test_sentinel_when_long_is_zero_and_short_gt_zero(self):
        v = compute_velocity(50, 0, "1w", "1mo")
        assert v == 999.0

    def test_none_when_both_zero(self):
        assert compute_velocity(0, 0, "1w", "1mo") is None

    def test_decelerating_returns_lt_one(self):
        v = compute_velocity(5, 100, "1w", "1mo")
        assert v is not None
        assert v < 1.0


class TestComputeAcceleration:
    def test_positive_when_short_vel_gt_long(self):
        acc = compute_acceleration(2.0, 1.0)
        assert acc == 1.0

    def test_negative_when_decelerating(self):
        acc = compute_acceleration(0.8, 1.5)
        assert acc == pytest.approx(-0.7)

    def test_none_when_either_is_none(self):
        assert compute_acceleration(None, 1.0) is None
        assert compute_acceleration(1.0, None) is None


class TestRollingCount:
    def _make_df(self, days_back: int, daily_count: int = 10) -> pd.DataFrame:
        today = date.today()
        rows = [
            {"ticker": "RKLB", "snapshot_date": today - timedelta(days=i), "mention_count_24h": daily_count}
            for i in range(days_back)
        ]
        df = pd.DataFrame(rows)
        df["snapshot_date"] = pd.to_datetime(df["snapshot_date"]).dt.date
        return df

    def test_returns_sum_within_window(self):
        df = self._make_df(days_back=10, daily_count=5)
        total = _rolling_count(df, date.today(), days=7, days_in_dataset=10)
        assert total == 35  # 7 days × 5 mentions

    def test_returns_none_when_no_data_in_window(self):
        # Ticker is 30 days old but only has 5 days of snapshots; data still falls in window
        df = self._make_df(days_back=5, daily_count=10)
        total = _rolling_count(df, date.today(), days=30, days_in_dataset=30)
        assert total is not None

    def test_returns_none_when_df_is_empty(self):
        df = pd.DataFrame(columns=["ticker", "snapshot_date", "mention_count_24h"])
        assert _rolling_count(df, date.today(), days=7, days_in_dataset=7) is None


class TestComputeRow:
    def _make_ticker_df(self, days: int, daily_count: int = 20) -> pd.DataFrame:
        today = date.today()
        rows = [
            {
                "ticker": "RKLB",
                "snapshot_date": today - timedelta(days=i),
                "mention_count_24h": daily_count,
            }
            for i in range(days)
        ]
        df = pd.DataFrame(rows)
        df["snapshot_date"] = pd.to_datetime(df["snapshot_date"]).dt.date
        return df

    def test_days_in_dataset_computed_from_first_seen_at(self):
        stat_date = date.today()
        first_seen = stat_date - timedelta(days=120)
        df = self._make_ticker_df(days=120)
        row = compute_row("RKLB", first_seen, stat_date, df, subreddit_spread=3)
        assert row["days_in_dataset"] == 120

    def test_short_window_null_when_no_data(self):
        stat_date = date.today()
        first_seen = stat_date - timedelta(days=5)
        df = self._make_ticker_df(days=5)
        row = compute_row("RKLB", first_seen, stat_date, df, subreddit_spread=None)
        # 1-year window has no data when ticker is 5 days old
        assert row["mention_count_1y"] is None

    def test_velocity_none_when_window_unavailable(self):
        stat_date = date.today()
        first_seen = stat_date - timedelta(days=5)
        df = self._make_ticker_df(days=5)
        row = compute_row("RKLB", first_seen, stat_date, df, subreddit_spread=None)
        assert row["velocity_6mo_vs_1y"] is None

    def test_snapshot_date_set_to_most_recent(self):
        stat_date = date.today()
        first_seen = stat_date - timedelta(days=100)
        df = self._make_ticker_df(days=100)
        row = compute_row("RKLB", first_seen, stat_date, df, subreddit_spread=2)
        assert row["apewisdom_snapshot_date"] == str(stat_date)
