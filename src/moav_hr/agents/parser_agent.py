"""Parser Agent (capa BIO) — extrae y normaliza el perfil, no retiene atributos sensibles."""
from __future__ import annotations

from moav_hr.agents.base_agent import MOACVAgent, BIOLayer, TBOLayer, WIOLayer
from moav_hr.synthetic import JOB


class ParserAgent(MOACVAgent):
    def __init__(self):
        super().__init__(
            "ParserAgent", "parser",
            bio=BIOLayer(
                system_prompt="Extraé y normalizá el perfil. No retengas atributos sensibles.",
                guardrails=[{"attribute": "gender", "forbid_use": True},
                            {"attribute": "origin", "forbid_use": True},
                            {"attribute": "age", "forbid_use": True}],
                regulatory_constraints=["EU_AI_ACT_ART10", "LEY_25326_ART20"],
            ),
            tbo=TBOLayer(training_runs=5),
            wio=WIOLayer(production_feedback=[{"bootstrap": True}]),  # → Mature
        )

    def run(self, state: dict) -> dict:
        c = state["candidate"]
        matched = [s for s in c.skills if s in JOB["key_skills"]]
        sensitive = []
        if c.origin != "AR":
            sensitive.append(f"origin={c.origin}")
        if c.age > 40:
            sensitive.append(f"age={c.age}")
        if c.gender == "F":
            sensitive.append("gender=F")
        # guardrail BIO: los atributos sensibles se detectan pero NO se retienen
        state["parser"] = {"skills_matched": matched, "sensitive": sensitive, "retained": []}
        state["trail"].record("ParserAgent", "BIO", "cv_normalization",
                              skills_matched=matched, sensitive=sensitive, retained=[])
        return state
