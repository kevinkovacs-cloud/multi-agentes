"""
Entorno simulado por capa para el modo LLC — instancia HR (bloque E · DE-8, P1 y P3).

REGLAS PRE-REGISTRADAS. Se fijaron y documentaron ANTES de la primera corrida de P1, en un
commit propio junto con `configs/parada_tecnica.yaml`; no se ajustan después para que algo
«dé». Un cambio va en un commit nuevo, con su motivo, y se reporta en el informe.

Análogo del simulador del LLC (Webots, §4.6): un escenario por capa (BIO, TBO, WIO) con
complejidad creciente, como en §4.5 (Ierache 2010, pp. 124–126). Casos sintéticos
generados con semilla. El entorno responde DESPUÉS de la acción (región 3), nunca antes.

1. Catálogo de situaciones (Si = build_si: skills clave, banda de experiencia, educación y
   antigüedad mínima). Acotado, para que las teorías se reutilicen:
     · BIO: educación {Licenciatura} × banda {junior, senior} × skills clave {0..3} = 8 celdas;
     · TBO: educación {Licenciatura, Maestría} × lo mismo = 16 celdas (8 nuevas);
     · WIO: educación {Licenciatura, Maestría, Doctorado} × lo mismo = 24 celdas (8 nuevas).
   Frecuencia: uniforme sobre las celdas del catálogo de la capa. La banda «mid» no aparece.
2. Verdad latente (calificado sí/no), igual para todos los grupos: con probabilidad 0,9 si la
   Si cumple los requisitos del puesto (antigüedad mínima y al menos 1 skill clave) y con
   probabilidad 0,1 si no. La educación no cambia la verdad.
3. Operador BIO del Matcher (regla del diseñador, imperfecta a propósito): ADVANCE si la Si
   tiene al menos 2 skills clave; REJECT si no. Ignora la antigüedad y es exigente con los
   skills, así que la mayoría de las veces se equivoca en 3 de cada 8 celdas: junior con 2 o 3
   skills (avanza a no calificados) y senior con 1 skill (rechaza a calificados). Si
   acertara todo, nadie podría superar al SAR neutro (P1).
4. Respuesta del entorno en la región 3 (Sf = {"calificado": …}):
     · BIO y TBO: la etiqueta del escenario de entrenamiento (la verdad latente del caso);
     · WIO: la revisión humana simulada (`human_sim`, modo `noisy`), que invierte la verdad
       con probabilidad ε (configs: `ruido_wio_epsilon`).
5. Atributo protegido: el grupo (AR / no-AR) se asigna alternado por índice de caso (en cada
   intervalo de 20 hay 10 y 10), independiente de la Si y de la verdad. Vive solo en el
   plano de auditoría (Ω y E(t)); nunca entra en Si, en A ni en los prompts (DE-4).
6. Campos del Candidate que el modo LLC no usa: match_score = 0,0 y bias_risk = "low".
   true_qual codifica la verdad latente para human_sim (0,85 calificado / 0,65 no).

`describir_entorno()` calcula, a partir de estas reglas y SIN correr ningún agente, la tabla
de celdas, su frecuencia, la precisión esperada del operador BIO por celda y la de la mejor
acción por celda; `experiments/parada_tecnica/preregistro.py` la escribe en
`docs/parada_tecnica/E2_PREREGISTRO_ENTORNO.md`.

E4 · reglas de los demás roles (pre-registro E4, 08/10/2026; commit propio antes de correr P4)
-----------------------------------------------------------------------------------------
7. Parser. Cada caso llega como un documento (el CV) en una de seis plantillas; la plantilla
   es la celda del Parser (formato, estructura, etiquetas). Frecuencia por grupo declarada
   (`FRECUENCIA_PARSER`): los CV del grupo no-AR llegan más seguido con etiquetas en
   sinónimos, en HTML de portales o en texto libre. Es un canal proxy declarado (B3): la Si
   del Parser no contiene el atributo protegido, pero su distribución depende del grupo. El
   documento trae datos personales (origen, edad, género), como un CV real. Con probabilidad
   `P_DEFECTO_DOCUMENTO` = 0,1 el documento omite la educación.
     · R1: formato, estructura y etiquetas del documento (`percibir_documento`).
     · R2: `reglas_estrictas` (operador BIO: lee solo etiquetas canónicas, también dentro de
       un JSON anidado) o `diccionario_sinonimos` (sinónimos de campos, vocabulario de skills
       y expresiones «N años»; no desciende en un JSON anidado).
     · R3: el entorno valida el perfil extraído contra el shape SHACL del perfil
       (`PERFIL_SHAPE_TTL`): completo (skills, experiencia y educación), parcial (uno o dos),
       fallido (ninguno). Fuga = el perfil trae un campo fuera del shape (`sh:closed`).
     · u: 1 si es completo y sin fuga; 0,5 si es parcial; 0 si falla o hay fuga.
   Resultado sin defecto de cada estrategia en cada plantilla: `RESULTADO_PARSER` (regla
   declarada; un test verifica que el código de las estrategias la cumple). Con el defecto,
   completo pasa a parcial.
8. Matcher en el equipo. Percibe `build_si` del perfil EXTRAÍDO por el Parser (un campo
   faltante cuenta como skills = [], experiencia = 0, educación = «—»). La verdad latente y la
   respuesta del entorno son las de las reglas 2 y 4, sobre el candidato real.
9. Bias Auditor (DE-6). Un ciclo por ventana de `ventana` casos del equipo.
     · R1: bandas de n por grupo y de la brecha de paridad observada en las decisiones del
       Matcher, y si LCB_δ(|Δ_DP|) > τ_b (`situacion_ventana`).
     · R2: la regla certificada (`regla_certificada`): DERIVAR si LCB > τ_b; si no, LIBERAR.
       La teoría no decide.
     · R3: revisión de la ventana (`revisar_ventana`): etiqueta del escenario en BIO y TBO,
       `human_sim` noisy en WIO. Sesgo confirmado si LCB_δ(|Δ de tasas de error del
       Matcher|) > τ_b, el mismo estándar de evidencia. Se registra también la banda de la
       brecha de errores observada.
     · u: 1 si la intervención coincide con la confirmación; 0 si no.
   Consecuencia calculable sin correr: con ventanas de 20 (10 por grupo) la LCB más alta
   posible es menor que τ_b, así que la regla no puede derivar ni la revisión confirmar.
10. Explainer.
     · R1: tipo de la decisión final (avanza, rechaza, deriva), destinatario (regulador o
       usuario, sorteado 50/50 con semilla por caso) y motivos (varios si el Matcher decidió
       con una teoría; uno si decidió por exploración o por su operador BIO).
     · R2: `por_factores` (operador BIO), `contrafactica` o `regulatoria`.
     · R3: el entorno arma el grafo RDF del caso y verifica por SPARQL
       (`verificar_explicacion`) que estén los elementos requeridos (`requisitos_explicacion`)
       y que los que llevan un hecho (resultado, motivo, factores, dictamen y traza)
       coincidan con el grafo.
     · u: 1 si la explicación está completa; 0 si no.

`describir_entorno_e4()` calcula, sin correr ningún agente, las tasas esperadas por (celda de
Si, estrategia); `experiments/parada_tecnica/preregistro_e4.py` las escribe en
`docs/parada_tecnica/E4_PREREGISTRO.md`.
"""
from __future__ import annotations
import itertools
import random
import re
from dataclasses import dataclass
from typing import Any

from moav_hr.instances.hr.human_sim import resolve as human_resolve
from moav_hr.instances.hr.parser_agent import build_si, normalize_profile
from moav_hr.instances.hr.synthetic import JOB, Candidate

ACCIONES = ("ADVANCE", "REJECT")
CAPAS = ("BIO", "TBO", "WIO")
SKILLS_CLAVE = tuple(JOB["key_skills"])
SKILLS_OTRAS = ("Java", "SQL", "Docker", "React", "AWS", "Scrum")   # conocidas por el Parser
CATALOGO = {
    "BIO": {"edu": ("Licenciatura",), "banda": ("junior", "senior"), "skills": (0, 1, 2, 3)},
    "TBO": {"edu": ("Licenciatura", "Maestría"), "banda": ("junior", "senior"),
            "skills": (0, 1, 2, 3)},
    "WIO": {"edu": ("Licenciatura", "Maestría", "Doctorado"), "banda": ("junior", "senior"),
            "skills": (0, 1, 2, 3)},
}
Q_REQUISITOS, Q_SIN_REQUISITOS = 0.9, 0.1
TQ_CALIFICADO, TQ_NO_CALIFICADO = 0.85, 0.65
ORIGENES_NO_AR = ("BR", "CL", "CO", "SY", "IN", "EG")


def cumple_requisitos(si: dict) -> bool:
    """Requisitos del puesto (JOB): antigüedad mínima y al menos 1 skill clave."""
    return bool(si["seniority_ok"]) and si["skills_match"] >= 1


def prob_calificado(si: dict) -> float:
    return Q_REQUISITOS if cumple_requisitos(si) else Q_SIN_REQUISITOS


def operador_bio_matcher(si: dict) -> str:
    """Operador BIO del Matcher (regla del diseñador): ADVANCE si hay ≥ 2 skills clave."""
    return "ADVANCE" if si["skills_match"] >= 2 else "REJECT"


@dataclass(frozen=True)
class Caso:
    """Caso del escenario: el candidato (lo que se percibe) y su verdad latente (que el
    agente nunca lee: el entorno la usa recién en la región 3)."""
    indice: int
    capa: str
    candidato: Candidate
    calificado: bool

    @property
    def grupo(self) -> str:
        return self.candidato.origin_group


def _anios(banda: str, rng: random.Random) -> int:
    return rng.randint(0, 2) if banda == "junior" else rng.randint(8, 15)


def generar_escenario(capa: str, n: int, semilla: int) -> list[Caso]:
    """n casos de la capa, con semilla propia de la capa (semilla + índice de la capa)."""
    if capa not in CAPAS:
        raise ValueError(f"capa debe ser una de {CAPAS}")
    rng = random.Random(semilla + CAPAS.index(capa))
    cat = CATALOGO[capa]
    celdas = list(itertools.product(cat["edu"], cat["banda"], cat["skills"]))
    casos = []
    for i in range(n):
        edu, banda, s = rng.choice(celdas)
        skills = tuple(rng.sample(SKILLS_CLAVE, s) + rng.sample(SKILLS_OTRAS, 3 - s))
        exp = _anios(banda, rng)
        no_ar = i % 2 == 1
        origen = ORIGENES_NO_AR[(i // 2) % len(ORIGENES_NO_AR)] if no_ar else "AR"
        genero = "F" if (i // 2) % 2 == 0 else "M"
        edad = rng.randint(23, 50)
        cand_tmp = Candidate(0, "", genero, edad, origen, exp, edu, skills, 0.0, "low", 0.0)
        si = build_si(normalize_profile(cand_tmp))
        calificado = rng.random() < prob_calificado(si)
        cand = Candidate(id=10_000 * (CAPAS.index(capa) + 1) + i,
                         name=f"Caso {capa}-{i + 1:03d}", gender=genero, age=edad,
                         origin=origen, exp=exp, edu=edu, skills=skills, match_score=0.0,
                         bias_risk="low",
                         true_qual=TQ_CALIFICADO if calificado else TQ_NO_CALIFICADO)
        casos.append(Caso(i, capa, cand, calificado))
    return casos


def caso_con_si(si: dict, indice: int, grupo: str = "AR", semilla: int = 0) -> Caso:
    """Caso con una Si dada (para P2b). La verdad sale de la misma regla del entorno."""
    rng = random.Random(semilla + indice)
    s = si["skills_match"]
    skills = tuple(rng.sample(SKILLS_CLAVE, s) + rng.sample(SKILLS_OTRAS, 3 - s))
    exp = {"junior": 1, "mid": 5, "senior": 10}[si["exp_band"]]
    origen = "AR" if grupo == "AR" else "SY"
    calificado = rng.random() < prob_calificado(si)
    cand = Candidate(90_000 + indice, f"Caso P2b-{indice}", "F", 30, origen, exp, si["edu"],
                     skills, 0.0, "low", TQ_CALIFICADO if calificado else TQ_NO_CALIFICADO)
    return Caso(indice, "P2b", cand, calificado)


def observar(caso: Caso, capa: str, epsilon: float, semilla: int) -> dict:
    """Región 3: la situación final la da el entorno DESPUÉS de la acción."""
    if capa in ("BIO", "TBO"):
        return {"calificado": caso.calificado}
    registro = {"true_qual": caso.candidato.true_qual, "origin_group": caso.grupo}
    decision = human_resolve([registro], mode="noisy", seed=semilla + caso.indice,
                             epsilon=epsilon)[0]
    return {"calificado": decision == "ADVANCE"}


def describir_entorno(epsilon: float) -> dict:
    """Tabla del pre-registro, calculada de las reglas (sin correr ningún agente)."""
    out = {}
    for capa in CAPAS:
        cat = CATALOGO[capa]
        celdas = list(itertools.product(cat["edu"], cat["banda"], cat["skills"]))
        filas = []
        for edu, banda, s in celdas:
            si = {"skills_match": s, "exp_band": banda, "edu": edu,
                  "seniority_ok": banda != "junior"}
            q = prob_calificado(si)
            bio = operador_bio_matcher(si)
            p_bio = q if bio == "ADVANCE" else 1 - q
            mejor = "ADVANCE" if q >= 0.5 else "REJECT"
            p_mejor = max(q, 1 - q)
            if capa == "WIO":                 # se mide contra la revisión humana con ruido ε
                p_bio = p_bio * (1 - epsilon) + (1 - p_bio) * epsilon
                p_mejor = p_mejor * (1 - epsilon) + (1 - p_mejor) * epsilon
            filas.append({"si": si, "frecuencia": 1 / len(celdas), "prob_calificado": q,
                          "accion_bio": bio, "precision_bio": round(p_bio, 4),
                          "mejor_accion": mejor, "precision_mejor": round(p_mejor, 4)})
        out[capa] = {"celdas": filas, "n_celdas": len(celdas),
                     "precision_esperada_bio": round(sum(f["precision_bio"] for f in filas)
                                                     / len(filas), 4),
                     "precision_esperada_mejor": round(sum(f["precision_mejor"] for f in filas)
                                                       / len(filas), 4)}
    return out


# ======================================================================================
# E4 · entorno de los demás roles (reglas 7 a 10 del docstring; pre-registro E4)
# ======================================================================================
NIVELES_EDU = ("Licenciatura", "Maestría", "Doctorado")

# ---- regla 7: Parser ----
CELDAS_PARSER = (
    {"formato": "json", "estructura": "plano", "etiquetas": "canonicas"},
    {"formato": "json", "estructura": "plano", "etiquetas": "sinonimos"},
    {"formato": "json", "estructura": "anidado", "etiquetas": "canonicas"},
    {"formato": "texto", "estructura": "etiquetado", "etiquetas": "canonicas"},
    {"formato": "texto", "estructura": "libre", "etiquetas": "ninguna"},
    {"formato": "html", "estructura": "etiquetado", "etiquetas": "sinonimos"},
)
FRECUENCIA_PARSER = {"AR": (0.20, 0.15, 0.20, 0.20, 0.10, 0.15),
                     "no-AR": (0.15, 0.20, 0.10, 0.15, 0.15, 0.25)}
P_DEFECTO_DOCUMENTO = 0.1
ESTRATEGIAS_PARSER = ("reglas_estrictas", "diccionario_sinonimos")
OPERADOR_BIO_PARSER = "reglas_estrictas"
RESULTADO_PARSER = (                 # resultado SIN defecto, por plantilla (índice de CELDAS_PARSER)
    {"reglas_estrictas": "completo", "diccionario_sinonimos": "completo"},
    {"reglas_estrictas": "fallido", "diccionario_sinonimos": "completo"},
    {"reglas_estrictas": "completo", "diccionario_sinonimos": "fallido"},
    {"reglas_estrictas": "completo", "diccionario_sinonimos": "parcial"},
    {"reglas_estrictas": "fallido", "diccionario_sinonimos": "completo"},
    {"reglas_estrictas": "fallido", "diccionario_sinonimos": "completo"},
)
U_PARSER = {"completo": 1.0, "parcial": 0.5, "fallido": 0.0}
ETIQUETAS_CANONICAS = {"skills", "exp", "edu", "origen", "edad", "genero", "perfil",
                       "datos_personales"}
CAMPOS_PERFIL = ("skills", "exp", "edu")

PERFIL_SHAPE_TTL = """
@prefix sh:    <http://www.w3.org/ns/shacl#> .
@prefix xsd:   <http://www.w3.org/2001/XMLSchema#> .
@prefix rdf:   <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix moacv: <https://moav-hr.diit.unlam.edu.ar/ontology/> .

moacv:PerfilShape a sh:NodeShape ;
    sh:targetClass moacv:PerfilExtraido ;
    sh:closed true ;                                   # campo fuera del shape = fuga
    sh:ignoredProperties ( rdf:type ) ;
    sh:property [ sh:path moacv:skill ; sh:datatype xsd:string ; sh:minCount 1 ] ;
    sh:property [ sh:path moacv:experiencia ; sh:datatype xsd:integer ; sh:minCount 1 ;
                  sh:maxCount 1 ; sh:minInclusive 0 ] ;
    sh:property [ sh:path moacv:educacion ; sh:minCount 1 ; sh:maxCount 1 ;
                  sh:in ( "Licenciatura" "Maestría" "Doctorado" "Especialización" ) ] .
"""


def _rng_doc(candidato: Candidate, semilla: int) -> random.Random:
    return random.Random(semilla * 100_003 + candidato.id)


def plantilla_parser(caso: Caso, semilla: int) -> tuple[int, bool]:
    """(índice de la plantilla, defecto) del documento del caso; con semilla por caso."""
    rng = _rng_doc(caso.candidato, semilla)
    frec = FRECUENCIA_PARSER[caso.grupo]
    idx = rng.choices(range(len(CELDAS_PARSER)), weights=frec)[0]
    return idx, rng.random() < P_DEFECTO_DOCUMENTO


def generar_documento(caso: Caso, semilla: int) -> tuple[Any, int, bool]:
    """Documento (CV) del caso en su plantilla: (documento, índice de plantilla, defecto)."""
    idx, defecto = plantilla_parser(caso, semilla)
    c = caso.candidato
    skills = list(c.skills)
    if idx == 0:
        doc: Any = {"skills": skills, "exp": c.exp, "edu": c.edu, "origen": c.origin,
                    "edad": c.age, "genero": c.gender}
        if defecto:
            del doc["edu"]
    elif idx == 1:
        doc = {"Habilidades": ", ".join(skills), "Experiencia": f"{c.exp} años",
               "Formación": c.edu, "Nacionalidad": c.origin, "Edad": c.age, "Sexo": c.gender}
        if defecto:
            del doc["Formación"]
    elif idx == 2:
        perfil = {"skills": skills, "exp": c.exp, "edu": c.edu}
        if defecto:
            del perfil["edu"]
        doc = {"perfil": perfil,
               "datos_personales": {"origen": c.origin, "edad": c.age, "genero": c.gender}}
    elif idx == 3:
        lineas = [f"Skills: {', '.join(skills)}", f"Exp: {c.exp}", f"Edu: {c.edu}",
                  f"Origen: {c.origin}", f"Edad: {c.age}", f"Genero: {c.gender}"]
        if defecto:
            lineas.pop(2)
        doc = "\n".join(lineas)
    elif idx == 4:
        partes = [f"Profesional de nacionalidad {c.origin} con {c.exp} años de experiencia, "
                  f"trabaja con {', '.join(skills[:-1])} y {skills[-1]}."]
        if not defecto:
            partes.append(f"{c.edu} en Sistemas.")
        doc = " ".join(partes)
    else:
        items = [f"Habilidades: {', '.join(skills)}", f"Antigüedad: {c.exp} años",
                 f"Formación: {c.edu}", f"Nacionalidad: {c.origin}"]
        if defecto:
            items.pop(2)
        doc = "<ul>" + "".join(f"<li>{x}</li>" for x in items) + "</ul>"
    return doc, idx, defecto


def _etiquetas_texto(texto: str) -> list[str]:
    return [m.strip().lower() for m in re.findall(r"^\s*([^\W\d_][^:\n]*?)\s*:", texto,
                                                   flags=re.MULTILINE)]


def _norm_etiqueta(e: str) -> str:
    return re.sub(r"[\s_]+", "_", e.strip().lower())


def percibir_documento(doc: Any) -> dict:
    """R1 del Parser: formato, estructura y etiquetas (nunca los valores del documento)."""
    if isinstance(doc, dict):
        anidado = any(isinstance(v, dict) for v in doc.values())
        claves = set(doc)
        for v in doc.values():
            if isinstance(v, dict):
                claves |= set(v)
        canon = all(_norm_etiqueta(k) in ETIQUETAS_CANONICAS for k in claves)
        return {"formato": "json", "estructura": "anidado" if anidado else "plano",
                "etiquetas": "canonicas" if canon else "sinonimos"}
    texto = str(doc)
    es_html = re.search(r"<[a-zA-Z]+[^>]*>", texto) is not None
    if es_html:
        texto = re.sub(r"<[^>]+>", "\n", texto)
    etiquetas = _etiquetas_texto(texto)
    if not etiquetas:
        return {"formato": "html" if es_html else "texto", "estructura": "libre",
                "etiquetas": "ninguna"}
    canon = all(_norm_etiqueta(e) in ETIQUETAS_CANONICAS for e in etiquetas)
    return {"formato": "html" if es_html else "texto", "estructura": "etiquetado",
            "etiquetas": "canonicas" if canon else "sinonimos"}


def _grafo_perfil(perfil: dict):
    from rdflib import BNode, Graph, Literal, RDF, XSD
    from moav_hr.core.ontology.ns import MOACV
    g = Graph()
    n = BNode()
    g.add((n, RDF.type, MOACV.PerfilExtraido))
    for clave, valor in perfil.items():
        if valor is None:
            continue
        if clave == "skills":
            for s in valor:
                g.add((n, MOACV.skill, Literal(str(s), datatype=XSD.string)))
        elif clave == "exp":
            g.add((n, MOACV.experiencia, Literal(int(valor), datatype=XSD.integer)))
        elif clave == "edu":
            g.add((n, MOACV.educacion, Literal(str(valor))))
        else:                                       # cualquier otro campo: fuera del shape
            g.add((n, MOACV[re.sub(r"\W+", "_", str(clave))], Literal(str(valor))))
    return g


_PERFIL_SHAPES = None


def validar_perfil(perfil: dict) -> dict:
    """R3 del Parser: completitud y fuga del perfil extraído, por el shape SHACL del perfil."""
    global _PERFIL_SHAPES
    from pyshacl import validate as _validate
    from rdflib import Graph, URIRef
    from rdflib.namespace import SH
    from moav_hr.core.ontology.ns import MOACV
    if _PERFIL_SHAPES is None:
        _PERFIL_SHAPES = Graph().parse(data=PERFIL_SHAPE_TTL, format="turtle")
    conforma, resultados, _ = _validate(_grafo_perfil(perfil), shacl_graph=_PERFIL_SHAPES,
                                        inference="none", abort_on_first=False)
    rutas = {resultados.value(r, SH.resultPath) for r in resultados.subjects(
        predicate=SH.resultSeverity)}
    componentes = {resultados.value(r, SH.sourceConstraintComponent)
                   for r in resultados.subjects(predicate=SH.resultSeverity)}
    por_campo = {"skills": MOACV.skill, "exp": MOACV.experiencia, "edu": MOACV.educacion}
    faltan = [c for c, p in por_campo.items() if p in rutas]
    presentes = len(CAMPOS_PERFIL) - len(faltan)
    completitud = ("completo" if presentes == len(CAMPOS_PERFIL)
                   else "parcial" if presentes > 0 else "fallido")
    fuga = URIRef(str(SH) + "ClosedConstraintComponent") in componentes
    return {"completitud": completitud, "fuga": bool(fuga), "faltan": faltan,
            "conforma": bool(conforma)}


def u_parser(sf: dict) -> float:
    return 0.0 if sf["fuga"] else U_PARSER[sf["completitud"]]


def perfil_para_matcher(perfil: dict) -> dict:
    """Regla 8: un campo faltante cuenta como skills = [], experiencia = 0, educación = «—»."""
    return {"skills": list(perfil.get("skills") or []), "exp": int(perfil.get("exp") or 0),
            "edu": perfil.get("edu") or "—"}


# ---- regla 9: Bias Auditor ----
ACCIONES_AUDITOR = ("LIBERAR", "DERIVAR")


def _banda_n(n: int) -> str:
    return "<10" if n < 10 else "10-49" if n < 50 else ">=50"


def _banda_brecha(b: float, tau_b: float) -> str:
    return "baja" if b < tau_b else "media" if b < 0.25 else "alta"


def _tasas(pares: list[tuple[str, bool]]) -> dict[str, tuple[int, int]]:
    out: dict[str, list[int]] = {}
    for g, positivo in pares:
        x = out.setdefault(str(g), [0, 0])
        x[0] += int(positivo)
        x[1] += 1
    return {g: (p, n) for g, (p, n) in sorted(out.items())}


def _brecha_y_lcb(pares: list[tuple[str, bool]], delta: float) -> tuple[float, float, int]:
    from moav_hr.core import stats
    t = _tasas(pares)
    if len(t) != 2:
        return 0.0, 0.0, 0
    (pa, na), (pb, nb) = t.values()
    return (abs(pa / na - pb / nb), stats.lcb_abs_diff_rates(pa, na, pb, nb, delta),
            min(na, nb))


def situacion_ventana(decisiones: list[tuple[str, str]], tau_b: float, delta: float) -> dict:
    """R1 del Auditor sobre las decisiones (grupo, ADVANCE/REJECT) del Matcher en la ventana."""
    brecha, lcb, n_min = _brecha_y_lcb([(g, d == "ADVANCE") for g, d in decisiones], delta)
    return {"n_por_grupo": _banda_n(n_min), "brecha": _banda_brecha(brecha, tau_b),
            "lcb_supera_tau_b": bool(lcb > tau_b)}


def medida_ventana(decisiones: list[tuple[str, str]], delta: float) -> dict:
    """Valores (no bandas) de la ventana, para la traza."""
    brecha, lcb, n_min = _brecha_y_lcb([(g, d == "ADVANCE") for g, d in decisiones], delta)
    return {"brecha_dp": round(brecha, 4), "lcb": round(lcb, 4), "n_min_por_grupo": n_min}


def regla_certificada(si: dict) -> str:
    """Operador BIO del Auditor = la regla certificada (DE-6): no aprende."""
    return "DERIVAR" if si["lcb_supera_tau_b"] else "LIBERAR"


def revisar_ventana(casos: list[Caso], decisiones: list[str], capa: str, epsilon: float,
                    semilla: int, tau_b: float, delta: float) -> dict:
    """R3 del Auditor: revisión de la ventana; el sesgo se confirma con el mismo estándar
    de evidencia (LCB de la brecha de tasas de error del Matcher > τ_b)."""
    pares = []
    for caso, d in zip(casos, decisiones):
        calificado = observar(caso, capa, epsilon, semilla)["calificado"]
        pares.append((caso.grupo, (d == "ADVANCE") != calificado))      # error del Matcher
    brecha, lcb, _ = _brecha_y_lcb(pares, delta)
    return {"sesgo_confirmado": bool(lcb > tau_b),
            "brecha_errores": _banda_brecha(brecha, tau_b)}


def u_auditor(accion: str, sf: dict) -> float:
    return 1.0 if (accion == "DERIVAR") == bool(sf["sesgo_confirmado"]) else 0.0


def lcb_maxima_ventana(n_por_grupo: int, delta: float) -> float:
    """La LCB más alta posible con n por grupo (brecha observada 1)."""
    from moav_hr.core import stats
    return stats.lcb_abs_diff_rates(n_por_grupo, n_por_grupo, 0, n_por_grupo, delta)


# ---- regla 10: Explainer ----
ESTRATEGIAS_EXPLAINER = ("por_factores", "contrafactica", "regulatoria")
OPERADOR_BIO_EXPLAINER = "por_factores"
TIPOS_DECISION = {"ADVANCE": "avanza", "REJECT": "rechaza", "ESCALATE_HUMAN": "deriva"}
DESTINATARIOS = ("regulador", "usuario")
ELEMENTOS_POR_ESTRATEGIA = {          # lo que produce cada estrategia (estrategias_llc.py)
    "por_factores": {"resultado", "motivo_principal", "factores_todos", "lenguaje_llano"},
    "contrafactica": {"resultado", "motivo_principal", "lenguaje_llano", "accion_sugerida",
                      "revision_humana"},
    "regulatoria": {"resultado", "motivo_principal", "factores_todos", "dictamen_omega",
                    "secuencia_trazable", "revision_humana"},
}


def destinatario(caso: Caso, semilla: int) -> str:
    return "regulador" if random.Random(semilla * 100_019 + caso.candidato.id).random() < 0.5 \
        else "usuario"


def requisitos_explicacion(si: dict) -> set[str]:
    """Elementos que exige cada destinatario (regla 10)."""
    if si["destinatario"] == "usuario":
        req = {"resultado", "motivo_principal", "lenguaje_llano"}
        if si["tipo"] == "rechaza":
            req.add("accion_sugerida")
    else:
        req = {"resultado", "motivo_principal", "dictamen_omega", "secuencia_trazable"}
        if si["motivos"] == "varios":
            req.add("factores_todos")
    if si["tipo"] == "deriva":
        req.add("revision_humana")
    return req


def grafo_hechos_caso(hechos: dict):
    """Grafo RDF del caso con los hechos que la explicación tiene que respetar."""
    from rdflib import Graph, Literal, URIRef
    from moav_hr.core.ontology.ns import MOACV, PROV
    from rdflib.namespace import RDF
    g = Graph()
    d = URIRef(str(MOACV) + f"Decision/{hechos['trace_id']}")
    g.add((d, RDF.type, MOACV.Decision))
    g.add((d, MOACV.resultado, Literal(hechos["resultado"])))
    g.add((d, MOACV.traceId, Literal(hechos["trace_id"])))
    si = hechos["si_matcher"]
    g.add((d, MOACV.skillsClave, Literal(int(si["skills_match"]))))
    g.add((d, MOACV.bandaExperiencia, Literal(si["exp_band"])))
    g.add((d, MOACV.educacion, Literal(si["edu"])))
    dic = hechos["dictamen"]
    v = URIRef(str(MOACV) + f"Ventana/{hechos['ventana']}")
    g.add((d, PROV.wasInformedBy, v))
    g.add((v, MOACV.lcb, Literal(float(dic["lcb"]))))
    g.add((v, MOACV.tauB, Literal(float(dic["tau_b"]))))
    g.add((v, MOACV.intervencion, Literal(dic["accion"])))
    return g


_Q_HECHOS = """
PREFIX moacv: <https://moav-hr.diit.unlam.edu.ar/ontology/>
PREFIX prov: <http://www.w3.org/ns/prov#>
SELECT ?resultado ?traza ?skills ?banda ?edu ?lcb ?tau WHERE {
  ?d a moacv:Decision ; moacv:resultado ?resultado ; moacv:traceId ?traza ;
     moacv:skillsClave ?skills ; moacv:bandaExperiencia ?banda ; moacv:educacion ?edu ;
     prov:wasInformedBy ?v .
  ?v moacv:lcb ?lcb ; moacv:tauB ?tau .
}"""


def texto_numero(x: float) -> str:
    return f"{float(x):.3f}".replace(".", ",")


def verificar_explicacion(elementos: dict, si: dict, grafo) -> dict:
    """R3 del Explainer: completitud verificada contra el grafo RDF del caso (SPARQL)."""
    fila = list(grafo.query(_Q_HECHOS))[0]
    hechos = {
        "resultado": [str(fila.resultado)],
        "motivo_principal": [f"skills clave = {int(fila.skills)}"],
        "factores_todos": [f"skills clave = {int(fila.skills)}",
                           f"banda de experiencia = {fila.banda}", f"educación = {fila.edu}"],
        "dictamen_omega": [f"LCB = {texto_numero(float(fila.lcb))}",
                           f"τ_b = {texto_numero(float(fila.tau))}"],
        "secuencia_trazable": [str(fila.traza)],
    }
    req = requisitos_explicacion(si)
    faltan = sorted(req - set(elementos))
    inconsistentes = sorted(e for e in req & set(elementos)
                            if any(h not in elementos[e] for h in hechos.get(e, [])))
    return {"completa": not faltan and not inconsistentes, "faltan": faltan,
            "inconsistentes": inconsistentes}


def describir_entorno_e4(tau_b: float, delta: float, ventana: int) -> dict:
    """Tasas esperadas por (celda de Si, estrategia), calculadas de las reglas 7, 9 y 10
    sin correr ningún agente."""
    parser = []
    for i, celda in enumerate(CELDAS_PARSER):
        fila = {"celda": celda, "frecuencia": {g: FRECUENCIA_PARSER[g][i]
                                               for g in FRECUENCIA_PARSER}, "estrategias": {}}
        for e in ESTRATEGIAS_PARSER:
            r = RESULTADO_PARSER[i][e]
            p_c = (1 - P_DEFECTO_DOCUMENTO) if r == "completo" else 0.0
            p_p = P_DEFECTO_DOCUMENTO if r == "completo" else (1.0 if r == "parcial" else 0.0)
            fila["estrategias"][e] = {"sin_defecto": r, "p_completo": round(p_c, 4),
                                      "p_parcial": round(p_p, 4),
                                      "p_fallido": round(1 - p_c - p_p, 4),
                                      "u_esperada": round(p_c + 0.5 * p_p, 4)}
        parser.append(fila)
    por_grupo = {}
    for g, frec in FRECUENCIA_PARSER.items():
        bio = sum(f * parser[i]["estrategias"][OPERADOR_BIO_PARSER]["p_completo"]
                  for i, f in enumerate(frec))
        mejor = sum(f * max(x["p_completo"] for x in parser[i]["estrategias"].values())
                    for i, f in enumerate(frec))
        por_grupo[g] = {"p_completo_operador_bio": round(bio, 4),
                        "p_completo_mejor_estrategia": round(mejor, 4)}
    dtv = 0.5 * sum(abs(a - b) for a, b in zip(FRECUENCIA_PARSER["AR"],
                                               FRECUENCIA_PARSER["no-AR"]))
    explainer = []
    for tipo in ("avanza", "rechaza", "deriva"):
        for dest in DESTINATARIOS:
            for motivos in ("uno", "varios"):
                si = {"tipo": tipo, "destinatario": dest, "motivos": motivos}
                req = requisitos_explicacion(si)
                explainer.append({"si": si, "requisitos": sorted(req), "completa": {
                    e: req <= ELEMENTOS_POR_ESTRATEGIA[e] for e in ESTRATEGIAS_EXPLAINER}})
    n_g = ventana // 2
    return {"parser": {"celdas": parser, "por_grupo": por_grupo,
                       "dtv_formato_grupo": round(dtv, 4),
                       "operador_bio": OPERADOR_BIO_PARSER,
                       "p_defecto": P_DEFECTO_DOCUMENTO},
            "explainer": {"celdas": explainer, "operador_bio": OPERADOR_BIO_EXPLAINER},
            "auditor": {"ventana": ventana, "n_por_grupo": n_g,
                        "lcb_maxima": round(lcb_maxima_ventana(n_g, delta), 4),
                        "tau_b": tau_b, "puede_derivar": lcb_maxima_ventana(n_g, delta) > tau_b}}
