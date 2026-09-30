"""Bloque D · D3: transferencia maestro→aprendiz con gating por reputación."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "experiments" / "demos_direccion"))

from comun import ROTULOS  # noqa: E402


def test_d3_transferencia_y_contraejemplos(tmp_path):
    import d3_transferencia
    d3_transferencia.correr(tmp_path)
    d = json.loads((tmp_path / "d3_transferencia.json").read_text(encoding="utf-8"))
    assert d["rotulos"] == ROTULOS
    p = d["principal"]
    tau = d["tau"]
    # el resultado del gating coincide con la regla r ≥ τ del código
    assert p["aceptada"] == (d["donante_A"]["reputacion"] >= tau)
    conteo = d["conteo_por_categoria"]
    assert sum(conteo.values()) == len(d["donante_A"]["base"])
    if p["aceptada"]:
        # Alg. 4.10: iguales se funden; similares y nuevas agregan variantes
        assert p["base_receptor_despues"] == (p["base_receptor_antes"]
                                              + conteo["similar"] + conteo["nueva"])
        for f in d["teorias_de_A_en_B"]:
            antes = f["en_B_antes"] or {"p": 0, "k": 0}
            if f["categoria"] == "igual":
                assert f["en_B_despues"]["p"] == f["en_A"]["p"] + antes["p"]
    c1 = d["contraejemplo_r_bajo"]
    assert c1["reputacion_donante"] < tau and not c1["aceptada"]
    assert c1["base_receptor_despues"] == c1["base_receptor_antes"]
    c2 = d["contraejemplo_sin_historia"]
    assert c2["can_donate"] is False and not c2["aceptada"]
    assert c2["base_receptor_despues"] == c2["base_receptor_antes"]
    assert (tmp_path / "d3_transferencia.png").exists()
