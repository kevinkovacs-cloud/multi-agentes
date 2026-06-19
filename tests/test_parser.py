"""P3 — robustez del parser: entradas heterogéneas y guardrail BIO de no-retención."""
from moav_hr.instances.hr.parser_agent import normalize_profile, build_si
from moav_hr.instances.hr.synthetic import get


def test_objeto_candidate():
    p = normalize_profile(get(3))
    assert "Python" in p["skills"] and p["exp"] == 3
    assert any("origin=" in s for s in p["_sensitive"])


def test_dict_con_sinonimos_y_mayusculas():
    raw = {"Habilidades": "Python, NLP", "Experiencia": "4 años",
           "Título": "Maestría", "género": "F", "Origen": "SY"}
    p = normalize_profile(raw)
    assert "Python" in p["skills"] and "NLP" in p["skills"]
    assert p["exp"] == 4 and p["edu"] == "Maestría"
    assert "gender=F" in p["_sensitive"] and any("origin" in s for s in p["_sensitive"])


def test_texto_html_libre():
    raw = "<div>Perfil: Python y PyTorch · 5 years exp · Doctorado</div>"
    p = normalize_profile(raw)
    assert "Python" in p["skills"] and "PyTorch" in p["skills"]
    assert p["exp"] == 5 and p["edu"] == "Doctorado"


def test_si_sin_atributos_protegidos():
    si = build_si(normalize_profile(get(3)))
    assert set(si) == {"skills_match", "exp_band", "edu", "seniority_ok"}
    assert not any(k in si for k in ("gender", "origin", "age", "name"))
