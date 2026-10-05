import sys, re
sys.path.insert(0, '.')
from neural_fellowship import AGENTES_ESPECIALIZADOS, Orquestador

orch = Orquestador()

# Sinónimos actuales
_SINONIMOS = {
    "diseño": "design", "diseña": "design", "diseñar": "design",
    "logo": "logo", "logotipo": "logo", "minimalista": "minimal",
    "landing": "landing", "pagina": "page", "página": "page", "responsivo": "responsive",
    "datos": "data", "analisis": "analytics", "analítica": "analytics", "analizá": "analytics",
    "ventas": "sales", "trimestre": "quarter",
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
    "Automatizá la gestión de facturas y pagos",
    "Creá una landing page responsive para mi negocio",
]

for tarea in tareas:
    t = set(re.findall(r'[a-záéíóúñ]{3,}', tarea.lower()))
    expanded = set(t)
    for tok in t:
        if tok in _SINONIMOS:
            expanded.add(_SINONIMOS[tok])
    
    print(f"\n=== {tarea[:55]} ===")
    print(f"  Tokens: {sorted(t)}")
    print(f"  Expandidos: {sorted(expanded)}")
    
    # Buscar matches
    for aid, info in AGENTES_ESPECIALIZADOS.items():
        for cap in info.get("capacidades", []):
            cap_norm = cap.lower().replace("-", " ")
            cap_toks = set(re.findall(r'[a-z]{3,}', cap_norm))
            exact = cap_toks & expanded
            if exact:
                non_gen = exact - {"app", "web", "data", "design", "system", "user", "service", "tool", "general", "management", "page", "api"}
                print(f"    {aid:45s} cap='{cap:30s}' exact={sorted(exact)} non_gen={sorted(non_gen)}")