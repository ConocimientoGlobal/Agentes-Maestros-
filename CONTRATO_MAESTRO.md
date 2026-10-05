
CONTRATO DEL MAESTRO — Agentes-Maestros v0.20.6
===============================================

Maestro = {
    "id": str,              # Clave única (ARCAN, ORION, CONSTR...)
    "emoji": str,
    "dominio": str,
    "division": str,        # División funcional o "cross → usa X"
    "especialidades": [str],
    "automatizable": bool,
    "tipo": "maestro" | "constructor",  # Nuevo: tipo especial
    "politica_preferencia": [str],  # Orden de preferencia al proponer
    "modo_construccion": "proposal_only" | "approved",  # Control de aprobación
}

Especialista = {
    "id": str,
    "maestro": str,         # Referencia al Maestro padre
    "capacidades": [str],
    "herramientas": [str],  # Nuevo: herramientas que requiere
}

Constructor/Arquitecto (tipo maestro "constructor"):
- Recibe capability gap (de orquestar.py → EvolutionProposer)
- Analiza reutilización en orden de preferencia
- Investiga si necesario (fuentes externas)
- Produce propuesta estructurada con requires_human_approval=True
- NO modifica red sin aprobación explícita
- Registra propuesta en state/construction_queue.json

Políticas de preferencia (orden):
1. Reutilizar capability existente
2. Reutilizar especialista existente
3. Reutilizar Maestro existente
4. Combinar capacidades existentes
5. Extender capability existente
6. Crear nueva capability
7. Crear especialista
8. Crear Maestro
9. Crear nueva fábrica
