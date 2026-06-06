import sys
sys.path.insert(0, "../src")
from moav_hr.lifecycle.theory import Theory, TheoryBase, collaborate
from moav_hr.agents.base_agent import MOACVAgent, TBOLayer, WIOLayer

# Test 1: selección por ranking U > P > K
tb = TheoryBase()
tb.add(Theory(si={"x":1}, a="advance", sf={"r":"ok"}, p=5, k=10, u=0.8))
tb.add(Theory(si={"x":1}, a="reject",  sf={"r":"no"}, p=8, k=10, u=0.8))  # mismo U, mayor P
best = tb.select({"x":1})
assert best.a == "reject", f"esperaba reject, dio {best.a}"
print("Test 1 OK: selección por ranking (U empate -> mayor P)")

# Test 2: transferencia maestro -> aprendiz
maestro = MOACVAgent("Auditor-1", "bias_auditor",
                     tbo=TBOLayer(training_runs=5),
                     wio=WIOLayer(production_feedback=[{"x":1}]))
novato = MOACVAgent("Auditor-2", "bias_auditor")
maestro.learn(si={"perfil":"A"}, a="flag", sf={"bias":"high"}, success=True, accuracy=0.9, fairness=0.8)
print(f"maestro madurez: {maestro.maturity.value}, novato madurez: {novato.maturity.value}")
print(f"teorías maestro: {len(maestro.theories)}, novato antes: {len(novato.theories)}")
maestro.transfer_to(novato)
print(f"novato después de transferencia: {len(novato.theories)}")
assert len(novato.theories) == 1
print("Test 2 OK: transferencia maestro -> aprendiz")

print("\nTodos los tests pasaron.")
