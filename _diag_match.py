import sys, re
sys.path.insert(0, '.')
from neural_fellowship import AGENTES_ESPECIALIZADOS, Orquestador

orch = Orquestador()

def toks(text):
    text = text.lower()
    text = re.sub(r'[^a-záéíóúñ0-9]+', ' ', text)
    return set(t for t in text.split() if len(t) >= 3)

tareas = [
 "Diseña un logo minimalista para una app",
 "Generá un informe financiero trimestral",
 "Creá una landing page responsive",
 "Optimizá la velocidad de carga de la web",
 "Desarrollá un juego 3D con ray tracing",
 "Arreglá un bug en el servidor",
 "Configurá el servidor SMTP",
 "Analizá los datos de ventas del mes",
 "Traducí la documentación legal al japonés",
 "Diseñá un ícono para la app de bienestar",
]
for t in tareas:
    tt = toks(t)
    hits = []
    for aid, info in AGENTES_ESPECIALIZADOS.items():
        caps = info.get('capacidades', [])
        for cap in caps:
            ct = set(x for x in re.split(r'[-_ ]+', cap.lower()) if len(x) >= 3)
            inter = ct.intersection(tt)
            if inter:
                hits.append((aid, cap, sorted(inter)))
    print(f'--- {t}')
    print(f'    tokens={sorted(tt)}')
    for h in hits[:8]:
        print(f'    {h[0]:38s} cap={h[1]:24s} match={h[2]}')
    if not hits:
        print('    (sin match)')
