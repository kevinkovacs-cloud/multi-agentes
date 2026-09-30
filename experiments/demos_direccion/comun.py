"""
Utilidades comunes de los demos para la dirección (Bloque D).

Todo corre en modo sim y con la semántica ACTUAL del código (P = aciertos, K = usos,
U = confiabilidad de Laplace cuando no se pasa `u`). Cada salida lleva los dos rótulos
de abajo. Ningún número de las salidas se escribe a mano: sale de correr el código.

Convención de Sf para el aprendizaje en línea (región 5) de los demos D2–D4:
    Sf = {"outcome": acción correcta según la calificación real del harness}
Es el resultado observado del caso. En el warmup de la PoC (pipeline.warmup) la acción
es la correcta, así que ahí Sf = {"outcome": acción}: el warmup es el caso particular
de esta convención. Acierto (P) = la acción del Matcher coincide con Sf.
"""
from __future__ import annotations
import json
import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from moav_hr.core import fairness  # noqa: E402
from moav_hr.core.theory import Theory, TheoryBase  # noqa: E402
from moav_hr.instances.hr.parser_agent import build_si, normalize_profile  # noqa: E402
from moav_hr.instances.hr.pipeline import HRPipeline, matcher_view, record_of  # noqa: E402

ROTULO_SIM = "ilustrativo, modo sim; no es evidencia experimental"
ROTULO_SEM = ("semántica actual del código; puede cambiar con las decisiones 2 y 5 "
              "de la dirección")
ROTULOS = [ROTULO_SIM, ROTULO_SEM]

REPO = Path(__file__).resolve().parents[2]
OUT_DEFAULT = REPO / "docs" / "demos_direccion"

UMBRAL = 0.75            # umbral de decisión del Matcher (el mismo de matcher_view)
ATTR = "origin_group"
CRITERIO = "demographic_parity"
TAM_VENTANA = 4          # como run_poc: W_SUB = 12 // 3 → 3 ventanas por lote de 12

# paleta oscura (crítica de legibilidad de Becerra: nada de gris claro)
C_AZUL = "#1F3A5F"
C_VERDE = "#0F5C46"
C_ROJO = "#8B1A1A"
C_AMBAR = "#7A4B00"
C_VIOLETA = "#3C3489"
C_TEXTO = "#111111"


# ---------------- salidas ----------------

def out_dir(path: "str | Path | None") -> Path:
    p = Path(path) if path is not None else OUT_DEFAULT
    p.mkdir(parents=True, exist_ok=True)
    return p


def guardar_json(data: dict, nombre: str, destino: Path) -> Path:
    data = {"rotulos": list(ROTULOS), **data}
    ruta = destino / nombre
    ruta.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return ruta


def estilo_figuras() -> None:
    plt.rcParams.update({
        "font.size": 12, "axes.titlesize": 14, "axes.labelsize": 12,
        "xtick.labelsize": 12, "ytick.labelsize": 12, "legend.fontsize": 12,
        "figure.titlesize": 14, "text.color": C_TEXTO, "axes.labelcolor": C_TEXTO,
        "xtick.color": C_TEXTO, "ytick.color": C_TEXTO, "axes.edgecolor": C_TEXTO,
        "savefig.dpi": 200, "figure.dpi": 100,
    })


def pie_rotulos(fig, extra: "list[str] | None" = None, ancho: int = 100) -> None:
    """Rótulos obligatorios al pie de cada figura (texto oscuro, ≥ 12 pt), con los
    renglones cortados para que entren en ~1800 px."""
    import textwrap
    lineas = []
    for texto in list(extra or []) + [ROTULO_SIM.capitalize() + ".",
                                       ROTULO_SEM.capitalize() + "."]:
        lineas.extend(textwrap.wrap(texto, ancho))
    fig.text(0.012, 0.008, "\n".join(lineas), ha="left", va="bottom",
             fontsize=12, color=C_TEXTO, linespacing=1.25)


def num(x: float, nd: int = 2) -> str:
    """Número con coma decimal para las figuras (los JSON conservan el punto)."""
    return f"{x:.{nd}f}".replace(".", ",")


def comas(*axes) -> None:
    """Coma decimal en los ejes numéricos de las figuras."""
    from matplotlib.ticker import FuncFormatter
    f = FuncFormatter(lambda v, _: f"{v:g}".replace(".", ",").replace("-", "−"))
    for ax in axes:
        ax.xaxis.set_major_formatter(f)
        ax.yaxis.set_major_formatter(f)


def guardar_figura(fig, nombre: str, destino: Path) -> Path:
    ruta = destino / nombre
    fig.savefig(ruta, dpi=200, facecolor="white")
    plt.close(fig)
    return ruta


# ---------------- similitud (backend por variable de entorno) ----------------

class backend_similitud:
    """Context manager: fija MOAV_SIMILARITY y lo restaura al salir."""

    def __init__(self, backend: str):
        self.backend = backend
        self._prev = None

    def __enter__(self):
        self._prev = os.environ.get("MOAV_SIMILARITY")
        os.environ["MOAV_SIMILARITY"] = self.backend
        return self

    def __exit__(self, *exc):
        if self._prev is None:
            os.environ.pop("MOAV_SIMILARITY", None)
        else:
            os.environ["MOAV_SIMILARITY"] = self._prev
        return False


# ---------------- teorías: descripción y ranking ----------------

def si_corta(si: dict) -> str:
    """Si en una línea legible para figuras."""
    edu = {"Licenciatura": "Lic", "Maestría": "Mag", "Doctorado": "Doc",
           "Especialización": "Esp"}.get(si.get("edu"), str(si.get("edu")))
    sen = "sí" if si.get("seniority_ok") else "no"
    return f"skills={si.get('skills_match')} · {si.get('exp_band')} · {edu} · sen={sen}"


def teoria_dict(t: Theory) -> dict:
    return {"id": t.id, "si": t.si, "a": t.a, "sf": t.sf, "p": t.p, "k": t.k,
            "k_propio": t.k_own, "u": round(t.u, 4)}


def puesto_en_celda(base: TheoryBase, t: Theory) -> tuple[int, int]:
    """Puesto (1 = seleccionada) de t entre las teorías aplicables a su Si, con la clave
    de TheoryBase.select (Def. 4: U desc, P desc, K asc, recencia desc, id asc)."""
    cands = base.applicable(t.si)
    cands.sort(key=lambda x: (-x.u, -x.p, x.k, -x.created_at, x.id))
    return [c is t for c in cands].index(True) + 1, len(cands)


# ---------------- aprendizaje en línea sobre un lote (regiones 2 → 5) ----------------

def accion_correcta(c) -> str:
    return "ADVANCE" if c.true_qual >= UMBRAL else "REJECT"


def pipeline_vacio(nacido: bool = False) -> HRPipeline:
    """Pipeline sim SIN warmup: la base del Matcher arranca vacía y las teorías nacen
    en la región 5 de cada caso. Con nacido=True el Matcher arranca en Born."""
    pipe = HRPipeline(mode="sim")
    if nacido:
        pipe.matcher.tbo.training_runs = 0
    return pipe


def ejecutar_tarea(pipe: HRPipeline, candidatos, tarea: int,
                   al_cerrar_ventana=None, despues_de_caso=None) -> dict:
    """
    Recorre un lote con el Matcher del pipeline: recupera y decide (región 2), el
    pipeline completa el caso, y el Matcher aprende (región 5) con learn(Si, A, Sf,
    acierto) sin pasar `u` (U := Laplace). Cada TAM_VENTANA casos cierra una ventana:
    fair(W) de las decisiones que implican los scores del Matcher (matcher_view, N3),
    registrado en su historia; si se pasa `al_cerrar_ventana`, se llama después.
    `despues_de_caso(caso, teoria)` se llama al terminar cada caso (para instantáneas).
    """
    m = pipe.matcher
    casos, ventanas, pendientes = [], [], []
    nuevas = 0
    for c in candidatos:
        si = build_si(normalize_profile(c))
        recuperadas = m.retrieve(si)                 # la misma llamada que hace run()
        seleccionada = recuperadas[0] if recuperadas else None
        sel_info = None if seleccionada is None else {
            "id": seleccionada.id, "a": seleccionada.a, "p": seleccionada.p,
            "k": seleccionada.k, "u": round(seleccionada.u, 4)}
        st = pipe.process(c)
        assert st["matcher"]["n_retrieved"] == len(recuperadas)
        accion = "ADVANCE" if st["matcher"]["score"] >= UMBRAL else "REJECT"
        correcta = accion_correcta(c)
        sf = {"outcome": correcta}
        es_nueva = m.theories.find_equal(Theory(si=si, a=accion, sf=sf)) is None
        t = m.learn(si, accion, sf, success=(accion == correcta))
        nuevas += es_nueva
        st["trail"].record(m.name, "TBO", "aprendizaje_teoria", region=5,
                           nueva=es_nueva, p=t.p, k=t.k, u=round(t.u, 4))
        casos.append({
            "tarea": tarea, "candidato_id": c.id, "grupo": c.origin_group,
            "si": si, "n_recuperadas": len(recuperadas), "seleccionada": sel_info,
            "score_matcher": st["matcher"]["score"], "accion": accion,
            "accion_correcta": correcta, "acierto": accion == correcta,
            "decision_pipeline": st["decision"], "teoria_aprendida": t.id,
            "teoria_nueva": es_nueva, "nombre": c.name,
        })
        if despues_de_caso is not None:
            despues_de_caso(casos[-1], t)
        pendientes.append(record_of(st))
        if len(pendientes) == TAM_VENTANA:
            fw = fairness.fair_window(matcher_view(pendientes), ATTR, CRITERIO)
            m.record_window_fairness(fw)
            ventanas.append({"tarea": tarea, "fair_w": fw,
                             "candidatos": [x["candidato_id"] for x in casos[-TAM_VENTANA:]]})
            pendientes = []
            if al_cerrar_ventana is not None:
                al_cerrar_ventana(ventanas[-1])
    return {"casos": casos, "ventanas": ventanas, "teorias_nuevas": nuevas}
