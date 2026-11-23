"""Administrator-editable scoring configuration, stored as JSON in the instance folder."""
import json
import os

from flask import current_app

from ..ai.matching.scoring import DEFAULT_WEIGHTS, ORDER
from ..ai.matching.similarity import MODES

DEFAULT = {"weights": {k: round(v * 100) for k, v in DEFAULT_WEIGHTS.items()}, "semantic_mode": "sbert", "blend_alpha": 0.5}


class ConfigError(ValueError):
    pass


def validate(cfg: dict) -> dict:
    w = cfg.get("weights", {})
    if set(w) != set(ORDER) or any(not isinstance(v, int) or isinstance(v, bool) or not 0 <= v <= 100 for v in w.values()):
        raise ConfigError("Each weight must be a whole number from 0 to 100.")
    if sum(w.values()) != 100:
        raise ConfigError(f"Weights must total 100 (currently {sum(w.values())}).")
    if cfg.get("semantic_mode") not in MODES:
        raise ConfigError("Unknown semantic mode.")
    alpha = cfg.get("blend_alpha", 0.5)
    if not isinstance(alpha, (int, float)) or not 0 <= alpha <= 1:
        raise ConfigError("Blend factor must be between 0 and 1.")
    return {"weights": dict(w), "semantic_mode": cfg["semantic_mode"], "blend_alpha": float(alpha)}


def _path() -> str:
    return os.path.join(current_app.instance_path, "scoring_config.json")


def load() -> dict:
    try:
        with open(_path(), encoding="utf-8") as fh:
            return validate(json.load(fh))
    except (FileNotFoundError, ValueError, TypeError):
        return json.loads(json.dumps(DEFAULT))


def save(cfg: dict) -> dict:
    cfg = validate(cfg)
    os.makedirs(current_app.instance_path, exist_ok=True)
    tmp = _path() + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(cfg, fh, indent=2)
    os.replace(tmp, _path())
    return cfg


def fractions(cfg: dict) -> dict:
    return {k: v / 100 for k, v in cfg["weights"].items()}
