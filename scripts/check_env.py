#!/usr/bin/env python
"""
Verificación del entorno de MOACV / MOAV-HR.

Comprueba que el stack completo esté operativo:
  - versión de Python
  - dependencias clave importables (orquestación, fairness, trazabilidad)
  - servidor Ollama accesible y modelo presente
  - inferencia real end-to-end vía langchain-ollama
  - código del paquete importable y tests de teorías

Uso:
    .venv/bin/python scripts/check_env.py
"""
from __future__ import annotations
import importlib
import os
import sys
import urllib.request
import json

OLLAMA_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1:8b")

ok = True


def line(status: str, msg: str) -> None:
    print(f"  {status}  {msg}")


def check_imports() -> None:
    global ok
    print("\n[1] Dependencias Python")
    paquetes = [
        ("langchain", "orquestación"),
        ("langgraph", "DAG de agentes"),
        ("langchain_ollama", "integración LLM local"),
        ("ollama", "cliente Ollama"),
        ("fairlearn", "fairness"),
        ("aif360", "fairness (IBM)"),
        ("sklearn", "ML base"),
        ("numpy", "numérico"),
        ("pandas", "datos"),
        ("datasets", "HuggingFace datasets"),
        ("opentelemetry", "trazabilidad"),
        ("langfuse", "observabilidad LLM"),
        ("pydantic", "validación"),
        ("dotenv", "config .env"),
        ("pytest", "tests"),
    ]
    for mod, desc in paquetes:
        try:
            m = importlib.import_module(mod)
            ver = getattr(m, "__version__", "?")
            line("✅", f"{mod:<18} {ver:<12} ({desc})")
        except Exception as e:  # noqa: BLE001
            ok = False
            line("❌", f"{mod:<18} FALLÓ: {e}")


def check_ollama_server() -> None:
    global ok
    print("\n[2] Servidor Ollama")
    try:
        with urllib.request.urlopen(f"{OLLAMA_URL}/api/version", timeout=5) as r:
            ver = json.loads(r.read()).get("version", "?")
        line("✅", f"servidor accesible en {OLLAMA_URL} (v{ver})")
    except Exception as e:  # noqa: BLE001
        ok = False
        line("❌", f"no se pudo contactar el servidor: {e}")
        return
    try:
        with urllib.request.urlopen(f"{OLLAMA_URL}/api/tags", timeout=5) as r:
            tags = [m["name"] for m in json.loads(r.read()).get("models", [])]
        if any(MODEL in t for t in tags):
            line("✅", f"modelo '{MODEL}' presente")
        else:
            ok = False
            line("❌", f"modelo '{MODEL}' no encontrado. Disponibles: {tags}")
    except Exception as e:  # noqa: BLE001
        ok = False
        line("❌", f"no se pudo listar modelos: {e}")


def check_llm_inference() -> None:
    global ok
    print("\n[3] Inferencia end-to-end (langchain-ollama)")
    try:
        from langchain_ollama import ChatOllama

        llm = ChatOllama(model=MODEL, num_predict=10, temperature=0)
        resp = llm.invoke("Respondé únicamente con la palabra: OK")
        text = (resp.content or "").strip()
        line("✅", f"ChatOllama respondió: {text!r}")
    except Exception as e:  # noqa: BLE001
        ok = False
        line("❌", f"inferencia falló: {e}")


def check_package() -> None:
    global ok
    print("\n[4] Código del paquete MOACV")
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
    try:
        from moav_hr.core.theory import Theory, TheoryBase     # núcleo genérico
        from moav_hr.core.ontology import shapes, abox
        from moav_hr.instances.hr.pipeline import HRPipeline
        from moav_hr.instances.hr.synthetic import get

        # mini-smoke: selección de teorías (Def. 4)
        tb = TheoryBase()
        tb.add(Theory(si={"x": 1}, a="advance", sf={"r": "ok"}, p=5, k=10, u=0.8))
        tb.add(Theory(si={"x": 1}, a="reject", sf={"r": "no"}, p=8, k=10, u=0.8))
        assert tb.select({"x": 1}).a == "reject"

        # mini-smoke: pipeline HR (sim) + ontología RDF + SHACL
        p = HRPipeline(mode="sim")
        p.warmup([get(3)])
        st = p.process(get(3))
        assert st["decision"] == "ESCALATE_HUMAN"
        conforms, _ = shapes.validate(abox.build_abox(st, agents=list(p.agents)))
        assert conforms
        line("✅", "core + instances/hr OK · pipeline sim + ontología RDF/SHACL conforme")
    except Exception as e:  # noqa: BLE001
        ok = False
        line("❌", f"paquete falló: {e}")


if __name__ == "__main__":
    print(f"Python {sys.version.split()[0]}  ({sys.executable})")
    check_imports()
    check_ollama_server()
    check_llm_inference()
    check_package()
    print("\n" + ("=" * 48))
    if ok:
        print("✅ ENTORNO OK — listo para construir los agentes MOACV")
        sys.exit(0)
    else:
        print("❌ HAY PROBLEMAS — revisá las líneas marcadas arriba")
        sys.exit(1)
