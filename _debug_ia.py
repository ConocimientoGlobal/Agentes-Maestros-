import sys, os
sys.path.insert(0, os.path.expanduser("~/Agentes-Maestros-audit"))
os.chdir(os.path.expanduser("~/Agentes-Maestros-audit"))
from neural_fellowship import Orquestador, AGENTES_MAESTROS

o = Orquestador()

# Full trace for IA query
query = 'modelo ml para predecir churn'
tarea_lower = query.lower()

print('=== IA query full trace ===')
for m, info in AGENTES_MAESTROS.items():
    score = 0
    reasons = []
    
    dominio = info['dominio'].lower()
    if dominio in tarea_lower:
        score += 40
        reasons.append(f'dominio: +40 ({info["dominio"]})')
    
    for kw in o.maestro_keywords.get(m, []):
        if kw.lower() in tarea_lower:
            score += 35
            reasons.append(f'keyword: {kw} +35')
    
    for esp in info.get('especialidades', []):
        esp_lower = esp.lower()
        # Word-boundary check: esp must match as whole word, not substring
        if esp_lower in tarea_lower:
            # Check it's not a substring of a larger word
            # e.g., 'pr' should not match 'predecir'
            idx = tarea_lower.find(esp_lower)
            while idx != -1:
                # Check boundaries
                left_ok = idx == 0 or not tarea_lower[idx - 1].isalnum()
                right_end = idx + len(esp_lower)
                right_ok = right_end >= len(tarea_lower) or not tarea_lower[right_end].isalnum()
                if left_ok and right_ok:
                    score += 25
                    reasons.append(f'especialidad: {esp} +25')
                    break
                idx = tarea_lower.find(esp_lower, idx + 1)
    
    div = info['division']
    if ' → ' in div:
        div = div.split(' → ')[0]
    if ' + ' in div:
        divs = div.split(' + ')
    else:
        divs = [div]
    
    for d in divs:
        for keyword in o.routing_map.get(d, []):
            if keyword in tarea_lower:
                score += 15
                reasons.append(f'routing[{d}]: {keyword} +15')
    
    routing_words = info.get('routing', '').lower().split(', ')
    for rw in routing_words:
        if len(rw) > 3 and rw in tarea_lower:
            score += 10
            reasons.append(f'routing_text: {rw} +10')
    
    if score > 0:
        print(f'  {m}: {score} pts - {reasons}')