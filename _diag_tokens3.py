import sys, re
sys.path.insert(0, '.')
from neural_fellowship import AGENTES_ESPECIALIZADOS

def toks(texto):
    return set(re.findall(r'[a-záéíóúñ]{3,}', texto.lower()))

# Sinónimos ES→EN actuales (los que hay en el código)
_SINONIMOS = {
    "diseño": "design", "diseno": "design", "diseña": "design", "diseñar": "design",
    "logo": "logo", "logotipo": "logo", "minimalista": "minimal",
    "landing": "landing", "pagina": "page", "página": "page", "responsivo": "responsive",
    "datos": "data", "analisis": "analytics", "analítica": "analytics",
    "analizá": "analytics", "ventas": "sales", "trimestre": "quarter",
    "automatizacion": "automation", "automatización": "automation", "automatizá": "automation",
    "factura": "invoice", "facturas": "invoice", "pago": "payment", "pagos": "payment",
    "tienda": "store", "online": "online", "comercio": "commerce", "pasarela": "gateway",
    "notificacion": "notification", "notificación": "notification", "notifications": "notification",
    "push": "push", "sistema": "system", "rendimiento": "performance",
    "optimizacion": "optimization", "optimización": "optimization", "optimizá": "optimization",
    "base": "database", "chatbot": "chatbot", "bot": "bot",
    "lenguaje": "language", "natural": "natural", "procesamiento": "processing",
    "autenticacion": "authentication", "autenticación": "authentication", "oauth": "oauth",
    "api": "api", "movil": "mobile", "móvil": "mobile", "ios": "ios", "android": "android",
    "app": "app", "aplicacion": "app", "aplicación": "app",
    "video": "video", "animacion": "animation", "animación": "animation",
    "sonido": "sound", "audio": "audio", "musica": "music", "música": "music",
    "redes": "social", "social": "social", "contenido": "content",
    "marketing": "marketing", "branding": "branding", "marca": "brand",
    "identidad": "identity", "web": "web", "frontend": "frontend",
    "backend": "backend", "servidor": "server",
    "seguridad": "security", "testing": "testing", "test": "test",
    "devops": "devops", "infraestructura": "infrastructure",
    "juego": "game", "3d": "3d", "2d": "2d",
    "modelo": "model", "pixel": "pixel", "sprite": "sprite",
    "ui": "ui", "ux": "ux", "interfaz": "interface", "usuario": "user",
    "carga": "load", "velocidad": "speed", "rapido": "fast", "rápido": "fast",
    "cicd": "cicd", "cloud": "cloud", "kubernetes": "kubernetes",
    "blockchain": "blockchain", "crypto": "crypto", "smart": "contract",
    "producto": "product", "roadmap": "roadmap", "gestion": "management",
    "documentacion": "documentation", "documentación": "documentation",
    "traduccion": "translation", "traducción": "translation", "idioma": "language",
    "legal": "legal", "contrato": "contract", "compliance": "compliance",
    "finanzas": "finance", "presupuesto": "budget", "costo": "cost",
    "historia": "history", "investigacion": "research", "investigación": "research",
    "fuentes": "sources", "primarias": "primary",
    "desarrollá": "development", "implementá": "implementation",
    "construí": "build", "creá": "create", "gestión": "management",
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
    t = toks(tarea)
    expanded = set(t)
    for tok in t:
        if tok in _SINONIMOS:
            expanded.add(_SINONIMOS[tok])

    print(f"\n=== {tarea[:50]} ===")
    print(f"  Tokens tarea: {sorted(t)}")
    print(f"  Tokens expandidos: {sorted(expanded)}")

    # Buscar mejor match por capability
    matches = []
    for aid, info in AGENTES_ESPECIALIZADOS.items():
        for cap in info.get("capacidades", []):
            cap_norm = cap.lower().replace("-", " ")
            cap_toks = set(re.findall(r'[a-z]{3,}', cap_norm))
            exact = cap_toks & expanded
            if exact:
                matches.append((aid, cap, sorted(exact), len(exact)))

    if matches:
        matches.sort(key=lambda x: -x[3])
        print(f"  Mejores matches:")
        for m in matches[:5]:
            print(f"    {m[0]:40s} cap='{m[1]:30s}' tokens={m[2]}")
    else:
        print(f"  Sin matches de capability")