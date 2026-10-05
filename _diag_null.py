import sys, re
sys.path.insert(0, '.')
from neural_fellowship import AGENTES_ESPECIALIZADOS

def toks(texto):
    return set(re.findall(r'[a-záéíóúñ]{3,}', texto.lower()))

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

def match_tokens(tarea_tokens, capa_tokens, sinonimos):
    """Matching token-based con sinónimos."""
    expanded = set(tarea_tokens)
    for t in tarea_tokens:
        if t in sinonimos:
            expanded.add(sinonimos[t])

    exact = capa_tokens & expanded
    non_generic = exact - {"app", "web", "data", "design", "system", "user", "service", "tool", "general", "management", "page", "api"}
    return exact, non_generic

# Revisar tasks que dan NULL para ver qué capability les falta
for tarea in tareas:
    t = toks(tarea)
    expanded = set(t)
    for tok in t:
        if tok in _SINONIMOS:
            expanded.add(_SINONIMOS[tok])

    relevantes = t - {"app", "web", "data", "design", "system", "user", "service", "tool", "general", "management", "page", "api"}
    print(f"\n=== {tarea[:55]} ===")
    print(f"  relevantes: {sorted(relevantes)}")
    print(f"  expanded: {sorted(expanded)}")

    # Buscar cualquier capability que tenga al menos 1 token relevante
    for aid, info in AGENTES_ESPECIALIZADOS.items():
        for cap in info.get("capacidades", []):
            cap_norm = cap.lower().replace("-", " ")
            cap_toks = set(re.findall(r'[a-z]{3,}', cap_norm))
            exact = cap_toks & expanded
            non_gen = exact - {"app", "web", "data", "design", "system", "user", "service", "tool", "general", "management", "page", "api"}
            if non_gen:
                print(f"    {aid:45s} cap='{cap:30s}' match={sorted(non_gen)}")