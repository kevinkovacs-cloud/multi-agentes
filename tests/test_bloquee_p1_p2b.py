"""Bloque E · E2.7–E2.8: demos P1 (ciclo de vida punto a punto) y P2b (planificador)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "experiments" / "parada_tecnica"))

from comun_pt import ROTULOS  # noqa: E402


def test_p1_traza_y_reproducibilidad(tmp_path):
    import p1_teoria_punto_a_punto as p1
    s = p1.correr(tmp_path / "a")
    p1.correr(tmp_path / "b")
    a = (tmp_path / "a" / "p1.json").read_text(encoding="utf-8")
    assert a == (tmp_path / "b" / "p1.json").read_text(encoding="utf-8")   # determinista
    d = json.loads(a)
    assert d["rotulos"] == ROTULOS
    assert d["invariante_sigma_p_igual_k"] is True
    assert d["teoria_estrella"]["nacimiento"]["ciclo"] == 1
    assert d["teoria_estrella"]["iri"].startswith("http")
    n = d["config"]["n_intervalo"]
    assert len(d["evaluaciones"]) == sum(c["ciclos"] // n for c in d["resultado"]["capas"])
    traza = (tmp_path / "a" / "p1_traza_ciclo1.md").read_text(encoding="utf-8")
    assert all(f"| R{r} (" in traza for r in range(1, 8))
    assert (tmp_path / "a" / "p1_linea_de_tiempo.png").exists()
    assert s["resultado"]["estado_final"] in ("Born", "Novice", "Trained", "Mature")


def test_p2b_y_el_informe(tmp_path):
    import p1_teoria_punto_a_punto as p1
    import p2b_planificador as p2b
    import informe_e2
    p1.correr(tmp_path)
    s = p2b.correr(tmp_path)
    ci = s["caso_i_misma_si"]
    assert ci["si_igual_a_t_estrella"] is True
    assert ci["alpha_1"]["motivo"] in ("celda", "azar_no_probada", "azar_bio")
    if s["caso_iii_sin_nada_aplicable"]:
        assert s["caso_iii_sin_nada_aplicable"]["en_wio"]["motivo"] == "azar_bio"
    texto = informe_e2.escribir(tmp_path)
    assert "Resultados que no fueron los esperados" in texto
    assert ROTULOS[0][1:] in texto and ROTULOS[1][1:] in texto
