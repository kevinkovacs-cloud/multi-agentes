"""Bloque E · E6 v2: ê por celda (Si, A) puede cambiar la acción; sin evidencia, α = 1."""
from moav_hr.core.equidad_roles import RegistroE
from moav_hr.core.planificador import PlanificadorLLC
from moav_hr.core.theory import TheoryBase

SI = {"skills_match": 2, "exp_band": "senior", "edu": "Licenciatura", "seniority_ok": True}


def _base():
    b = TheoryBase()
    b.registrar_llc(SI, "ADVANCE", {"calificado": True}, 1.0)
    b.registrar_llc(SI, "REJECT", {"calificado": False}, 1.0)
    for t in b.theories:                                   # U de la acción, parecidas
        t.u = 0.62 if t.a == "ADVANCE" else 0.58
    return b


def _registro(advance_parejo: bool, n: int = 10):
    r = RegistroE()
    pl = PlanificadorLLC(TheoryBase(), ("ADVANCE", "REJECT"))
    for g in ("AR", "no-AR"):
        for i in range(n):
            ok_adv = True if (advance_parejo or g == "AR") else (i % 2 == 0)
            r.registrar(pl.clave_celda(SI, "ADVANCE"), g, ok_adv)
            r.registrar(pl.clave_celda(SI, "REJECT"), g, True)
    return r


def _planificador(registro, alpha=0.5):
    return PlanificadorLLC(_base(), ("ADVANCE", "REJECT"), alpha=alpha, m_min=5,
                           validez_minima=0.5, validez_estricta=False, equidad="celda",
                           registro_celda=registro)


def test_la_equidad_por_celda_puede_cambiar_la_accion():
    plan = _planificador(_registro(advance_parejo=False)).planificar(SI, "WIO", "ADVANCE")
    assert plan.ajuste_equidad == "aplicado"
    assert plan.accion == "REJECT" and plan.alpha_1["accion"] == "ADVANCE"


def test_con_evidencia_pareja_no_cambia():
    plan = _planificador(_registro(advance_parejo=True)).planificar(SI, "WIO", "ADVANCE")
    assert plan.ajuste_equidad == "aplicado" and plan.accion == "ADVANCE"


def test_sin_evidencia_en_una_accion_alfa_1_para_todas():
    plan = _planificador(_registro(advance_parejo=False, n=3)).planificar(SI, "WIO", "ADVANCE")
    assert plan.ajuste_equidad == "no aplicable: falta evidencia"
    assert plan.accion == "ADVANCE" and not plan.equidad_usada


def test_documento_de_metricas_con_terminos_precisos(tmp_path):
    import shutil
    import sys
    from pathlib import Path
    raiz = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(raiz / "experiments" / "parada_tecnica"))
    import metricas_equidad_doc
    from comun_pt import ROTULOS, mayus
    for f in ("p5_metricas_equidad.json", "p5_sesgo_programado.json", "p5_equidad_v2.json",
              "p5_control_post_hoc.json"):
        shutil.copy(raiz / "docs" / "parada_tecnica" / f, tmp_path / f)
    md = Path(metricas_equidad_doc.escribir(tmp_path)).read_text(encoding="utf-8")
    assert "paridad de errores" not in md.lower()
    for termino in ("Paridad demográfica", "Paridad de aciertos", "Odds igualadas",
                    "Paridad de tasa de error", "no pre-registrado"):
        assert termino in md
    assert all(mayus(r) in md for r in ROTULOS)
