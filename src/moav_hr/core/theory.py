"""
Teorías de aprendizaje ⟨Si, A, Sf, P, K, U⟩ y su base de conocimiento.

v13 Def. 3 (teoría + equivalencia por CUANTIZACIÓN — A1), Def. 4 (selección por ranking
con desempate determinista — A5+A10).

Equivalencia por cuantización (A1): la identidad de teorías se define por una función de
cuantización Q que mapea situaciones a claves hashables; Si ≅ Si′ ⟺ Q(Si) == Q(Si′).
Al ser igualdad de claves, la equivalencia es REFLEXIVA, SIMÉTRICA y TRANSITIVA — a
diferencia del esquema anterior sim(a,b) ≥ δ, que no era transitivo y hacía la fusión de
bases dependiente del orden de comparación.

SEPARACIÓN equivalencia ↔ recuperación: Q se usa SOLO para identidad/fusión de teorías
(Defs. 3/7/8). La recuperación top-k (RAG, §2.2) sigue usando similitud continua por
ranking en core/retrieval.py — no necesita transitividad porque no define identidad.

Default: q_canonical (identidad sobre la serialización JSON canónica) — recupera el caso
simbólico exacto del LLC original. q_grid (rejilla sobre embeddings) queda implementada
para el Eje 1, sin uso por defecto.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Callable, Hashable, Optional
import json

# función de cuantización: situación → clave hashable (identidad de celda)
QuantizationFn = Callable[[dict], Hashable]

# (compat) similitud continua sobre situaciones: (a, b) -> [0,1] — vive en retrieval
SimFn = Callable[[dict, dict], float]


def serialize(situation: dict[str, Any]) -> str:
    """Serializa una situación como JSON canónico (región 1, §2.2)."""
    return json.dumps(situation, ensure_ascii=False, sort_keys=True)


def q_canonical(situation: dict) -> Hashable:
    """Cuantización canónica (default): identidad sobre la serialización JSON.

    Recupera el caso simbólico/discreto del LLC original: dos situaciones son
    equivalentes si y solo si su representación canónica es idéntica.
    """
    return serialize(situation)


def q_grid(embedding_fn: Callable[[dict], "list[float]"], h: float) -> QuantizationFn:
    """
    Cuantización por rejilla sobre embeddings (A1; para el Eje 1, sin uso por defecto):
    redondea cada coordenada del embedding a resolución h y usa la tupla como celda.

    Condición dura (SOLUCIONES_AUDITORIA §A1): Q debe CONGELARSE tras su ajuste — si Q
    cambia en el tiempo, la identidad de teorías deja de ser estable entre ventanas y
    los contadores P/K acumulados pierden semántica.
    """
    if h <= 0:
        raise ValueError("la resolución h debe ser positiva")

    def q(situation: dict) -> Hashable:
        return tuple(int(round(v / h)) for v in embedding_fn(situation))

    return q


def exact_sim(a: dict, b: dict) -> float:
    """(compat) similitud exacta 0/1 — ya no define la equivalencia de la base."""
    return 1.0 if a == b else 0.0


@dataclass
class Theory:
    si: dict[str, Any]           # situación inicial
    a: str                        # acción
    sf: dict[str, Any]           # situación final
    p: int = 0                    # éxitos
    k: int = 0                    # usos (expuesto; tras fusiones = K del grupo de celda)
    u: float = 0.0                # utilidad U(t) = acc(t) ∈ [0,1]  (Def. 5)
    created_at: int = 0           # contador monótono de la base (recencia; A5+A10)
    id: int = 0                   # id autoincremental dentro de la base (A5+A10)
    k_own: Optional[int] = None   # K PROPIO: contador aditivo conservado en fusiones (A1)

    def __post_init__(self):
        if self.p > self.k:
            raise ValueError("invariante de Def. 3 violada: P ≤ K")
        if self.k_own is None:
            self.k_own = self.k

    @property
    def reliability(self) -> float:
        """
        Confiabilidad con suavizado de Laplace (A2): (P+1)/(K+2).

        Media posterior Beta(1,1) — definida en K=0 (→ 0.5), regulariza teorías con
        pocos usos y converge a P/K cuando K crece. Reemplaza el estimador crudo P/K
        de la Def. 3, que era indefinido en K=0 y sobreconfiado con K chico.
        """
        return (self.p + 1) / (self.k + 2)

    def reinforce(self, success: bool) -> None:
        self.k += 1
        self.k_own += 1
        if success:
            self.p += 1

    def to_dict(self) -> dict[str, Any]:
        return {"si": self.si, "a": self.a, "sf": self.sf, "p": self.p,
                "k": self.k, "u": round(self.u, 6),
                "reliability": round(self.reliability, 4)}


def equivalent(a: dict, b: dict, q: QuantizationFn = q_canonical) -> bool:
    """Si ≅ Si′  ⟺  Q(Si) == Q(Si′)  (Def. 3, A1)."""
    return q(a) == q(b)


def theories_equal(t1: Theory, t2: Theory, q: QuantizationFn = q_canonical) -> bool:
    """Iguales: misma celda y variante — (Q(Si), A, Q(Sf)) idénticos."""
    return t1.a == t2.a and q(t1.si) == q(t2.si) and q(t1.sf) == q(t2.sf)


def theories_similar(t1: Theory, t2: Theory, q: QuantizationFn = q_canonical) -> bool:
    """Similares: misma celda — (Q(Si), A) — con distinta variante Q(Sf)."""
    return t1.a == t2.a and q(t1.si) == q(t2.si) and q(t1.sf) != q(t2.sf)


class TheoryBase:
    """
    Base de conocimiento de teorías de un agente (θᵢ, Def. 1/2), indexada por celda.

    El parámetro de equivalencia es `q` (cuantización) — NO un umbral de similitud:
    la similitud continua es asunto de la recuperación (core/retrieval.py). El índice
    por celda (Q(Si), A) → variantes hace find_equal/find_similar O(1) amortizado
    (antes O(n)).
    """

    def __init__(self, q: QuantizationFn = q_canonical) -> None:
        self.q = q
        self.theories: list[Theory] = []
        self._seq = 0                                       # recencia/id (A5+A10)
        self._by_cell: dict[tuple, list[Theory]] = {}       # (q(si), a) → variantes
        self._by_si: dict[Hashable, list[Theory]] = {}      # q(si) → teorías

    # ---- indexación ----
    def _cell(self, t: Theory) -> tuple:
        return (self.q(t.si), t.a)

    def add(self, theory: Theory) -> None:
        self._seq += 1
        theory.id = self._seq
        theory.created_at = self._seq
        self.theories.append(theory)
        self._by_cell.setdefault(self._cell(theory), []).append(theory)
        self._by_si.setdefault(self.q(theory.si), []).append(theory)

    def replace_all(self, theories: list[Theory]) -> None:
        """Reemplaza el contenido completo (fusiones Def. 7/8): re-indexa y re-estampa
        la recencia en el orden dado."""
        self.theories = []
        self._by_cell = {}
        self._by_si = {}
        self._seq = 0
        for t in theories:
            self.add(t)

    # ---- consultas (Def. 3/4) ----
    def applicable(self, situation: dict[str, Any]) -> list[Theory]:
        """Teorías cuya Si es equivalente (misma celda de Si) a la situación dada."""
        return list(self._by_si.get(self.q(situation), []))

    def select(self, situation: dict[str, Any]) -> Optional[Theory]:
        """
        Def. 4 con desempate determinista (A5+A10): orden lexicográfico
        (U desc, P desc, K asc, recencia desc, id asc).

        El desempate final es total y reproducible: ante (U, P, K) idénticos gana la
        teoría más reciente y, de persistir el empate, la de menor id. Nota: bajo
        Laplace (A2), si U := reliability, un empate en (Û, P) implica empate en K,
        de modo que el criterio "menor K" queda subsumido y decide la recencia.
        """
        cands = self.applicable(situation)
        if not cands:
            return None
        cands.sort(key=lambda t: (-t.u, -t.p, t.k, -t.created_at, t.id))
        return cands[0]

    def find_equal(self, theory: Theory) -> Optional[Theory]:
        qsf = self.q(theory.sf)
        for t in self._by_cell.get(self._cell(theory), []):
            if self.q(t.sf) == qsf:
                return t
        return None

    def find_similar(self, theory: Theory) -> Optional[Theory]:
        qsf = self.q(theory.sf)
        for t in self._by_cell.get(self._cell(theory), []):
            if self.q(t.sf) != qsf:
                return t
        return None

    def __len__(self) -> int:
        return len(self.theories)

    def to_json(self) -> str:
        return json.dumps([t.to_dict() for t in self.theories],
                          ensure_ascii=False, indent=2)
