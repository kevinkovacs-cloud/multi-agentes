"""Bloque D · D7: generar_todo escribe NUMEROS_PARA_PLACAS.md desde las salidas."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "experiments" / "demos_direccion"))

from comun import ROTULO_SEM, ROTULO_SIM  # noqa: E402


def test_generar_todo_sin_modelo(tmp_path):
    import generar_todo
    texto = generar_todo.correr(tmp_path, backend="token-cosine")
    md = (tmp_path / "NUMEROS_PARA_PLACAS.md").read_text(encoding="utf-8")
    assert md == texto
    for d in ("D1", "D2", "D3", "D4", "D5"):
        assert f"## {d} · " in md
    assert md.count(ROTULO_SIM) >= 5 and md.count(ROTULO_SEM) >= 5
    assert "no es evidencia de la conjetura de atenuación" in md
    assert "embeddings no disponibles" in md                  # D1 sin modelo lo reporta
    for f in ("d1_embeddings.json", "d2_ciclo_teoria.json", "d3_transferencia.json",
              "d4_maduracion.json", "d5_diversidad.json", "d2_evolucion_PKU.png",
              "d3_transferencia.png", "d4_linea_de_tiempo.png", "d5_diversidad.png"):
        assert (tmp_path / f).exists()
