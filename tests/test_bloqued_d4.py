"""Bloque D · D4b: maduración sobre el caso y segunda tarea (demo)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "experiments" / "demos_direccion"))

from comun import ROTULOS  # noqa: E402
from moav_hr.core import stats  # noqa: E402


def test_d4_puntual_y_certificado(tmp_path):
    import d4_maduracion
    d4_maduracion.correr(tmp_path)
    d = json.loads((tmp_path / "d4_maduracion.json").read_text(encoding="utf-8"))
    assert d["rotulos"] == ROTULOS
    g = d["gate"]
    assert d["m_min_ventanas_perfectas"] == stats.m_min_gate(1.0, g["tau"], g["delta"])
    orden = ["born", "novato", "trained", "mature"]
    for modo in ("puntual", "certificado"):
        linea = d[modo]["linea_de_tiempo"]
        assert linea[0]["estado_antes"] == "born"
        pos = [orden.index(v["estado_despues"]) for v in linea]
        assert pos == sorted(pos)                      # el ciclo nunca retrocede
        for v in linea:                                # a lo sumo un paso por ventana
            assert orden.index(v["estado_despues"]) - orden.index(v["estado_antes"]) in (0, 1)
    # el certificado no puede aprobar con menos ventanas que m_min(1.0)
    n = len(d["certificado"]["linea_de_tiempo"])
    if n < d["m_min_ventanas_perfectas"]:
        assert d["certificado"]["estado_final"] == "born"
        assert all(v["aviso"] for v in d["certificado"]["linea_de_tiempo"])
    assert d["tarea_2_reutiliza_teorias"]["casos"] == 12
    assert (tmp_path / "d4_linea_de_tiempo.png").exists()
