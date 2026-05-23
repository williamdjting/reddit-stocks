"""Unit tests for tranche_classify.py — phase gates, quality filter, tranche rules."""
import pytest

from pipeline.tranche_classify import _classify, _is_noise_spike


def base_row(
    days: int = 200,
    weekly: int = 50,
    monthly: int = 200,
    v_1w_1mo: float = 1.5,
    v_1mo_3mo: float = 1.2,
    v_3mo_6mo: float = 1.1,
    v_6mo_1y: float = 1.05,
    spread: int = 4,
) -> dict:
    return {
        "days_in_dataset": days,
        "mention_count_1w": weekly,
        "mention_count_1mo": monthly,
        "velocity_1w_vs_1mo": v_1w_1mo,
        "velocity_1mo_vs_3mo": v_1mo_3mo,
        "velocity_3mo_vs_6mo": v_3mo_6mo,
        "velocity_6mo_vs_1y": v_6mo_1y,
        "subreddit_spread": spread,
    }


class TestInsufficientDataGate:
    def test_89_days_returns_insufficient_data(self):
        row = base_row(days=89)
        assert _classify(row, market_cap=1_000_000_000, raw_mention_stats={}) == "insufficient_data"

    def test_90_days_is_eligible_for_classification(self):
        row = base_row(days=90)
        result = _classify(row, market_cap=1_000_000_000, raw_mention_stats={})
        assert result != "insufficient_data"

    def test_0_days_returns_insufficient_data(self):
        row = base_row(days=0)
        assert _classify(row, market_cap=500_000_000, raw_mention_stats={}) == "insufficient_data"


class TestSeedPhaseGate:
    def test_200_days_cannot_be_seed(self):
        row = base_row(days=200, weekly=20, v_6mo_1y=1.5, v_3mo_6mo=1.3, spread=2)
        result = _classify(row, market_cap=2_000_000_000, raw_mention_stats={})
        assert result != "seed"

    def test_365_days_with_correct_metrics_can_be_seed(self):
        row = base_row(days=365, weekly=20, monthly=90, v_6mo_1y=1.2, v_3mo_6mo=1.1, spread=2)
        result = _classify(row, market_cap=2_000_000_000, raw_mention_stats={})
        assert result == "seed"

    def test_seed_blocked_above_5b_market_cap(self):
        row = base_row(days=365, weekly=20, monthly=90, v_6mo_1y=1.2, v_3mo_6mo=1.1, spread=2)
        result = _classify(row, market_cap=6_000_000_000, raw_mention_stats={})
        assert result != "seed"


class TestEarlyPhaseGate:
    def test_170_days_cannot_be_early(self):
        row = base_row(days=170, weekly=100, v_1mo_3mo=1.2, v_3mo_6mo=1.1, spread=3)
        result = _classify(row, market_cap=3_000_000_000, raw_mention_stats={})
        assert result != "early"

    def test_180_days_with_correct_metrics_can_be_early(self):
        # v_1w_1mo=1.1 is below TIER3_WOW_GROWTH_THRESHOLD (1.50) so pre_pop WoW path won't fire
        row = base_row(days=180, weekly=100, monthly=400, v_1w_1mo=1.1, v_1mo_3mo=1.2, v_3mo_6mo=1.1, spread=3)
        result = _classify(row, market_cap=3_000_000_000, raw_mention_stats={})
        assert result == "early"

    def test_early_blocked_above_10b_market_cap(self):
        row = base_row(days=180, weekly=100, monthly=400, v_1mo_3mo=1.2, v_3mo_6mo=1.1, spread=3)
        result = _classify(row, market_cap=11_000_000_000, raw_mention_stats={})
        assert result != "early"


class TestPrePopTier3:
    def test_high_weekly_volume_with_spread_is_prepop(self):
        # monthly=1400 gives monthly_weekly_avg≈323 > 350×0.20=70, so no noise spike
        row = base_row(days=120, weekly=350, monthly=1400, spread=4)
        result = _classify(row, market_cap=900_000_000, raw_mention_stats={})
        assert result == "pre_pop"

    def test_high_wow_growth_with_spread_is_prepop(self):
        row = base_row(days=120, weekly=100, v_1w_1mo=2.0, spread=4)
        result = _classify(row, market_cap=500_000_000, raw_mention_stats={})
        assert result == "pre_pop"

    def test_prepop_blocked_above_20b_market_cap(self):
        row = base_row(days=120, weekly=400, spread=5)
        result = _classify(row, market_cap=25_000_000_000, raw_mention_stats={})
        assert result != "pre_pop"

    def test_high_volume_without_spread_is_not_prepop(self):
        row = base_row(days=120, weekly=400, spread=1)
        result = _classify(row, market_cap=500_000_000, raw_mention_stats={})
        assert result != "pre_pop"


class TestQualityFilter:
    def test_below_50m_market_cap_is_noise(self):
        row = base_row(days=200, weekly=400, spread=5)
        result = _classify(row, market_cap=30_000_000, raw_mention_stats={})
        assert result == "noise"

    def test_none_market_cap_not_filtered(self):
        row = base_row(days=200, weekly=50, spread=4)
        result = _classify(row, market_cap=None, raw_mention_stats={})
        assert result != "noise"


class TestNoiseSpikeDetection:
    def test_spike_without_prior_build_is_noise(self):
        row = {"mention_count_1w": 500, "mention_count_1mo": 50}
        # monthly_weekly_avg = 50/4.33 ≈ 11.5; threshold: 500 × 0.20 = 100 → 11.5 < 100 → noise
        assert _is_noise_spike(row, {}) is True

    def test_sustained_build_is_not_noise(self):
        row = {"mention_count_1w": 300, "mention_count_1mo": 800}
        # monthly_weekly_avg = 800/4.33 ≈ 184; threshold: 300 × 0.20 = 60 → 184 > 60 → not noise
        assert _is_noise_spike(row, {}) is False

    def test_below_abs_threshold_is_not_noise(self):
        row = {"mention_count_1w": 50, "mention_count_1mo": 5}
        assert _is_noise_spike(row, {}) is False

    def test_high_new_account_ratio_triggers_noise(self):
        row = {"mention_count_1w": 50, "mention_count_1mo": 500}
        assert _is_noise_spike(row, {"new_account_ratio": 0.85}) is True

    def test_pump_subreddit_dominance_triggers_noise(self):
        row = {"mention_count_1w": 50, "mention_count_1mo": 500}
        stats = {"new_account_ratio": 0.0, "dominant_subreddit": "r/RobinHoodPennyStocks"}
        assert _is_noise_spike(row, stats) is True
