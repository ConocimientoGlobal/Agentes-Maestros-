import sys, re
sys.path.insert(0, '.')
from neural_fellowship import AGENTES_ESPECIALIZADOS

def toks(texto):
    return set(re.findall(r'[a-záéíóúñ]{3,}', texto.lower()))

# Sinónimos actuales
_SINONIMOS = {
    "diseño": "design", "diseña": "design", "logo": "logo", "logotipo": "logo",
    "datos": "data", "analisis": "analytics", "analizá": "analytics",
    "automatizacion": "automation", "automatizá": "automation",
    "factura": "invoice", "facturas": "invoice", "pago": "payment", "pagos": "payment",
    "tienda": "store", "online": "online", "comercio": "commerce",
    "notificacion": "notification", "notifications": "notification",
    "push": "push", "sistema": "system",
    "rendimiento": "performance", "optimizacion": "optimization", "optimizá": "optimization",
    "base": "database", "chatbot": "chatbot", "bot": "bot",
    "lenguaje": "language", "natural": "natural", "procesamiento": "processing",
    "autenticacion": "authentication", "oauth": "oauth", "api": "api",
    "movil": "mobile", "móvil": "mobile", "ios": "ios", "android": "android",
    "app": "app", "aplicacion": "app",
    "video": "video", "animacion": "animation",
    "sonido": "sound", "audio": "audio", "musica": "music",
    "redes": "social", "social": "social", "contenido": "content",
    "marketing": "marketing", "branding": "branding", "marca": "brand",
    "identidad": "identity", "web": "web", "frontend": "frontend",
    "backend": "backend", "servidor": "server",
    "seguridad": "security", "testing": "testing", "test": "test",
    "devops": "devops", "infraestructura": "infrastructure",
    "juego": "game", "3d": "3d", "2d": "2d",
    "modelo": "model", "pixel": "pixel", "sprite": "sprite",
    "ui": "ui", "ux": "ux", "interfaz": "interface", "usuario": "user",
    "carga": "load", "velocidad": "speed", "rapido": "fast",
    "cicd": "cicd", "cloud": "cloud", "kubernetes": "kubernetes",
    "blockchain": "blockchain", "crypto": "crypto",
    "producto": "product", "roadmap": "roadmap", "gestion": "management",
    "documentacion": "documentation", "traduccion": "translation",
    "idioma": "language", "legal": "legal", "contrato": "contract",
    "compliance": "compliance", "finanzas": "finance", "presupuesto": "budget",
    "costo": "cost", "historia": "history", "investigacion": "research",
    "fuentes": "sources", "primarias": "primary",
    "desarrollá": "development", "implementá": "implementation",
    "construí": "build", "creá": "create", "gestión": "management",
    "landing": "landing", "pagina": "page", "responsivo": "responsive",
    "ventas": "sales", "trimestre": "quarter", "pasarela": "gateway",
    "minimalista": "minimal", "último": "last", "del": "of",
}

tareas = [
    "Diseña un logo minimalista para una app",
    "Creá una landing page responsive para mi negocio",
    "Analizá los datos de ventas del último trimestre",
    "Automatizá la gestión de facturas y pagos",
    "Construí una tienda online con pasarela de pago",
    "Diseñá un sistema de notifications push para la app",
    "Optimizá el rendimiento de la base de datos",
    "Creá un chatbot con procesamiento de lenguaje natural",
    "Implementá autenticación OAuth2 para la API",
    "Desarrollá una app móvil para iOS y Android",
]

for tarea in tareas:
    tarea_toks = toks(tarea)
    expandidos = set(tarea_toks)
    for t in tarea_toks:
        if t in _SINONIMOS:
            expandidos.add(_SINONIMOS[t])
    print(f"\n=== {tarea}")
    print(f"  tokens: {sorted(tarea_toks)}")
    print(f"  expandidos: {sorted(expandidos)}")
    
    # Ver qué capabilities matchean
    matches = []
    for aid, info in AGENTES_ESPECIALIZADOS.items():
        for cap in info.get('capacidades', []):
            cap_norm = cap.lower().replace('-', ' ')
            cap_toks = set(re.findall(r'[a-z]{3,}', cap_norm))
            exact = cap_toks & expandidos
            if exact:
                matches.append((aid, cap, exact, len(exact), len(cap_toks)))
    
    if matches:
        for aid, cap, exact, n, total in matches:
            print(f"  MATCH {aid} cap='{cap}' exact={exact} prop={n}/{total}")
    else:
        print(f"  NO MATCHES")