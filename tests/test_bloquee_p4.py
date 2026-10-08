"""Bloque E · E4: el demo P4 escribe la traza por rol, la ABox, SHACL y SPARQL, con rótulos."""
import json
import sys
from pathlib import Path

import pytest
from rdflib import Graph

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "experiments" / "parada_tecnica"))
import p4_traza  # noqa: E402
from comun_pt import ROTULOS, mayus  # noqa: E402


@pytest.fixture(scope="module")
def salida(tmp_path_factory):
    out = tmp_path_factory.mktemp("p4")
    return out, p4_traza.correr(out)


def test_p4_escribe_las_salidas_con_rotulos(salida):
    out, res = salida
    casos = [f"{c}-{n:03d}" for c, n in res["config_equipo"]["casos_traza"].items()]
    for c in casos:
        for ext in ("md", "html"):
            texto = (out / f"p4_traza_{c}.{ext}").read_text(encoding="utf-8")
            assert all(mayus(r) in texto for r in ROTULOS)
            for titulo in ("Parser", "Semantic Matcher", "Bias Auditor", "Orchestrator",
                           "Explainer"):
                assert titulo in texto
    for nombre in ("p4_sparql.md", "p4_shacl.txt", "p4_equipo.json"):
        texto = (out / nombre).read_text(encoding="utf-8")
        assert all(mayus(r) in texto or r in texto for r in ROTULOS)


def test_p4_ttl_conforma_y_las_pruebas_negativas_fallan(salida):
    out, res = salida
    assert res["shacl"]["conforma"]
    assert res["shacl"]["negativa_sigma_p"] and res["shacl"]["negativa_de4"]
    g = Graph().parse(out / "p4_equipo.ttl", format="turtle")
    assert len(g) == res["shacl"]["tripletas"]


def test_p4_estados_ganados_y_json_coherente(salida):
    out, res = salida
    d = json.loads((out / "p4_equipo.json").read_text(encoding="utf-8"))
    assert d["estados_finales"] == res["estados_finales"]
    for rol, info in d["equipo"]["roles"].items():
        assert info["estado"] == "Born" or info["promociones"]     # nadie fija estados a mano
    assert d["estados_finales"]["bias_auditor"] == "Born"           # consecuencia pre-registrada
    assert d["decisiones_finales"]["ESCALATE_HUMAN"] == 0           # la regla no deriva con w = 20
