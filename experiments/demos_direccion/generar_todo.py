#!/usr/bin/env python
"""
Bloque D · D7 — corre los demos D1 a D5 y escribe docs/demos_direccion/NUMEROS_PARA_PLACAS.md.

Todos los números del markdown salen de las salidas de los demos (ninguno escrito a mano).
Para cada demo: de 3 a 6 números clave, la figura, una leyenda de una línea y los rótulos.

Uso:  python experiments/demos_direccion/generar_todo.py [--out DIR] [--backend auto|token-cosine]
"""
from __future__ import annotations
import argparse

import d1_embeddings
import d2_ciclo_teoria
import d3_transferencia
import d4_maduracion
import d5_diversidad
from comun import ROTULO_SEM, ROTULO_SIM, num, out_dir, si_corta

NOMBRE_ESTADO = {"born": "Born", "novato": "Novice", "trained": "Trained", "mature": "Mature"}


def _rotulos(extra: "str | None" = None) -> list[str]:
    out = [f"- Rótulo: *{ROTULO_SIM}*.", f"- Rótulo: *{ROTULO_SEM}*."]
    if extra:
        out.append(f"- Rótulo obligatorio: *{extra}*.")
    return out


def _figuras(nombres: list[str]) -> str:
    return " · ".join(f"`docs/demos_direccion/{n}`" for n in nombres)


def seccion_d1(s: dict) -> tuple[list[str], list[str]]:
    tok, emb, dl = s["token_cosine"], s["embeddings"], s["delta"]
    n = s["base"]["n_teorias"]
    L = ["## D1 · Selección de teoría por embeddings (P3)", "",
         f"- δ que rige en el Matcher: **{num(dl['rige'], 1)}** (el default de "
         f"`TheoryRetriever` es {num(dl['default_TheoryRetriever'], 1)}, pero el Matcher "
         f"hereda {num(dl['default_MOACVAgent'], 1)} de `MOACVAgent`).",
         f"- Teorías que superan δ con la Si de Fátima: token-cosine **{len(tok['superan_delta'])} de {n}**"
         + (f"; embeddings **{len(emb['superan_delta'])} de {n}** (coseno entre "
            f"{num(emb['similitud_min'], 3)} y {num(emb['similitud_max'], 3)})."
            if emb["disponible"] else "; embeddings no disponibles en esta corrida."),
         f"- Seleccionada: token-cosine **T{tok['seleccionada']}**"
         + (f", embeddings **T{emb['seleccionada']}** → misma teoría: "
            f"**{'sí' if s['comparacion']['misma_seleccionada'] else 'no'}**; top-{s['top_k']} "
            f"recuperadas iguales: **{'sí' if s['comparacion']['mismas_recuperadas'] else 'no'}** "
            f"({tok['recuperadas_top_k']} vs {emb['recuperadas_top_k']})."
            if emb["disponible"] else "."),
         ]
    propia = s["consulta"]["teoria_con_la_misma_si"]
    nota = []
    if emb["disponible"]:
        pp = s["comparacion"]["puesto_de_la_teoria_con_la_misma_si"]
        L.append(f"- La teoría con la misma Si que la consulta (T{propia}, coseno 1) queda en el "
                 f"puesto **{pp['token_cosine']}** (token-cosine) y **{pp['embeddings']}** "
                 "(embeddings) del orden de `retrieve`.")
        L.append(f"- Modelo: `{emb['modelo']}` ({emb['dimension']} dimensiones); PCA 2D explica "
                 f"{num(sum(emb['pca_varianza_explicada']) * 100, 1)} % de la varianza.")
        if len(emb["superan_delta"]) == n:
            nota.append(f"D1: con embeddings sobre la Si serializada en JSON **todas** las teorías "
                        f"superan δ = {num(dl['rige'], 1)} (coseno ≥ {num(emb['similitud_min'], 3)}); "
                        "el umbral no discrimina y el top-k lo decide la clave (U, P, K, recencia, "
                        "id): entran teorías poco parecidas "
                        f"({emb['recuperadas_top_k']}).")
        if s["comparacion"]["puesto_de_la_teoria_con_la_misma_si"]["embeddings"] != 1:
            nota.append(f"D1: la teoría con la misma Si que la consulta (T{propia}) no es la "
                        "seleccionada en ningún backend: la similitud solo filtra, no ordena.")
    else:
        nota.append(f"D1: embeddings no disponibles: {emb['error']}.")
    L += [f"- Figura: {_figuras(s['figuras'])}.",
          "- Leyenda: *la similitud (coseno) solo decide qué teorías pasan δ; entre las que "
          "pasan, la seleccionada sale de la clave (U, P, K, recencia, id).* PCA es una "
          "proyección: la selección usa el coseno en la dimensión completa.",
          *_rotulos(), ""]
    return L, nota


def seccion_d2(s: dict) -> tuple[list[str], list[str]]:
    seg, nuevas = s["teoria_seguida"], s["teorias_nuevas_por_tarea"]
    nac, fin = seg["nacimiento"], seg["usos"][-1]
    t1, t2 = s["tarea_1"], s["tarea_2"]
    puestos = sorted({f"{u['puesto']}/{u['n_celda']}" for u in seg["usos"]})
    L = ["## D2 · Creación e iteración de una teoría en dos tareas (P1)", "",
         f"- Teorías nuevas por tarea (región 7): tarea 1 = **{nuevas[0]}**, tarea 2 = "
         f"**{nuevas[1]}** ({'decrece' if s['teorias_nuevas_decrecen'] else 'no decrece'}).",
         f"- Teoría seguida: **T{seg['id']}** ({seg['a']}; Si: {si_corta(seg['si'])}), "
         f"{seg['regla_de_eleccion']}.",
         f"- Nace en la tarea {nac['tarea']}, caso de {nac['nombre']}: P = {nac['p']}, "
         f"K = {nac['k']}, U = {num(nac['u'], 3)}. Tras {len(seg['usos'])} usos: P = {fin['p']}, "
         f"K = {fin['k']}, U = **{num(fin['u'], 3)}**; puesto en su celda: {', '.join(puestos)}.",
         f"- Fue la seleccionada (★) para decidir **{len(seg['seleccionada_para_decidir'])}** casos.",
         f"- Aciertos del Matcher: tarea 1 = {t1['aciertos_del_matcher']}/{t1['n_casos']}, "
         f"tarea 2 = {t2['aciertos_del_matcher']}/{t2['n_casos']}; casos que refuerzan una "
         f"teoría existente: {t1['casos_que_refuerzan_una_teoria_existente']} y "
         f"{t2['casos_que_refuerzan_una_teoria_existente']}.",
         f"- Figura: {_figuras(s['figuras'])}.",
         "- Leyenda: *la teoría nace en la región 5 con el primer caso y cada caso equivalente "
         "la refuerza (P, K, U); "
         + (f"en la segunda tarea nacen menos teorías nuevas ({nuevas[1]} vs {nuevas[0]}).*"
            if s["teorias_nuevas_decrecen"] else
            f"en la segunda tarea no nacen menos teorías nuevas ({nuevas[1]} vs {nuevas[0]}).*"),
         *_rotulos(), ""]
    nota = []
    if not s["teorias_nuevas_decrecen"]:
        nota.append("D2: las teorías nuevas NO decrecen de la tarea 1 a la 2.")
    if puestos == ["1/1"]:
        nota.append(f"D2: la celda de Si de T{seg['id']} tiene una sola teoría en todo el "
                    "recorrido, así que su puesto es siempre 1 de 1 (no hay competencia que mostrar).")
    cambios = [c for c in s["casos"] if c["la_teoria_cambio_la_accion"]]
    peor = [c for c in cambios if not c["acierto"]]
    mejor = [c for c in cambios if c["acierto"]]
    if cambios:
        nota.append(f"D2: la teoría seleccionada cambió la acción del Matcher (contrafáctico: "
                    f"score sin teoría) en {len(cambios)} caso(s): "
                    + ", ".join(f"caso {c['candidato_id']} (tarea {c['tarea']}, T{c['seleccionada']['id']} "
                                f"{c['seleccionada']['a']}: {c['accion_sin_teoria']} → {c['accion']}, "
                                f"{'acierto' if c['acierto'] else 'error'})" for c in cambios)
                    + f". Corrige {len(mejor)}, empeora {len(peor)}.")
    errores_sin_cambio = [c for c in s["casos"] if not c["acierto"] and not c["la_teoria_cambio_la_accion"]]
    if errores_sin_cambio:
        nota.append("D2: errores del Matcher que no dependen de la teoría (el score base ya "
                    "estaba del otro lado del umbral): "
                    + ", ".join(f"caso {c['candidato_id']} (tarea {c['tarea']})" for c in errores_sin_cambio) + ".")
    return L, nota


def seccion_d3(s: dict) -> tuple[list[str], list[str]]:
    p, c1, c2, cnt = (s["principal"], s["contraejemplo_r_bajo"],
                      s["contraejemplo_sin_historia"], s["conteo_por_categoria"])
    L = ["## D3 · Transferencia maestro → aprendiz del mismo rol (P2)", "",
         f"- Donante A (Matcher de la PoC, {NOMBRE_ESTADO[s['donante_A']['estado']]}): "
         f"r = **{num(s['donante_A']['reputacion'], 3)}** ≥ τ = {num(s['tau'], 1)} con "
         f"{len(s['donante_A']['fair_w'])} ventanas → transferencia "
         f"**{'aceptada' if p['aceptada'] else 'rechazada'}**.",
         f"- Teorías de A en B: igual **{cnt['igual']}** · similar **{cnt['similar']}** · "
         f"nueva **{cnt['nueva']}**; base de B: {p['base_receptor_antes']} → "
         f"**{p['base_receptor_despues']}** teorías.",
         f"- Contraejemplo r < τ: donante C con r = **{num(c1['reputacion_donante'], 3)}** "
         f"({c1['ventanas_donante']} ventanas) → **{'aceptada' if c1['aceptada'] else 'rechazada'}**.",
         f"- Contraejemplo sin historia: A∅ con {c2['ventanas_donante']} ventanas → "
         f"can_donate = {c2['can_donate']} → **{'aceptada' if c2['aceptada'] else 'rechazada'}** "
         f"(hacen falta {c2['ventanas_minimas_para_donar']}); `approve_sharing` sola daría "
         f"{c2['aprobacion_omega']} por el prior r0.",
         f"- Estado de B: {NOMBRE_ESTADO[s['receptor_B']['estado_antes']]} → "
         f"{NOMBRE_ESTADO[s['receptor_B']['estado_despues']]} "
         f"({'cambia' if s['cambia_el_estado_de_B'] else 'la transferencia no cambia el estado'}).",
         f"- Figura: {_figuras(s['figuras'])}.",
         "- Leyenda: *Ω habilita la transferencia solo si el donante tiene historia (≥ m0 "
         "ventanas) y reputación r ≥ τ; las teorías entran por las reglas del Alg. 4.10.*",
         *_rotulos(), ""]
    nota = []
    if cnt["similar"] == 0:
        nota.append(f"D3: no hay teorías **similares** (0): {s['nota_similares']}. La regla "
                    "existe en `sharing._merge` pero estos lotes no la ejercitan.")
    if not s["cambia_el_estado_de_B"]:
        nota.append("D3: la transferencia no cambia el estado de madurez de B (sigue en "
                    f"{NOMBRE_ESTADO[s['receptor_B']['estado_despues']]}): el estado se deriva "
                    "de TBO/WIO, no del tamaño de la base.")
    return L, nota


def seccion_d4(s: dict) -> tuple[list[str], list[str]]:
    pu, ce, t2 = s["puntual"], s["certificado"], s["tarea_2_reutiliza_teorias"]
    trans = " · ".join(f"W{t['ventana']}: {NOMBRE_ESTADO[t['de']]} → {NOMBRE_ESTADO[t['a']]}"
                       for t in pu["transiciones"]) or "ninguna transición"
    w_mat = pu["ventana_en_que_llega_a_mature"]
    tarea_mature = next((v["tarea"] for v in pu["linea_de_tiempo"] if v["ventana"] == w_mat),
                        None)
    L = ["## D4 · Maduración sobre el caso y segunda tarea (P4)", "",
         f"- Gate puntual (τ = {num(s['gate']['tau'], 1)}): {trans}.",
         f"- Gate certificado: queda en **{NOMBRE_ESTADO[ce['estado_final']]}** tras "
         f"{len(ce['linea_de_tiempo'])} ventanas; aun con ventanas perfectas necesita "
         f"**m_min(1,0) = {s['m_min_ventanas_perfectas']}** (δ = {num(s['gate']['delta'], 2)}). "
         "Es la propiedad del certificado, no un defecto.",
         f"- Media de fair(W) en las {len(ce['linea_de_tiempo'])} ventanas: "
         f"{num(s['media_de_todas_las_ventanas'], 3)}.",
         f"- Tarea 2: **{t2['casos_cuya_teoria_seleccionada_tenia_aciertos']}/{t2['casos']}** "
         f"casos recuperan una teoría con aciertos (tarea 1: "
         f"{s['tarea_1']['casos_cuya_teoria_seleccionada_tenia_aciertos']}/{s['tarea_1']['casos']}); "
         f"aciertos {t2['aciertos_del_matcher_total']}/{t2['casos']}; teorías nuevas "
         f"**{t2['teorias_nuevas']}** (tarea 1: {s['tarea_1']['teorias_nuevas']}).",
         f"- Eventos de la región 7 en el trail: puntual {pu['eventos_region_7']}, certificado "
         f"{ce['eventos_region_7']}.",
         f"- Figura: {_figuras(s['figuras'])}.",
         "- Leyenda: *" + (
             f"con el gate puntual el Matcher llega a Mature en la tarea {tarea_mature} "
             if tarea_mature is not None else "con el gate puntual el Matcher no llega a Mature ")
         + "y en la tarea 2 reutiliza sus teorías; el certificado exige una historia mucho más "
         f"larga (m_min(1,0) = {s['m_min_ventanas_perfectas']} ventanas).*",
         *_rotulos(), ""]
    nota = []
    if s["ventanas_en_mature_con_r_bajo_tau"]:
        nota.append("D4: en " + ", ".join(f"W{w}" for w in s["ventanas_en_mature_con_r_bajo_tau"])
                    + " la reputación puntual cae por debajo de τ y el agente sigue en Mature: "
                    "`advance` solo avanza (el ciclo del código es monótono, no hay regresión).")
    if not s["el_estado_cambia_las_decisiones_del_matcher"]:
        nota.append("D4: el estado de madurez no cambia las decisiones del Matcher en modo sim "
                    "(mismas acciones con el gate puntual y con el certificado).")
    nota.append("D4: las ventanas son de 4 casos; fair(W) toma valores extremos "
                f"(p. ej. {num(pu['linea_de_tiempo'][-1]['fair_w'], 2)} en "
                f"W{pu['linea_de_tiempo'][-1]['ventana']}).")
    return L, nota


def seccion_d5(s: dict) -> tuple[list[str], list[str]]:
    c = s["comites"]
    et = {"homogeneo": "(a) homogéneo", "diverso": "(b) diverso",
          "diverso_con_piso": "(c) diverso con piso"}
    L = ["## D5 · Diversidad en comité con sesgos programados (I5)", "",
         "- D(M) = (1 − ρ̄)/2: " + " · ".join(f"{et[k]} **{num(v['D'], 3)}**" for k, v in c.items())
         + f"; d_max(3) = {num(c['homogeneo']['d_max'], 2)}.",
         "- |Δ_DP| del comité vs. media de los miembros: "
         + " · ".join(f"{et[k]} {num(v['disparidad_comite'], 3)} vs "
                      f"{num(v['media_disparidad_miembros'], 3)} "
                      f"(**{num(v['relacion_comite_sobre_media_miembros'], 2)}**)"
                      for k, v in c.items()) + ".",
         "- |Δ_DP| de cada miembro: " + " · ".join(
             f"{et[k]} [{', '.join(num(x, 3) for x in v['disparidad_miembros'])}]"
             for k, v in c.items()) + ".",
         f"- Δ_DP de la calificación real en la muestra: {num(s['disparidad_de_la_calificacion_real'], 3)} "
         f"({2 * s['parametros_programados']['candidatos_por_grupo']} candidatos).",
         f"- Figura: {_figuras(s['figuras'])}.",
         "- Leyenda: *" + (
             "con sesgos de grupo en direcciones distintas el promedio del comité cancela parte "
             f"del sesgo de sus miembros (comité/media = "
             f"{num(c['diverso']['relacion_comite_sobre_media_miembros'], 2)})"
             if c["diverso"]["relacion_comite_sobre_media_miembros"] < 1 else
             "con sesgos de grupo en direcciones distintas el comité NO reduce el sesgo medio "
             f"de sus miembros (comité/media = "
             f"{num(c['diverso']['relacion_comite_sobre_media_miembros'], 2)})")
         + (f"; con un piso común, el comité queda en {num(c['diverso_con_piso']['disparidad_comite'], 3)}"
            f" frente a {num(c['diverso']['disparidad_comite'], 3)} sin piso.*"),
         *_rotulos(s["rotulo_obligatorio"]), ""]
    nota = []
    for k, v in c.items():
        if v["relacion_comite_sobre_media_miembros"] and v["relacion_comite_sobre_media_miembros"] > 1:
            nota.append(f"D5: en {et[k]} la disparidad del comité ({num(v['disparidad_comite'], 3)}) "
                        f"supera la media de sus miembros ({num(v['media_disparidad_miembros'], 3)}): "
                        "el piso común no se cancela y el miembro menos sesgado queda en "
                        f"{num(min(v['disparidad_miembros']), 3)}, lo que baja la media; frente al "
                        f"peor miembro la relación es {num(v['relacion_comite_sobre_max_miembro'], 2)}.")
    if s["disparidad_de_la_calificacion_real"] > 0:
        nota.append(f"D5: la calificación real ya tiene Δ_DP = "
                    f"{num(s['disparidad_de_la_calificacion_real'], 3)} en la muestra (misma "
                    "distribución por grupo, pero muestra finita): es la referencia de la figura.")
    return L, nota


def correr(out=None, backend: str = "auto") -> str:
    destino = out_dir(out)
    salidas = {"D1": d1_embeddings.correr(destino, backend), "D2": d2_ciclo_teoria.correr(destino),
               "D3": d3_transferencia.correr(destino), "D4": d4_maduracion.correr(destino),
               "D5": d5_diversidad.correr(destino)}
    cuerpo, notas = [], []
    for fn, clave in ((seccion_d1, "D1"), (seccion_d2, "D2"), (seccion_d3, "D3"),
                      (seccion_d4, "D4"), (seccion_d5, "D5")):
        L, n = fn(salidas[clave])
        cuerpo += L
        notas += n
    md = ["# Números para las placas — Bloque D (demos para la dirección)", "",
          "Generado por `experiments/demos_direccion/generar_todo.py`: **ningún número está "
          "escrito a mano**; todo sale de correr los demos (JSON y figuras en "
          "`docs/demos_direccion/`). Decimales con coma, como en las figuras; los JSON usan "
          "punto.", "",
          f"Todas las salidas llevan dos rótulos: *{ROTULO_SIM}* y *{ROTULO_SEM}*.", "",
          "Regenerar:", "", "```bash",
          "python experiments/demos_direccion/generar_todo.py", "```", ""]
    md += cuerpo
    md += ["## Resultados que no fueron los esperados (se reportan tal cual)", ""]
    md += [f"- {n}" for n in notas] + [""]
    texto = "\n".join(md)
    (destino / "NUMEROS_PARA_PLACAS.md").write_text(texto, encoding="utf-8")
    return texto


def main() -> None:
    ap = argparse.ArgumentParser(description="Bloque D · corre D1–D5 y escribe los números")
    ap.add_argument("--out", default=None, help="carpeta de salida (default docs/demos_direccion)")
    ap.add_argument("--backend", choices=["auto", "token-cosine"], default="auto",
                    help="backend de similitud para D1 (ver d1_embeddings.py)")
    args = ap.parse_args()
    correr(args.out, args.backend)
    print(f"NUMEROS_PARA_PLACAS.md escrito en {out_dir(args.out)}")


if __name__ == "__main__":
    main()
