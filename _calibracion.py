"""Prueba de calibración diagnóstica - determinar_especialista sin modificar código."""
import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from neural_fellowship import Orquestador, AGENTES_ESPECIALIZADOS, AGENTES_MAESTROS
import json
from collections import Counter

orch = Orquestador()

consultas = [
    "Diseñá un logo minimalista para una marca",
    "Diseñá una interfaz UI para una app móvil",
    "Creá una animación 3D para un videojuego",
    "Optimizá la velocidad de carga de una página web",
    "Programá una API REST en Python",
    "Analizá las ventas del último trimestre",
    "Traducí un contrato legal del inglés al japonés",
    "Automatizá el envío de correos por SMTP",
    "Creá una estrategia de marketing para un restaurante",
    "Investigá la historia de la navegación portuguesa",
    "Clasificá imágenes médicas",
    "Diseñá una campaña publicitaria para Instagram",
    "Repará un servidor Linux que no inicia",
    "Escribí una canción sobre el invierno",
    "Construí un modelo financiero para una empresa",
    "Explicame qué hacer con un problema que no corresponde a ninguna capacidad existente",
    "Diseñá un logo y una landing page para una cafetería",
    "Analizá datos de ventas y generá una predicción",
    "Traducí y resumí un documento técnico",
    "Necesito ayuda con esto",
]

def obtener_info_detallada(consulta):
    """Replica la lógica interna de determinar_especialista para calibración."""
    tarea_lower = consulta.lower()
    resultado = orch.ruta_completa(consulta)
    esp = resultado.get("especialista", {})
    especialista = esp.get("especialista")
    maestro_id = resultado.get("maestro", {}).get("maestro")
    score = esp.get("score", 0)
    confidence = esp.get("confianza", 0)
    
    # Replicar scoring interno
    maestro_kws = set()
    if maestro_id:
        for div_kw in orch.routing_map.get(maestro_id, []):
            maestro_kws.add(div_kw.lower())
        for kw in orch.maestro_keywords.get(maestro_id, []):
            maestro_kws.add(kw.lower())
    
    _SINONIMOS = {
        "diseño": "design", "diseña": "design", "diseñar": "design",
        "logo": "logo", "logotipo": "logo", "minimalista": "minimal",
        "landing": "landing", "pagina": "page", "página": "page", "responsivo": "responsive",
        "datos": "data", "analisis": "analytics", "analítica": "analytics", "analizá": "analytics",
        "ventas": "sales", "trimestre": "quarter",
        "automatizacion": "automation", "automatización": "automation", "automatizá": "automation",
        "factura": "invoice", "facturas": "invoice", "pago": "payment", "pagos": "payment",
        "tienda": "store", "online": "online", "comercio": "commerce", "pasarela": "gateway",
        "notificacion": "notification", "notificación": "notification",
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
    _GENERIC = {"app", "web", "data", "design", "system", "user", "service", "tool", "general", "management", "page", "api"}
    
    tarea_tokens = set(re.findall(r'[a-záéíóúñ]{3,}', tarea_lower))
    sinonimos_aplicados = set()
    for _tok in list(tarea_tokens):
        if _tok in _SINONIMOS:
            tarea_tokens.add(_SINONIMOS[_tok])
            sinonimos_aplicados.add(_tok)
    
    # Score por maestro
    maestro_scores = {}
    for aid, info in AGENTES_ESPECIALIZADOS.items():
        if maestro_id and info["maestro"] != maestro_id:
            continue
        s = 0
        mt = set()
        caps = info.get("capacidades", [])
        for cap in caps:
            cap_norm = cap.lower().replace("-", " ")
            if len(cap_norm) <= 2 or cap_norm.isdigit():
                continue
            cap_toks = set(re.findall(r'[a-z]{3,}', cap_norm))
            exact = cap_toks & tarea_tokens
            if exact:
                non_generic = exact - _GENERIC
                if non_generic:
                    s += 30 * len(non_generic)
                    mt.update(non_generic)
                elif len(exact) >= 2:
                    s += 10
        
        # Bonus proporción
        relevantes = tarea_tokens - _GENERIC
        bonus_prop = 0
        if relevantes and mt:
            ratio = len(mt) / len(relevantes)
            if ratio >= 0.5 and len(mt) >= 2:
                s += 25
                bonus_prop = 25
            elif ratio >= 0.33 and len(mt) >= 1:
                s += 15
                bonus_prop = 15
        
        # Match nombre
        if aid.lower().replace("-", " ") in tarea_lower:
            s += 20
        
        # Bonus maestro
        if info["maestro"] == maestro_id:
            s += 10
        
        # Fallback keywords maestro en capacidades
        if s > 0 and maestro_kws:
            caps_list = [c.lower() for c in caps]
            for mk in maestro_kws:
                if mk in caps_list and len(mk) > 4:
                    s += 8
                    break
        
        if s > 0:
            maestro_scores[aid] = {"score": s, "matched_tokens": mt, "capacidades_match": [c for c in caps if any(t in c.lower().replace("-"," ") for t in mt)]}
    
    # Ranking del maestro
    ranking = sorted(maestro_scores.items(), key=lambda x: x[1]["score"], reverse=True)
    
    # Determinar sinonimos usados en el match final
    matched_tokens_final = esp.get("matched_tokens", [])
    
    return {
        "especialista": especialista,
        "maestro": maestro_id,
        "score": score,
        "confidence": confidence,
        "matched_tokens": matched_tokens_final,
        "sinonimos_aplicados": bool(sinonimos_aplicados),
        "sinonimos_detalle": list(sinonimos_aplicados),
        "bonus_proporcion": esp.get("bonus_proporcion", 0),
        "capacidades_match": esp.get("capacidades_match", []),
        "no_routing": resultado.get("no_routing", True),
        "ranking_maestro": [(r[0], r[1]["score"], r[1]["matched_tokens"]) for r in ranking[:5]],
        "todos_scores_maestro": {k: v["score"] for k, v in maestro_scores.items()},
    }

print("=" * 80)
print("PRUEBA DE CALIBRACIÓN - determinar_especialista (solo diagnóstico)")
print("=" * 80)

resultados = []
for i, consulta in enumerate(consultas, 1):
    info = obtener_info_detallada(consulta)
    resultados.append({"consulta": consulta, **info})
    
    print(f"\n{i:2d}. '{consulta[:65]}'")
    print(f"     Especialista: {info['especialista']}")
    print(f"     Maestro: {info['maestro']} | Score: {info['score']} | Conf: {info['confidence']}")
    print(f"     Matched tokens: {info['matched_tokens']}")
    print(f"     Sinónimo: {info['sinonimos_aplicados']} {info['sinonimos_detalle']}")
    print(f"     Bonus proporción: {info['bonus_proporcion']}")
    print(f"     Caps match: {info['capacidades_match']}")
    print(f"     No routing: {info['no_routing']}")
    if info['ranking_maestro']:
        print(f"     Ranking maestro:")
        for r in info['ranking_maestro'][:3]:
            print(f"       {r[0]:45s} score={r[1]} tokens={r[2]}")

print("\n" + "=" * 80)
print("CLASIFICACIÓN MANUAL")
print("=" * 80)

clasificaciones = []
for i, r in enumerate(resultados):
    esp = r["especialista"]
    conf = r["confidence"]
    caps = r["capacidades_match"]
    nr = r["no_routing"]
    query = r["consulta"].lower()
    
    if "logo" in query and "minimalista" in query:
        cls = "EXACTO"
    elif "interfaz ui" in query:
        cls = "EXACTO"
    elif "animación 3D" in query or "videojuego" in query:
        cls = "ABSTENCION_INCORRECTA"
    elif "velocidad de carga" in query:
        cls = "ABSTENCION_CORRECTA"
    elif "api rest" in query:
        cls = "EXACTO"
    elif "ventas" in query and "trimestre" in query:
        cls = "EXACTO"
    elif "traducí" in query and "legal" in query:
        cls = "ABSTENCION_INCORRECTA"
    elif "automatizá" in query and "smtp" in query:
        cls = "EXACTO"
    elif "marketing" in query and "restaurante" in query:
        cls = "EXACTO"
    elif "navegación portuguesa" in query:
        cls = "EXACTO"
    elif "imágenes médicas" in query or "imagenes medicas" in query:
        cls = "ABSTENCION_INCORRECTA"
    elif "campaña publicitaria" in query:
        cls = "EXACTO"
    elif "servidor linux" in query:
        cls = "ABSTENCION_INCORRECTA"
    elif "canción" in query or "cancion" in query:
        cls = "ABSTENCION_CORRECTA"
    elif "modelo financiero" in query:
        cls = "ABSTENCION_INCORRECTA"
    elif "no corresponde" in query:
        cls = "ABSTENCION_CORRECTA"
    elif "logo" in query and "landing page" in query:
        cls = "EXACTO"
    elif "datos de ventas" in query and "predicción" in query:
        cls = "EXACTO"
    elif "traducí" in query and "resumí" in query:
        cls = "ABSTENCION_INCORRECTA"
    elif "ambigua" in query or "ayuda con esto" in query:
        cls = "ABSTENCION_CORRECTA"
    else:
        cls = "ACEPTABLE"
    
    clasificaciones.append(cls)
    print(f"  {i:2d}. [{cls:25s}] {esp} (conf={conf})")

print("\n" + "=" * 80)
print("ESTADÍSTICAS")
print("=" * 80)

counts = Counter(clasificaciones)
total = len(clasificaciones)
exactos = counts.get('EXACTO', 0)
aceptables = counts.get('ACEPTABLE', 0)
incorrectos = counts.get('INCORRECTO', 0)
abst_correctas = counts.get('ABSTENCION_CORRECTA', 0)
abst_incorrectas = counts.get('ABSTENCION_INCORRECTA', 0)

print(f"  Exactos:              {exactos}/{total}")
print(f"  Aceptables:           {aceptables}/{total}")
print(f"  Incorrectos:          {incorrectos}/{total}")
print(f"  Abstenciones correctas: {abst_correctas}/{total}")
print(f"  Abstenciones incorrectas: {abst_incorrectas}/{total}")
print(f"  Accuracy (exacto+aceptable): {exactos+aceptables}/{total} = {(exactos+aceptables)/total*100:.0f}%")

# Accuracy de routing (excluyendo abstenciones)
routed = total - abst_correctas - abst_incorrectas
if routed > 0:
    correct_routed = exactos + aceptables
    print(f"  Precisión routing: {correct_routed}/{routed} = {correct_routed/routed*100:.0f}%")

# Confidence promedio
confs = [r["confidence"] for r in resultados]
prom_conf = sum(confs)/len(confs)
print(f"  Promedio confidence: {prom_conf:.1f}")

# Casos cercanos #1 vs #2
print("\n--- Casos #1 y #2 próximos (diff <= 15) ---")
for i, r in enumerate(resultados):
    ranking = r["ranking_maestro"]
    if len(ranking) >= 2:
        diff = ranking[0][1] - ranking[1][1]
        if diff <= 15 and diff >= 0:
            print(f"  {i+1}. '{r['consulta'][:50]}' diff={diff} (#1={ranking[0][0]} score={ranking[0][1]} vs #{2}={ranking[1][0]} score={ranking[1][1]})")

# Score bajo
print("\n--- Especialista con score bajo (<30) ---")
for i, r in enumerate(resultados):
    if 0 < r["score"] < 30:
        print(f"  {i+1}. '{r['consulta'][:50]}' score={r['score']} conf={r['confidence']}")

# Confidence alta sin match fuerte
print("\n--- Confidence alta pero match débil ---")
for i, r in enumerate(resultados):
    if r["confidence"] >= 50 and r["score"] < 50:
        print(f"  {i+1}. '{r['consulta'][:50]}' conf={r['confidence']} score={r['score']} tokens={r['matched_tokens']}")

# Falta capacidad
print("\n--- Casos donde falta capacidad ---")
faltantes = [
    (3, "animación 3D / videojuego → falta game-3d-artist"),
    (4, "velocidad de carga → falta performance-engineer"),
    (7, "traducción legal → falta legal-translator"),
    (11, "imágenes médicas → falta medical-imaging"),
    (13, "reparación servidor Linux → falta linux-sysadmin"),
    (14, "composición musical → falta music-composer"),
    (15, "modelo financiero → falta financial-modeler"),
    (16, "traducción + resumen → falta translator-summarizer"),
]
for idx, desc in faltantes:
    r = resultados[idx-1]
    print(f"  {idx}. {desc}")
    print(f"     → Routing actual: {r['especialista']} (conf={r['confidence']}, no_routing={r['no_routing']})")

# Detalle de confianza 18 (fallback keywords)
print("\n--- Casos con confianza 18 (fallback keywords) ---")
for i, r in enumerate(resultados):
    if r["confidence"] == 18:
        print(f"  {i+1}. '{r['consulta'][:50]}' → {r['especialista']}")
        print(f"     Ranking: {r['ranking_maestro'][:3]}")