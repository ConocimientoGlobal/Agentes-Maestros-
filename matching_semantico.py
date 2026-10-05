"""Helpers para matching de capabilities — corrige bugs de substring."""
import re

from neural_fellowship import AGENTES_ESPECIALIZADOS, ES_CAPABILITIES


def _toks(texto: str) -> set:
    return set(re.findall(r'[a-z]{3,}', texto.lower()))


def _cap_toks(cap: str) -> set:
    return set(re.findall(r'[a-z]{3,}', cap.lower().replace('-', ' ')))


def sinergia_score(cap: str, tarea_toks: set) -> int:
    """Score semántico de una capability contra tokens de tarea."""
    cap_lower = cap.lower()
    tarea_lower = ' '.join(tarea_toks)
    score = 0
    # 1) Match exacto de tokens (excluye substrings cortos)
    cap_toks = _cap_toks(cap)
    for t in cap_toks:
        if t in tarea_toks:
            score += 12  # +12 por token, no +30 por substring
    # 2) Match de sinónimos (cap en ES_CAPABILITIES)
    sin = ES_CAPABILITIES.get(cap_lower, set())
    sin_tokens = set()
    for s in sin:
        sin_tokens.update(_cap_toks(s))
    for t in sin_tokens:
        if t in tarea_toks and t not in cap_toks:
            score += 6  # bonus sinónimo más conservador
    # 3) Penalización si NO hay tokens relevantes y la cap es corta/específica
    # Las capabilities tipo "c", "x", "i" son placeholders vacíos — nunca deben ganar
    if not cap_toks.intersection(tarea_toks):
        if len(cap_lower) <= 2 or cap_lower.isdigit():
            score -= 100  # descartar placeholder vacío
    return score


def mejor_especialista(tarea: str, maestro: str = None) -> dict:
    """Encuentra el mejor especialista para una tarea usando matching semántico."""
    tarea_toks = _toks(tarea)
    best_match = None
    best_score = 0

    for agent_id, info in AGENTES_ESPECIALIZADOS.items():
        if maestro and info["maestro"] != maestro:
            continue
        score = 0
        for cap in info.get("capacidades", []):
            score += sinergia_score(cap, tarea_toks)
        if score > best_score:
            best_score = score
            best_match = {
                "especialista": agent_id,
                "maestro": info["maestro"],
                "confianza": min(score, 100),
                "capacidades": info.get("capacidades", [])
            }

    return best_match or {"especialista": None, "maestro": maestro or "PHOENIX", "confianza": 0, "capacidades": []}