"""Bloque D · D2: creación e iteración de una teoría en dos tareas."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "experiments" / "demos_direccion"))

from comun import ROTULOS  # noqa: E402
from tarea2 import generar_tarea2  # noqa: E402
from moav_hr.instances.hr.parser_agent import build_si, normalize_profile  # noqa: E402
from moav_hr.instances.hr.synthetic import CANDIDATES  # noqa: E402


def _si(c):
    return json.dumps(build_si(normalize_profile(c)), sort_keys=True)


def test_tarea2_determinista_y_con_si_repetidas():
    a, b = generar_tarea2(), generar_tarea2()
    assert a == b                                        # semilla fija
    assert {c.id for c in a}.isdisjoint({c.id for c in CANDIDATES})
    assert {_si(c) for c in a} & {_si(c) for c in CANDIDATES}   # hay Si repetidas


def test_d2_json_y_consistencia(tmp_path):
    import d2_ciclo_teoria
    d2_ciclo_teoria.correr(tmp_path)
    data = json.loads((tmp_path / "d2_ciclo_teoria.json").read_text(encoding="utf-8"))
    assert data["rotulos"] == ROTULOS
    assert data["tarea_1"]["n_casos"] == len(CANDIDATES)
    nuevas = data["teorias_nuevas_por_tarea"]
    assert nuevas == [data["tarea_1"]["teorias_nuevas"], data["tarea_2"]["teorias_nuevas"]]
    assert sum(nuevas) == len(data["base_final"])        # cada teoría nace una sola vez
    seg = data["teoria_seguida"]
    ks = [u["k"] for u in seg["usos"]]
    assert ks == list(range(1, len(ks) + 1))            # un uso = K+1
    assert seg["nacimiento"]["k"] == 1
    assert all(u["p"] <= u["k"] for u in seg["usos"])
    assert (tmp_path / "d2_evolucion_PKU.png").exists()


def test_d2_reproducible(tmp_path):
    import d2_ciclo_teoria
    d2_ciclo_teoria.correr(tmp_path / "a")
    d2_ciclo_teoria.correr(tmp_path / "b")
    assert ((tmp_path / "a" / "d2_ciclo_teoria.json").read_text(encoding="utf-8")
            == (tmp_path / "b" / "d2_ciclo_teoria.json").read_text(encoding="utf-8"))
