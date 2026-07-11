"""C3 — flag MOAV_SIMILARITY: con el default el comportamiento es idéntico al actual."""
import pytest

from moav_hr.core.retrieval import TheoryRetriever, similarity
from moav_hr.core.theory import Theory, TheoryBase


def _base() -> TheoryBase:
    b = TheoryBase()
    b.add(Theory(si={"skill": "python", "exp": 5}, a="ADVANCE", sf={"r": 1}, p=3, k=4, u=0.9))
    b.add(Theory(si={"skill": "python", "exp": 2}, a="REJECT", sf={"r": 0}, p=2, k=3, u=0.7))
    b.add(Theory(si={"skill": "java", "exp": 9}, a="ADVANCE", sf={"r": 1}, p=1, k=2, u=0.5))
    return b


def test_default_token_cosine_sin_flag(monkeypatch):
    monkeypatch.delenv("MOAV_SIMILARITY", raising=False)
    assert similarity({"a": 1, "b": 2}, {"a": 1, "b": 2}) == pytest.approx(1.0)
    assert similarity({"a": 1}, {"a": 2}) == 0.0            # valores distintos: sin token común


def test_flag_off_rankings_identicos(monkeypatch):
    monkeypatch.delenv("MOAV_SIMILARITY", raising=False)
    r = TheoryRetriever(_base(), delta=0.4, top_k=2)
    got = [t.a for t in r.retrieve({"skill": "python", "exp": 5})]
    monkeypatch.setenv("MOAV_SIMILARITY", "token-cosine")   # explícito == default
    got2 = [t.a for t in r.retrieve({"skill": "python", "exp": 5})]
    assert got == got2 == ["ADVANCE", "REJECT"]


def test_backend_desconocido_es_error(monkeypatch):
    monkeypatch.setenv("MOAV_SIMILARITY", "magia")
    with pytest.raises(ValueError):
        similarity({"a": 1}, {"a": 1})


def test_embeddings_sin_extra_da_import_error(monkeypatch):
    monkeypatch.setenv("MOAV_SIMILARITY", "embeddings")
    try:
        import sentence_transformers  # noqa: F401
        pytest.skip("sentence-transformers instalado: este test cubre el caso SIN extra")
    except ImportError:
        with pytest.raises(ImportError, match="embeddings"):
            similarity({"a": 1}, {"a": 1})
