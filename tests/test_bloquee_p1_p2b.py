"""Bloque E · E2.7–E2.8: demos P1 (ciclo de vida punto a punto) y P2b (planificador), v1 y v2."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "experiments" / "parada_tecnica"))

from comun_pt import ROTULOS  # noqa: E402


@pytest.mark.parametrize("version", ["v1", "v2"])
def test_p1_traza_y_reproducibilidad(tmp_path, version):
    import p1_teoria_punto_a_punto as p1
    s = p1.correr(tmp_path / "a", version)
    p1.correr(tmp_path / "b", version)
    a = (tmp_path / "a" / version / "p1.json").read_text(encoding="utf-8")
    assert a == (tmp_path / "b" / version / "p1.json").read_text(encoding="utf-8")   # determinista
    d = json.loads(a)
    assert d["rotulos"] == ROTULOS and d["config"]["version"] == version
    assert d["invariante_sigma_p_igual_k"] is True
    assert d["teoria_estrella"]["nacimiento"]["ciclo"] == 1
    n = d["config"]["n_intervalo"]
    capas = d["resultado"]["capas"]
    assert len(d["evaluaciones"]) == sum(c["ciclos"] // n for c in capas)
    traza = (tmp_path / "a" / version / "p1_traza_ciclo1.md").read_text(encoding="utf-8")
    assert all(f"| R{r} (" in traza for r in range(1, 8))
    assert (tmp_path / "a" / version / "p1_linea_de_tiempo.png").exists()
    assert s["resultado"]["estado_final"] in ("Born", "Novice", "Trained", "Mature")


def test_p2b_informes_y_comparacion(tmp_path):
    import p1_teoria_punto_a_punto as p1
    import p2b_planificador as p2b
    import informe_e2
    for v in ("v1", "v2"):
        p1.correr(tmp_path, v)
        s = p2b.correr(tmp_path, v)
        assert s["caso_i_misma_si"]["si_igual_a_t_estrella"] is True
        texto = informe_e2.escribir(tmp_path, v)
        assert "Resultados que no fueron los esperados" in texto
        assert ROTULOS[0][1:] in texto and ROTULOS[1][1:] in texto
    comp = informe_e2.comparar(tmp_path)
    assert "| Estado final |" in comp
