"""Bloque D · D1: selección de teoría por embeddings (demo para la dirección)."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "experiments" / "demos_direccion"))

from comun import ROTULOS  # noqa: E402
from moav_hr.instances.hr.pipeline import HRPipeline  # noqa: E402

CLAVES = {"rotulos", "demo", "base", "consulta", "delta", "top_k", "clave_de_orden",
          "teorias", "token_cosine", "embeddings", "comparacion", "figuras"}


def test_d1_corre_con_token_cosine_sin_modelo(tmp_path):
    import d1_embeddings
    d1_embeddings.correr(tmp_path, backend="token-cosine")
    data = json.loads((tmp_path / "d1_embeddings.json").read_text(encoding="utf-8"))
    assert CLAVES <= set(data)
    assert data["rotulos"] == ROTULOS
    # el δ que rige es el del retriever del Matcher, no el default de TheoryRetriever
    assert data["delta"]["rige"] == HRPipeline(mode="sim").matcher.retriever.delta
    assert data["embeddings"]["disponible"] is False
    assert data["comparacion"] is None
    tok = data["token_cosine"]
    assert tok["seleccionada"] == tok["recuperadas_top_k"][0]
    assert set(tok["recuperadas_top_k"]) <= set(tok["superan_delta"])
    assert len(data["teorias"]) == data["base"]["n_teorias"]
    assert (tmp_path / "d1_similitud_barras.png").exists()
    assert not (tmp_path / "d1_espacio_embeddings.png").exists()


def test_d1_embeddings(tmp_path):
    pytest.importorskip("sentence_transformers")
    import d1_embeddings
    s = d1_embeddings.correr(tmp_path, backend="auto")
    if not s["embeddings"]["disponible"]:
        pytest.skip(f"modelo de embeddings no disponible: {s['embeddings']['error']}")
    emb = s["embeddings"]
    # el coseno de los vectores coincide con core.retrieval.similarity (backend real)
    assert emb["verificacion_max_dif_coseno_vs_similarity"] < 1e-5
    assert emb["seleccionada"] == emb["recuperadas_top_k"][0]
    assert isinstance(s["comparacion"]["misma_seleccionada"], bool)
    assert (tmp_path / "d1_espacio_embeddings.png").exists()
    assert (tmp_path / "d1_similitud_barras.png").exists()
