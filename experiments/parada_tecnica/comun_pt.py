"""Utilidades comunes de los demos del Bloque E («parada técnica»)."""
from __future__ import annotations
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402,F401

ROTULO_SIM = "ilustrativo, entorno simulado (modo sim); no es evidencia experimental"
ROTULO_SEM = "semántica LLC propuesta; decisiones 2, 4 y 5 pendientes de la dirección"
ROTULOS = [ROTULO_SIM, ROTULO_SEM]

REPO = Path(__file__).resolve().parents[2]
OUT_DEFAULT = REPO / "docs" / "parada_tecnica"
CONFIG = REPO / "configs" / "parada_tecnica.yaml"

C_AZUL, C_VERDE, C_ROJO, C_AMBAR, C_VIOLETA, C_TEXTO = (
    "#1F3A5F", "#0F5C46", "#8B1A1A", "#7A4B00", "#3C3489", "#111111")


CONFIGS = {"v1": REPO / "configs" / "parada_tecnica_v1.yaml", "v2": CONFIG}


def cargar_config(path: "str | Path | None" = None, version: "str | None" = None) -> dict:
    from moav_hr.core.runlog import load_config
    if version is not None:
        path = CONFIGS[version]
    return load_config(str(path or CONFIG))


def out_version(base: "str | Path | None", version: str) -> Path:
    """Salidas de cada versión del pre-registro en su subcarpeta (v1/, v2/)."""
    return out_dir(Path(base if base is not None else OUT_DEFAULT) / version)


def out_dir(path: "str | Path | None") -> Path:
    p = Path(path) if path is not None else OUT_DEFAULT
    p.mkdir(parents=True, exist_ok=True)
    return p


def texto_json(data: dict) -> str:
    """El texto exacto que escribe `guardar_json` (para verificar una corrida contra lo
    commiteado sin escribir nada)."""
    return json.dumps({"rotulos": list(ROTULOS), **data}, ensure_ascii=False, indent=2,
                      default=str) + "\n"


def guardar_json(data: dict, nombre: str, destino: Path) -> Path:
    ruta = destino / nombre
    ruta.write_text(texto_json(data), encoding="utf-8")
    return ruta


def mayus(texto: str) -> str:
    """Primera letra en mayúscula sin tocar el resto (capitalize() rompe «LLC»)."""
    return texto[:1].upper() + texto[1:]


def encabezado_md(titulo: str) -> list[str]:
    return [f"# {titulo}", "", f"> *{mayus(ROTULO_SIM)}.* · *{mayus(ROTULO_SEM)}.*",
            "", "> Generado por código: ningún número de este documento está escrito a mano.", ""]


def num(x: float, nd: int = 2) -> str:
    return f"{x:.{nd}f}".replace(".", ",")


def estilo_figuras() -> None:
    plt.rcParams.update({
        "font.size": 12, "axes.titlesize": 14, "axes.labelsize": 12, "xtick.labelsize": 12,
        "ytick.labelsize": 12, "legend.fontsize": 12, "figure.titlesize": 14,
        "text.color": C_TEXTO, "axes.labelcolor": C_TEXTO, "xtick.color": C_TEXTO,
        "ytick.color": C_TEXTO, "axes.edgecolor": C_TEXTO, "savefig.dpi": 200})


def pie_rotulos(fig, extra: "list[str] | None" = None, ancho: int = 100) -> None:
    import textwrap
    lineas = []
    for t in list(extra or []) + [mayus(ROTULO_SIM) + ".", mayus(ROTULO_SEM) + "."]:
        lineas.extend(textwrap.wrap(t, ancho))
    fig.text(0.012, 0.008, "\n".join(lineas), ha="left", va="bottom", fontsize=12,
             color=C_TEXTO, linespacing=1.25)
