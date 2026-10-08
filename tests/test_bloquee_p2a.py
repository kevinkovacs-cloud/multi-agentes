"""Bloque E · E3: demo P2a (cooperación, colaboración y transferencia) y su informe."""
import json
import sys
from pathlib import Path

from rdflib import Graph

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "experiments" / "parada_tecnica"))

from comun_pt import ROTULOS  # noqa: E402


def test_p2a_determinista_axiomas_y_procedencia(tmp_path):
    import p1_teoria_punto_a_punto as p1
    import p2a_compartir as p2a
    import informe_e3
    s = p2a.correr(tmp_path / "a")
    p2a.correr(tmp_path / "b")
    a = (tmp_path / "a" / "v2" / "p2a.json").read_text(encoding="utf-8")
    assert a == (tmp_path / "b" / "v2" / "p2a.json").read_text(encoding="utf-8")
    d = json.loads(a)
    assert d["rotulos"] == ROTULOS
    if d["detenido"]:
        return                                            # se frena y se avisa (E2_RESPUESTA §4)
    op = d["operaciones"]
    assert not op["contraejemplo_cooperacion_A_B"]["aceptada"]
    assert "[a]" in op["contraejemplo_cooperacion_A_B"]["axioma"]
    assert not op["contraejemplo_colaboracion_B_A"]["aceptada"]
    assert "[b]" in op["contraejemplo_colaboracion_B_A"]["axioma"]
    for r in op.values():
        if r["aceptada"]:
            assert r["invariante_receptor"] and r["invariante_donante"]
    g = Graph().parse(tmp_path / "a" / "v2" / "p2a_procedencia.ttl", format="turtle")
    assert len(g) > 0
    for seg in s["seguimiento"].values():
        assert seg["prov_wasDerivedFrom"]                  # la cadena existe en el receptor
    p1.correr(tmp_path / "a", "v2")
    assert "Resultados que no fueron los esperados" in informe_e3.escribir(tmp_path / "a")
