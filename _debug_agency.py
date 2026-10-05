import sys, os
sys.path.insert(0, os.path.expanduser("~/Agentes-Maestros-audit"))
os.chdir(os.path.expanduser("~/Agentes-Maestros-audit"))
from neural_fellowship import Orquestador, AGENTES_MAESTROS

o = Orquestador()

# Check AGENCY for 'modelo ml para predecir churn'
query = 'modelo ml para predecir churn'
tarea_lower = query.lower()

print('=== AGENCY ===')
info = AGENTES_MAESTROS['AGENCY']
score = 0
reasons = []

dominio = info['dominio'].lower()
if dominio in tarea_lower:
    score += 40
    reasons.append(f'dominio: +40 ({info["dominio"]})')

for kw in o.maestro_keywords.get('AGENCY', []):
    if kw.lower() in tarea_lower:
        score += 35
        reasons.append(f'keyword: {kw} +35')

for esp in info.get('especialidades', []):
    esp_lower = esp.lower().replace('-', ' ')
    if esp_lower in tarea_lower:
        score += 25
        reasons.append(f'especialidad: {esp} +25')

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

print(f'AGENCY: {score} pts - {reasons}')