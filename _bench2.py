import sys, json
sys.path.insert(0, '.')
from neural_fellowship import Orquestador
orch = Orquestador()
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
resultados = []
for tarea in tareas:
    r = orch.ruta_completa(tarea)
    esp = r.get('especialista', {})
    resultados.append({
        "tarea": tarea,
        "maestro": r.get('maestro', {}).get('maestro', '?'),
        "especialista": esp.get('especialista', 'NULL'),
        "confianza": esp.get('confianza', 0),
    })
for r in resultados:
    tarea = r['tarea'][:50] if r['tarea'] else '?'
    esp = r['especialista'] or 'NULL'
    conf = r['confianza'] or 0
    print(f"{tarea:52s} → {esp:40s} conf={conf}")