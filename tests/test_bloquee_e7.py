"""Bloque E · E7: el informe final se genera desde las salidas y respeta el lenguaje pedido."""
import re
import shutil
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "experiments" / "parada_tecnica"))
import informe_final  # noqa: E402
from comun_pt import ROTULOS, mayus  # noqa: E402


def test_informe_final_y_guion(tmp_path):
    shutil.copytree(RAIZ / "docs" / "parada_tecnica", tmp_path / "pt")
    informe_final.escribir(tmp_path / "pt")
    md = (tmp_path / "pt" / "INFORME_PARADA_TECNICA.md").read_text(encoding="utf-8")
    for punto in ("Punto 1", "Punto 2a", "Punto 2b", "Punto 3", "Punto 4", "Punto 5",
                  "Preguntas para el encuentro"):
        assert f"## {punto}" in md
    assert md.count("- **Historial:**") == 6 and md.count("- **Comando") == 6
    assert all(mayus(r) in md for r in ROTULOS)
    bajo = md.lower()
    assert "valida" not in bajo and "demuestra la conjetura" not in bajo
    assert "paridad de errores" not in bajo
    guion = (tmp_path / "pt" / "LEEME_REUNION.md").read_text(encoding="utf-8")
    assert sum(1 for x in guion.splitlines() if re.match(r"^\d+\. ", x)) == 10


def _generar_todo():
    """Se carga por ruta con otro nombre: `generar_todo` también es un módulo del Bloque D."""
    import importlib.util
    ruta = RAIZ / "experiments" / "parada_tecnica" / "generar_todo.py"
    spec = importlib.util.spec_from_file_location("generar_todo_parada_tecnica", ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_generar_todo_lista_los_pasos_y_los_documentos_a_mano():
    generar_todo = _generar_todo()
    nombres = [n for n, _ in generar_todo.pasos()]
    assert len(nombres) == len(set(nombres)) and nombres[-1].startswith("Informe final")
    assert "E0_DIAGNOSTICO.md" in generar_todo.A_MANO
