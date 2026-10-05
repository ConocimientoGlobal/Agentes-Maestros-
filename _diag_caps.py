import sys, json
sys.path.insert(0, '.')
from neural_fellowship import AGENTES_ESPECIALIZADOS

# Ver capabilities reales de especialistas clave
for aid in ['design-brand-guardian', 'design-ui-designer', 'design-motion-designer',
            'engineering-backend-architect', 'engineering-frontend-developer',
            'engineering-mobile-app-builder', 'engineering-embedded-engineer',
            'marketing-content-creator', 'research-historian']:
    if aid in AGENTES_ESPECIALIZADOS:
        info = AGENTES_ESPECIALIZADOS[aid]
        print(f"{aid}: {info['capacidades']}")
    else:
        print(f"{aid}: NO EXISTE")