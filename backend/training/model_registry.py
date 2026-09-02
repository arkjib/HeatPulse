"""
model_registry.py
-----------------
Saves and loads approved ML model artifacts and metadata.

Directory layout:
  backend/training/artifacts/
    model_metadata.json          ← latest approved model metadata
    wbgt_h24_v1.pkl              ← joblib-serialized sklearn pipeline
    utci_h24_v1.pkl
    hi_h24_v1.pkl
    ...

Each artifact file stores a single (target, horizon) model.
The metadata JSON stores performance, feature list, and training provenance.
"""
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import joblib

ARTIFACTS_DIR = Path(__file__).parent / "artifacts"
METADATA_FILE = ARTIFACTS_DIR / "model_metadata.json"

# Model status constants
STATUS_READY = "MODEL_READY"
STATUS_NOT_TRAINED = "MODEL_NOT_TRAINED"
STATUS_ERROR = "MODEL_ERROR"


def _ensure_artifacts_dir() -> None:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)


def model_path(target: str, horizon: int, version: str = "v1") -> Path:
    return ARTIFACTS_DIR / f"{target}_h{horizon}_{version}.pkl"


def save_model(
    model: Any,
    target: str,
    horizon: int,
    metadata: Dict[str, Any],
    version: str = "v1",
) -> None:
    """
    Serialize a fitted sklearn pipeline and record metadata.

    Parameters
    ----------
    model    : fitted sklearn estimator or Pipeline
    target   : 'wbgt' | 'utci' | 'hi'
    horizon  : 24 | 48 | 72 | 96 | 120
    metadata : dict containing feature_columns, metrics, data_period, etc.
    version  : artifact version string
    """
    _ensure_artifacts_dir()
    path = model_path(target, horizon, version)
    joblib.dump(model, path)

    # Update (or create) the metadata JSON
    all_meta = _load_all_metadata()
    key = f"{target}_h{horizon}"
    all_meta[key] = {
        "target": target,
        "horizon_hours": horizon,
        "version": version,
        "artifact_path": str(path),
        "saved_at": datetime.now(timezone.utc).isoformat(),
        **metadata,
    }
    all_meta["_status"] = STATUS_READY
    all_meta["_last_updated"] = datetime.now(timezone.utc).isoformat()
    _write_all_metadata(all_meta)


def load_model(target: str, horizon: int, version: str = "v1") -> Tuple[Any, Dict]:
    """
    Load a single (target, horizon) model and its metadata.

    Returns (model, meta_dict).
    Raises FileNotFoundError if not trained yet.
    """
    path = model_path(target, horizon, version)
    if not path.exists():
        raise FileNotFoundError(
            f"No trained model artifact at {path}. "
            "Run training/train.py first."
        )
    model = joblib.load(path)
    all_meta = _load_all_metadata()
    meta = all_meta.get(f"{target}_h{horizon}", {})
    return model, meta


def get_model_status() -> str:
    """Return the overall model registry status string."""
    all_meta = _load_all_metadata()
    return all_meta.get("_status", STATUS_NOT_TRAINED)


def get_all_metadata() -> Dict[str, Any]:
    return _load_all_metadata()


def _load_all_metadata() -> Dict[str, Any]:
    if not METADATA_FILE.exists():
        return {"_status": STATUS_NOT_TRAINED}
    with open(METADATA_FILE, "r") as f:
        return json.load(f)


def _write_all_metadata(data: Dict[str, Any]) -> None:
    _ensure_artifacts_dir()
    with open(METADATA_FILE, "w") as f:
        json.dump(data, f, indent=2, default=str)
