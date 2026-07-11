"""
Registro de corridas (C1): reproducibilidad auditable de los experimentos.

Cada corrida registra una línea JSON en runs/registry.jsonl con:
  · config_sha: SHA-256 del config CANÓNICO (claves ordenadas — el hash es estable
    ante reordenamientos del YAML);
  · git_sha: commit del código que corrió;
  · timestamp UTC, seeds y métricas resultantes.

Con (config_sha, git_sha, seeds) cualquier corrida es re-ejecutable y auditable:
la reproducibilidad se DEMUESTRA, no se promete.
"""
from __future__ import annotations
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

DEFAULT_REGISTRY = Path("runs/registry.jsonl")


def canonical_config(config: dict[str, Any]) -> str:
    """Serialización canónica (claves ordenadas, sin espacios) — base del hash."""
    return json.dumps(config, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"))


def config_sha(config: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_config(config).encode("utf-8")).hexdigest()


def git_sha() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                              capture_output=True, text=True, timeout=5,
                              check=True).stdout.strip()
    except Exception:
        return "unknown"


def log_run(config: dict[str, Any], metrics: dict[str, Any],
            registry: Optional[Path] = None) -> dict[str, Any]:
    """Registra la corrida; devuelve la entrada escrita."""
    path = Path(registry) if registry is not None else DEFAULT_REGISTRY
    path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "config_sha": config_sha(config),
        "git_sha": git_sha(),
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "seeds": config.get("seed", config.get("seeds")),
        "config": config,
        "metrics": metrics,
    }
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")
    return entry


def load_config(path: str) -> dict[str, Any]:
    """Carga un YAML de configs/ (C1)."""
    import yaml
    with open(path, encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    if not isinstance(cfg, dict):
        raise ValueError(f"config inválida (se esperaba un mapeo YAML): {path}")
    return cfg
