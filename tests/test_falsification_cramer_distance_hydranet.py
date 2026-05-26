"""Falsification tests for HydraNet per-type validation claims.

Tests verify that the HydraNet scoring CSVs exist and that the numbers
reported in the paper (§5.3, §6.3) match the data.

Data source: purple_alien calibration partition (Jan 2017 - Dec 2020).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

PAPER_DIR = Path(__file__).resolve().parent.parent / "paper"
DATA_DIR = PAPER_DIR / "data"

_TYPES = {
    "state_based": DATA_DIR / "hydranet_scores_state_based.csv",
    "non_state": DATA_DIR / "hydranet_scores_non_state.csv",
    "one_sided": DATA_DIR / "hydranet_scores_one_sided.csv",
}


@pytest.fixture(params=list(_TYPES.keys()))
def hydranet_df(request: pytest.FixtureRequest) -> tuple[str, pd.DataFrame]:
    path = _TYPES[request.param]
    assert path.exists(), f"Missing {path}"
    return request.param, pd.read_csv(path)


class TestHydraNetCSVsExistAndHaveExpectedShape:
    def test_csv_exists(self, hydranet_df: tuple[str, pd.DataFrame]) -> None:
        _, df = hydranet_df
        assert len(df) > 0

    def test_required_columns(self, hydranet_df: tuple[str, pd.DataFrame]) -> None:
        _, df = hydranet_df
        required = {
            "priogrid_gid", "year", "month", "best", "post_mean",
            "tight_classical", "honest_classical",
            "tight_parametric", "honest_parametric",
            "tight_rvi", "honest_rvi",
        }
        assert required.issubset(set(df.columns))


class TestHydraNetSampleSizes:
    """Verify sample sizes match Table hydranet_sample in §5.3."""

    def test_state_based_sample_size(self) -> None:
        df = pd.read_csv(_TYPES["state_based"])
        assert len(df) == 5372

    def test_non_state_sample_size(self) -> None:
        df = pd.read_csv(_TYPES["non_state"])
        assert len(df) == 2130

    def test_one_sided_sample_size(self) -> None:
        df = pd.read_csv(_TYPES["one_sided"])
        assert len(df) == 2702


def _factor_of_two(df: pd.DataFrame) -> pd.DataFrame:
    ratio = df["post_mean"] / df["best"].clip(lower=1e-6)
    return df[(ratio >= 0.5) & (ratio <= 2.0)]


def _reversal_stats(df: pd.DataFrame) -> dict:
    close = _factor_of_two(df)
    classical_tight = close[close["tight_classical"] < close["honest_classical"]]
    n_tight = len(classical_tight)
    if n_tight == 0:
        return {"n_close": len(close), "n_tight": 0, "param_rev": 0, "rvi_rev": 0}
    param_rev = (classical_tight["honest_parametric"] < classical_tight["tight_parametric"]).sum()
    rvi_rev = (classical_tight["honest_rvi"] < classical_tight["tight_rvi"]).sum()
    return {"n_close": len(close), "n_tight": n_tight, "param_rev": param_rev, "rvi_rev": rvi_rev}


class TestHydraNetReversalRates:
    """Verify reversal rates match Table hydranet_reversal in §6.3."""

    def test_state_based_reversal(self) -> None:
        df = pd.read_csv(_TYPES["state_based"])
        s = _reversal_stats(df)
        assert s["n_close"] == 589
        assert s["n_tight"] == 115
        assert s["param_rev"] == 114
        assert s["rvi_rev"] == 110

    def test_non_state_reversal(self) -> None:
        df = pd.read_csv(_TYPES["non_state"])
        s = _reversal_stats(df)
        assert s["n_close"] == 188
        assert s["n_tight"] == 54
        assert s["param_rev"] == 51
        assert s["rvi_rev"] == 53

    def test_one_sided_reversal(self) -> None:
        df = pd.read_csv(_TYPES["one_sided"])
        s = _reversal_stats(df)
        assert s["n_close"] == 148
        assert s["n_tight"] == 36
        assert s["param_rev"] == 36
        assert s["rvi_rev"] == 36


class TestHydraNetReversalRatesAbove90Percent:
    """The paper claims >=94% reversal across all types."""

    def test_all_types_parametric_above_90(self) -> None:
        for label, path in _TYPES.items():
            df = pd.read_csv(path)
            s = _reversal_stats(df)
            if s["n_tight"] > 0:
                rate = s["param_rev"] / s["n_tight"]
                assert rate >= 0.90, f"{label} parametric reversal {rate:.1%} < 90%"

    def test_all_types_rvi_above_90(self) -> None:
        for label, path in _TYPES.items():
            df = pd.read_csv(path)
            s = _reversal_stats(df)
            if s["n_tight"] > 0:
                rate = s["rvi_rev"] / s["n_tight"]
                assert rate >= 0.90, f"{label} RVI reversal {rate:.1%} < 90%"
