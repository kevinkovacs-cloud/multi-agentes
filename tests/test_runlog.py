"""C1 — registro de corridas: hash canónico estable y líneas JSONL válidas."""
import json

from moav_hr.core import runlog


def test_hash_estable_ante_reordenamiento_de_claves():
    a = {"mode": "sim", "k": 3, "nested": {"x": 1, "y": 2}}
    b = {"nested": {"y": 2, "x": 1}, "k": 3, "mode": "sim"}
    assert runlog.config_sha(a) == runlog.config_sha(b)
    assert runlog.config_sha(a) != runlog.config_sha({**a, "k": 4})


def test_log_run_escribe_linea_valida(tmp_path):
    registry = tmp_path / "registry.jsonl"
    cfg = {"mode": "sim", "seed": 7}
    entry = runlog.log_run(cfg, {"mu_rel": 0.7}, registry=registry)
    lines = registry.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    parsed = json.loads(lines[0])
    assert parsed["config_sha"] == runlog.config_sha(cfg) == entry["config_sha"]
    assert parsed["metrics"]["mu_rel"] == 0.7
    assert parsed["seeds"] == 7
    runlog.log_run(cfg, {"mu_rel": 0.8}, registry=registry)     # append, no pisa
    assert len(registry.read_text().strip().splitlines()) == 2


def test_load_config_yaml(tmp_path):
    p = tmp_path / "c.yaml"
    p.write_text("mode: sim\nk: 3\n", encoding="utf-8")
    assert runlog.load_config(str(p)) == {"mode": "sim", "k": 3}
