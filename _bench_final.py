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

results = []
for t in tareas:
    r = orch.ruta_completa(t)
    esp = r["especialista"]["especialista"]
    conf = r["especialista"]["confianza"]
    maestro = r["maestro"]["maestro"]
    esp_str = esp if esp else "NULL"
    results.append({"tarea": t, "especialista": esp, "confianza": conf, "maestro": maestro})
    print(f"  {t[:55]:57s} → {esp_str:45s} conf={conf}")

# Métricas
total = len(results)
con_match = sum(1 for r in results if r["especialista"] is not None)
sin_routing = sum(1 for r in results if r["especialista"] is None)
conf_prom = sum(r["confianza"] for r in results) / total if total else 0

print(f"\nTotal: {total}")
print(f"Con match: {con_match} ({con_match*100/total:.0f}%)")
print(f"Sin routing: {sin_routing} ({sin_routing*100/total:.0f}%)")
print(f"Confianza promedio: {conf_prom:.1f}")