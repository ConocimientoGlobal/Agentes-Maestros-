    def determinar_especialista(self, tarea: str, maestro: str = None) -> dict:
        """Encuentra el mejor especialista para una tarea con scoring restrictivo."""
        import re as _re
        tarea_lower = tarea.lower()
        tarea_tokens = set(_re.findall(r'[a-záéíóúñ]{3,}', tarea_lower))
        best_match = None
        best_score = 0

        # Tokens genéricos que no indican relevancia por sí solos
        _GENERIC_TOKENS = {"app", "web", "data", "design", "system", "user", "service", "tool", "general", "management", "page", "api"}

        # Keywords del maestro para fallback de scoring
        maestro_kws = set()
        if maestro:
            for div_kw in self.routing_map.get(maestro, []):
                maestro_kws.add(div_kw.lower())
            for kw in self.maestro_keywords.get(maestro, []):
                maestro_kws.add(kw.lower())

        for agent_id, info in AGENTES_ESPECIALIZADOS.items():
            if maestro and info["maestro"] != maestro:
                continue
            score = 0
            caps = info.get("capacidades", [])
            matched_tokens = set()

            for cap in caps:
                cap_norm = cap.lower().replace("-", " ")
                # CORRECCIÓN: descartar capability vacía tipo "c" (bug substring)
                if len(cap_norm) <= 2 or cap_norm.isdigit():
                    continue
                # Match exacto de tokens (no substring)
                cap_tokens = set(_re.findall(r'[a-z]{3,}', cap_norm))
                exact = cap_tokens & tarea_tokens
                if exact:
                    # Penalizar si solo match de tokens genéricos
                    non_generic = exact - _GENERIC_TOKENS
                    if non_generic:
                        score += 30 * len(non_generic)
                        matched_tokens.update(non_generic)
                    elif len(exact) >= 2:
                        # Múltiples tokens genéricos = parcial
                        score += 10
                    else:
                        # Solo un token genérico = irrelevante
                        pass

            # Match por nombre del especialista (solo tokens no genéricos)
            name_norm = agent_id.lower().replace("-", " ")
            name_tokens = set(_re.findall(r'[a-z]{3,}', name_norm))
            name_match = name_tokens & tarea_tokens - _GENERIC_TOKENS
            if name_match:
                score += 20

            # Bonus si el maestro coincide
            if info["maestro"] == maestro:
                score += 10

            # Fallback: keywords del maestro coinciden EXACTAMENTE en capacidades
            if score > 0 and maestro_kws:
                caps_list = [c.lower() for c in caps]
                for mk in maestro_kws:
                    if mk in caps_list and len(mk) > 4:
                        score += 8
                        break

            # Requerir al menos 2 tokens relevantes para considerar válido
            if len(matched_tokens) < 2 and score < 30:
                score = 0

            if score > best_score:
                best_score = score
                best_match = {
                    "especialista": agent_id,
                    "maestro": info["maestro"],
                    "confianza": min(score, 100),
                    "capacidades": caps
                }

        # Si el mejor match tiene confianza baja (< 30), intentar con keywords de especialista
        if best_score < 30 and maestro in self.especialista_keywords:
            for categoria, palabras in self.especialista_keywords[maestro].items():
                for palabra in palabras:
                    if palabra.lower() in tarea_lower:
                        for agent_id, info in AGENTES_ESPECIALIZADOS.items():
                            if info["maestro"] != maestro:
                                continue
                            caps_text = " ".join(info.get("capacidades", [])).lower().replace("-", " ")
                            if palabra.lower() in caps_text:
                                cat_score = 50 + (30 if palabra.lower() == tarea_lower.split()[0] else 0)
                                if cat_score > best_score:
                                    best_score = cat_score
                                    best_match = {
                                        "especialista": agent_id,
                                        "maestro": info["maestro"],
                                        "confianza": min(cat_score, 100),
                                        "capacidades": info.get("capacidades", [])
                                    }
                        break

        return best_match or {"especialista": None, "maestro": maestro or "PHOENIX", "confianza": 0, "capacidades": []}