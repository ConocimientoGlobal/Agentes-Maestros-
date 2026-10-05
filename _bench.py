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
    resultados.append({
        "tarea": tarea,
        "maestro": r.get("maestro"),
        "especialista": r.get("especialista"),
        "confianza": r.get("confianza"),
        "senial": r.get("senal_routing"),
        "propuesta": r.get("propuesta_evolucion"),
    })
print(json.dumps(resultados, indent=2, ensure_ascii=False))