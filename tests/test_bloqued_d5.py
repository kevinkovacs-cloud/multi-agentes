"""Bloque D · D5: diversidad en comité con sesgos programados."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "experiments" / "demos_direccion"))

from comun import ROTULOS  # noqa: E402
from moav_hr.core import fairness  # noqa: E402


def test_d5_json_y_cotas(tmp_path):
    import d5_diversidad
    d5_diversidad.correr(tmp_path)
    d = json.loads((tmp_path / "d5_diversidad.json").read_text(encoding="utf-8"))
    assert d["rotulos"] == ROTULOS
    assert "no es evidencia de la conjetura" in d["rotulo_obligatorio"]
    assert set(d["comites"]) == {"homogeneo", "diverso", "diverso_con_piso"}
    for r in d["comites"].values():
        assert r["d_max"] == fairness.d_max(3)
        assert 0.0 <= r["D"] <= r["d_max"] + 1e-9          # cota de alcanzabilidad (A3)
        assert len(r["disparidad_miembros"]) == 3
        media = sum(r["disparidad_miembros"]) / 3
        assert abs(r["relacion_comite_sobre_media_miembros"] - r["disparidad_comite"] / media) < 1e-3
    # el comité homogéneo tiene menos diversidad que el diverso (mecanismo programado)
    assert d["comites"]["homogeneo"]["D"] < d["comites"]["diverso"]["D"]
    assert (tmp_path / "d5_diversidad.png").exists()
