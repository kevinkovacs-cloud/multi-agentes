"""
Ítem B (Becerra) — explicabilidad derivada de la serialización (XAI como feature).

Trazabilidad ≠ explicabilidad: un audit trail puede estar completo y aun así ser
ininteligible. Este módulo deriva la explicación A PARTIR DEL GRAFO RDF SERIALIZADO
(no del estado en memoria), y la articula para dos destinatarios con necesidades distintas:

  - regulador / auditor: completitud y cumplimiento (umbrales, regiones, secuencia,
    por qué se bloqueó/escaló) — alineado con EU AI Act Art. 12-14.
  - usuario afectado: comprensible y accionable, en lenguaje llano.

Alcance honesto: el aporte es la DERIVACIÓN desde la serialización + la distinción de
destinatarios. No implementa XAI por atribución (SHAP/LIME/contrafácticos).
"""
from __future__ import annotations
from rdflib import Graph

from moav_hr.core.ontology.queries import Q_EVENTS_ORDERED, run

_Q_DECISION = """
PREFIX moacv: <https://moav-hr.diit.unlam.edu.ar/ontology/>
SELECT ?resultado ?score ?sesgo ?umbral ?tipoSesgo ?bloqueada
WHERE {
  ?d a moacv:Decision ; moacv:resultado ?resultado .
  OPTIONAL { ?d moacv:scoreMatching  ?score }
  OPTIONAL { ?d moacv:sesgoDetectado ?sesgo }
  OPTIONAL { ?d moacv:umbralEquidad  ?umbral }
  OPTIONAL { ?d moacv:tipoSesgo      ?tipoSesgo }
  OPTIONAL { ?d moacv:bloqueada      ?bloqueada }
}
"""


def explain_from_rdf(source: "Graph | str") -> dict:
    """
    Deriva explicaciones (regulador y usuario) desde un grafo de procedencia RDF.

    `source` puede ser un rdflib.Graph o una cadena Turtle ya serializada; en este último
    caso se reconstruye el grafo, demostrando que la explicación sale de la SERIALIZACIÓN.
    Devuelve {"regulador": str, "usuario": str, "datos": {...}}.
    """
    g = source if isinstance(source, Graph) else Graph().parse(data=source, format="turtle")

    dec = run(g, _Q_DECISION)
    if not dec:
        return {"regulador": "Sin decisión registrada en el grafo.",
                "usuario": "No hay una decisión registrada para tu caso.", "datos": {}}
    d = dec[0]
    resultado = d.get("resultado", "—")
    score = d.get("score")
    sesgo = d.get("sesgo")
    umbral = d.get("umbral")
    tipo_sesgo = d.get("tipoSesgo")
    bloqueada = str(d.get("bloqueada", "")).lower() in ("true", "1")
    escalada = resultado == "ESCALATE_HUMAN"

    eventos = run(g, Q_EVENTS_ORDERED)
    secuencia = " → ".join(f"{int(e['orden'])+1}. {e['tipo']}" for e in eventos)

    # --- destinatario: regulador / auditor (completitud + cumplimiento) ---
    reg = [f"[Auditoría · regulador] Decisión registrada: {resultado}"]
    if score is not None:
        reg.append(f"score ajustado {float(score):.3f}")
    if sesgo is not None and umbral is not None:
        rel = "≥" if float(sesgo) >= float(umbral) else "<"
        reg.append(f"sesgo detectado Δ={float(sesgo):.3f} {rel} umbral τ={float(umbral):.3f}"
                   + (f" ({tipo_sesgo})" if tipo_sesgo else ""))
    reg.append("bloqueada por el Monitor de Equidad y escalada a revisión humana"
               if bloqueada else "dentro del umbral de equidad")
    if secuencia:
        reg.append(f"secuencia de ejecución trazable ({len(eventos)} eventos): {secuencia}")
    reg.append("audit trail RDF/PROV-O recuperable (EU AI Act Art. 12-14)")
    regulador = "; ".join(reg) + "."

    # --- destinatario: usuario afectado (lenguaje llano + accionable) ---
    if escalada:
        usuario = ("Tu evaluación fue derivada a una revisión humana. Un sistema automático "
                   "detectó que el resultado podía estar influido por un factor ajeno a tus "
                   "capacidades, así que una persona revisará tu caso antes de decidir.")
    elif resultado == "ADVANCE":
        usuario = ("Tu perfil avanzó a la siguiente etapa del proceso; no se detectaron "
                   "señales de trato desigual en la evaluación automática.")
    elif resultado == "REJECT":
        usuario = ("Tu perfil no avanzó en esta instancia según los criterios del puesto. "
                   "Podés solicitar una revisión si considerás que hubo un error.")
    else:
        usuario = f"El resultado de tu evaluación fue: {resultado}."

    return {"regulador": regulador, "usuario": usuario,
            "datos": {"resultado": resultado, "bloqueada": bloqueada, "escalada": escalada,
                      "n_eventos": len(eventos)}}
