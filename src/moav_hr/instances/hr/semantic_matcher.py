"""
Semantic Matcher (capa TBO, región 2) — instancia HR.

Integración teorías↔LLM (v13 §2.2, P2.1): recupera por similitud las teorías relevantes
a Si, las inyecta como few-shot y condiciona la decisión. EL PUNTO EXACTO donde la teoría
entra en la decisión está marcado abajo (★). En modo sim, la teoría top ajusta el score
base (dependencia causal medible por el harness de fidelidad); en modo llm, va como few-shot.
"""
from __future__ import annotations
import re

from moav_hr.core.agent import MOACVAgent, TBOLayer
from moav_hr.core.llm import LLMBackend
from moav_hr.core.theory import Theory, serialize
from moav_hr.instances.hr.scoring import sim_match_score
from moav_hr.instances.hr.synthetic import Candidate, JOB

THEORY_NUDGE = 0.03   # peso del ajuste por teoría sobre el score base (modo sim)


class SemanticMatcherAgent(MOACVAgent):
    def __init__(self, backend: LLMBackend):
        super().__init__("SemanticMatcher", "matcher", tbo=TBOLayer(training_runs=4))  # → Trained
        self.backend = backend

    def _score_sim(self, candidate: Candidate, retrieved: list[Theory]) -> tuple[float, str]:
        base = sim_match_score(candidate)
        if not retrieved:
            return base, "sim"
        top = retrieved[0]                                    # ★ teoría seleccionada (Def. 4)
        direction = 1.0 if top.a == "ADVANCE" else -1.0
        score = base + THEORY_NUDGE * top.reliability * direction   # ★ teoría → decisión
        return round(max(0.0, min(0.99, score)), 3), "sim+theory"

    def _score_llm(self, candidate: Candidate, profile: dict, few_shot: str) -> tuple[float, str]:
        prompt = (
            "Sos un evaluador técnico de RR.HH. Calificá el ajuste del perfil al puesto "
            f"«{JOB['title']}» (skills clave: {', '.join(JOB['key_skills'])}; exp. mínima "
            f"{JOB['min_exp']} años).\nIgnorá nombre, género, edad y origen.\n"
            + (few_shot + "\n" if few_shot else "")                # ★ teorías como few-shot
            + f"Perfil: skills={profile['skills']}, experiencia={profile['exp']} años, "
            f"educación={profile['edu']}.\nRespondé SOLO un número entre 0 y 1."
        )
        txt = self.backend.complete(prompt)
        m = re.search(r"\d?\.\d+|\b[01]\b", txt)
        if m:
            return round(max(0.0, min(1.0, float(m.group()))), 3), "llm"
        return sim_match_score(candidate), "sim(fallback)"

    def run(self, state: dict) -> dict:
        c = state["candidate"]
        si = state["parser"]["si"]
        retrieved = self.retrieve(si)                          # RAG (§2.2)
        if self.backend.mode == "llm":
            score, source = self._score_llm(c, state["parser"]["profile"],
                                            self.retriever.few_shot(retrieved))
        else:
            score, source = self._score_sim(c, retrieved)
        state["matcher"] = {
            "score": score, "source": source,
            "n_retrieved": len(retrieved),
            "retrieved": [f"{serialize(t.si)}→{t.a}(U={t.u:.2f})" for t in retrieved],
            "si": si,
        }
        state["trail"].record("SemanticMatcher", "TBO", "semantic_matching", region=2,
                              score=score, source=source, n_theories=len(retrieved))
        return state
