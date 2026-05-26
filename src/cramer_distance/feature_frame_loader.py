"""Load FeatureFrame and PredictionFrame directories.

FeatureFrame loader reimplemented from views-lab00/src/lab_core/feature_frame_loader.py
for replicability and to reduce coupling with the VIEWS platform.
The canonical upstream is maintained in views-lab00.

Pure numpy + json. No dependency on any external VIEWS package.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

logger = logging.getLogger(__name__)

_REQUIRED_FILES = ("y_features.npy", "identifiers.npz", "feature_names.json")
_SUPPORTED_FORMAT_VERSIONS = {1}


def _default_feature_frame_dir() -> Path:
    env = os.environ.get("VIEWS_FEATURE_FRAME_DIR")
    if env:
        return Path(env)
    return Path.home() / "Documents" / "scripts" / "views_platform" / "views-datafactory" / "data" / "assembled" / "feature_frame"


@dataclass(frozen=True)
class FeatureFrameConfig:
    feature_frame_dir: Path = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.feature_frame_dir is None:
            object.__setattr__(
                self, "feature_frame_dir", _default_feature_frame_dir()
            )
        path = Path(self.feature_frame_dir)
        if not path.is_dir():
            raise ValueError(
                f"FeatureFrame directory does not exist: {path}"
            )
        for fname in _REQUIRED_FILES:
            if not (path / fname).is_file():
                raise ValueError(
                    f"Missing required file '{fname}' in {path}"
                )


def load_feature_frame(
    config: FeatureFrameConfig | None = None,
) -> dict[str, Any]:
    """Load a FeatureFrame directory into numpy arrays.

    Returns dict with keys: features, time_ids, unit_ids, feature_names, metadata.
    """
    if config is None:
        config = FeatureFrameConfig()

    path = Path(config.feature_frame_dir)
    logger.info("Loading FeatureFrame from %s", path)

    features: NDArray[np.float32] = np.load(path / "y_features.npy")
    identifiers = dict(np.load(path / "identifiers.npz"))
    with open(path / "feature_names.json") as f:
        feature_names: list[str] = json.load(f)

    for key in ("time", "unit"):
        if key not in identifiers:
            raise ValueError(
                f"Missing required identifier '{key}' in identifiers.npz"
            )

    if features.ndim == 3:
        logger.warning(
            "FeatureFrame has sample dimension (shape %s), using mean",
            features.shape,
        )
        features = features.mean(axis=2)

    time_ids: NDArray[np.int64] = identifiers["time"].astype(np.int64)
    unit_ids: NDArray[np.int64] = identifiers["unit"].astype(np.int64)

    metadata: dict[str, Any] = {}
    meta_path = path / "metadata.json"
    if meta_path.is_file():
        with open(meta_path) as f:
            metadata = json.load(f)
        fmt_version = metadata.get("format_version")
        if fmt_version is not None and fmt_version not in _SUPPORTED_FORMAT_VERSIONS:
            raise ValueError(
                f"Unsupported format_version {fmt_version} in {meta_path}. "
                f"Supported: {_SUPPORTED_FORMAT_VERSIONS}"
            )

    logger.info(
        "Loaded %d observations, %d features, %d times, %d units",
        features.shape[0],
        features.shape[1],
        len(np.unique(time_ids)),
        len(np.unique(unit_ids)),
    )

    return {
        "features": features,
        "time_ids": time_ids,
        "unit_ids": unit_ids,
        "feature_names": feature_names,
        "metadata": metadata,
    }


# ---------------------------------------------------------------------------
# Prediction frame loader (rolling-origin MC Dropout predictions)
# ---------------------------------------------------------------------------

_DEFAULT_PREDICTIONS_DIR = (
    Path(__file__).resolve().parents[2] / "data" / "predictions"
)


def load_prediction_frame(
    target: str,
    predictions_dir: Path | None = None,
    n_origins: int = 13,
) -> dict[str, Any]:
    """Load prediction frames for a target and apply shortest-horizon selection.

    Each origin directory contains y_pred.npy (N, S) and identifiers.npz
    with 'time' and 'unit' arrays. Origin k predicts months starting at
    493+k with 36 steps ahead. For each (time, unit) pair, we keep the
    origin where the step-ahead distance is smallest.

    Args:
        target: Target name, e.g. "lr_sb_best".
        predictions_dir: Root directory containing target subdirectories.
        n_origins: Number of rolling origins (default 13).

    Returns dict with keys:
        predictions: NDArray (N, S) float32 — MC Dropout samples
        time_ids: NDArray (N,) int64
        unit_ids: NDArray (N,) int64
    """
    pred_dir = (predictions_dir or _DEFAULT_PREDICTIONS_DIR) / target
    if not pred_dir.is_dir():
        raise ValueError(f"Prediction directory does not exist: {pred_dir}")

    all_preds = []
    all_times = []
    all_units = []
    all_origins = []

    for origin_idx in range(n_origins):
        origin_dir = pred_dir / f"origin_{origin_idx}"
        if not origin_dir.is_dir():
            raise ValueError(f"Missing origin directory: {origin_dir}")

        preds = np.load(origin_dir / "y_pred.npy")
        ids = dict(np.load(origin_dir / "identifiers.npz"))
        times = ids["time"].astype(np.int64)
        units = ids["unit"].astype(np.int64)

        all_preds.append(preds)
        all_times.append(times)
        all_units.append(units)
        all_origins.append(np.full(len(times), origin_idx, dtype=np.int64))

    preds_cat = np.concatenate(all_preds, axis=0)
    times_cat = np.concatenate(all_times)
    units_cat = np.concatenate(all_units)
    origins_cat = np.concatenate(all_origins)

    # Shortest-horizon selection: origin k starts at time min_time + k,
    # so step = time - (min_time + origin). Lower step = shorter horizon.
    min_time = int(times_cat.min())
    steps = times_cat - (min_time + origins_cat)

    # For each (time, unit), keep the row with the smallest step
    # Build a compound key for grouping
    tu_keys = times_cat * 1_000_000 + units_cat

    # Vectorised: sort by (key, step), then take first occurrence per key
    sort_idx = np.lexsort((steps, tu_keys))
    sorted_keys = tu_keys[sort_idx]
    # First occurrence of each unique key in sorted array
    first_mask = np.concatenate(([True], sorted_keys[1:] != sorted_keys[:-1]))
    keep_idx = sort_idx[first_mask]

    logger.info(
        "Loaded %d predictions for %s (%d origins, %d after shortest-horizon selection)",
        len(preds_cat), target, n_origins, len(keep_idx),
    )

    return {
        "predictions": preds_cat[keep_idx],
        "time_ids": times_cat[keep_idx],
        "unit_ids": units_cat[keep_idx],
    }
