"""P4 — regla no negociable: core/ no importa nada de instances/."""
import glob
import os
import re

CORE = os.path.join(os.path.dirname(__file__), "..", "src", "moav_hr", "core")


def test_core_no_importa_instances():
    offenders = []
    for f in glob.glob(os.path.join(CORE, "**", "*.py"), recursive=True):
        with open(f, encoding="utf-8") as fh:
            if re.search(r"(from|import)\s+moav_hr\.instances|import\s+.*instances", fh.read()):
                offenders.append(os.path.relpath(f))
    assert not offenders, f"core importa instances: {offenders}"
