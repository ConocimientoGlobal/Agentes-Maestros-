#!/usr/bin/env python3
"""
NEURAL FELLOWSHIP — Red Neuronal de Agentes Autónomos (Consolidada)
=================================================================
Sistema unificado de orquestación, routing, memoria y aprendizaje.

Estructura:
  - 63 Agentes Maestros (nodos de dominio)
  - 85 Agentes Especializados (nodos hoja)
  - Orquestador (routing + delegación)
  - Auto-Executor (tareas mecánicas)
  - Memory System (grafo + lecciones)
  - Learning System (errores → checklist)

Uso:
  python3 neural_fellowship.py                  # Scan + propuestas
  python3 neural_fellowship.py --auto           # Auto-ejecutar tareas mecánicas
  python3 neural_fellowship.py --route "tarea"  # Ruteo al agente correcto
  python3 neural_fellowship.py --agents         # Listar todos los agentes
  python3 neural_fellowship.py --maestros       # Listar solo maestros
  python3 neural_fellowship.py --status         # Estado del sistema
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

HOME = Path.home()
KNOWLEDGE_DIR = HOME / "knowledge"
PROJECTS_DIR = KNOWLEDGE_DIR / "_projects"
ACTIVE_DIR = KNOWLEDGE_DIR / "_active"
TODAY_FILE = KNOWLEDGE_DIR / "TODAY.md"
QUEUE_FILE = HOME / "agency-agents" / "orchestrator-logs" / "agent_queue.json"
STATE_FILE = HOME / "agency-agents" / "orchestrator-logs" / "executor_state.json"
LOG_DIR = HOME / "agency-agents" / "orchestrator-logs"
SKILL_DIR = Path(__file__).parent.parent
AGENT_DIR = SKILL_DIR / "references" / "agent_directory.json"
MEMORY_INDEX = SKILL_DIR / "references" / "memory_index.json"
LESSONS_FILE = SKILL_DIR / "references" / "learned_lessons.json"
ORCHESTRATOR_STATE = SKILL_DIR / "references" / "orchestrator_state.json"

# ============================================================================
# 63 AGENTES MAESTROS — Nodos de Dominio
# ============================================================================

AGENTES_MAESTROS = {
    "ARCAN": {
        "dominio": "Creatividad",
        "division": "design",
        "emoji": "🎨",
        "especialidades": ["branding", "ui-design", "ux-research", "ilustración", "imagen-generativa", "storytelling-visual", "persona-walkthrough", "whimsy"],
        "routing": "Tareas de diseño, marca, experiencia de usuario, interfaces, contenido visual",
        "automatizable": False,
    },
    "ORION": {
        "dominio": "Investigación",
        "division": "research + academic",
        "emoji": "🔬",
        "especialidades": ["literature-review", "síntesis-evidencia", "estadística", "antropología", "historia", "narratología", "psicología", "geografía"],
        "routing": "Investigación académica, análisis de datos, literatura, estudios de mercado",
        "automatizable": False,
    },
    "NEXUS": {
        "dominio": "Desarrollo",
        "division": "engineering",
        "emoji": "⚙️",
        "especialidades": ["frontend", "backend", "mobile", "devops", "database", "security-code", "ai-engineering", "llm-post-training", "rag", "prompt-engineering", "api-platform", "embedded", "webassembly", "search-relevance", "multi-agent-systems"],
        "routing": "Código, arquitectura de sistemas, infraestructura, bases de datos, AI/ML, LLMs",
        "automatizable": True,
    },
    "AURUM": {
        "dominio": "Finanzas",
        "division": "finance",
        "emoji": "💰",
        "especialidades": ["modeling", "fp&a", "bookkeeper", "tax", "investment", "pricing", "lbo", "dcf", "merger-model", "comps-analysis"],
        "routing": "Modelos financieros, contabilidad, impuestos, inversiones, valuaciones",
        "automatizable": False,
    },
    "SENTINEL": {
        "dominio": "Seguridad",
        "division": "security",
        "emoji": "🛡️",
        "especialidades": ["pentesting", "appsec", "compliance", "threat-intel", "incident-response", "blockchain-security", "secrets-hygiene", "cloud-security", "code-audit"],
        "routing": "Pentesting, auditoría, cumplimiento, threat modeling, DevSecOps",
        "automatizable": False,
    },
    "MERIDIAN": {
        "dominio": "Productividad",
        "division": "project-management + product",
        "emoji": "📊",
        "especialidades": ["product-manager", "sprint-prioritizer", "project-shepherd", "experiment-tracker", "meeting-notes", "studio-ops", "studio-producer", "feedback-synthesizer", "trend-researcher"],
        "routing": "Product management, priorización, planificación de sprints, gestión de proyectos",
        "automatizable": False,
    },
    "AGENCY": {
        "dominio": "Comercial",
        "division": "marketing + sales + paid-media",
        "emoji": "📢",
        "especialidades": ["seo", "content-creator", "email-marketing", "social-media", "paid-media", "pr", "proposals", "sales-outbound", "lead-gen", "discovery-coach", "growth-hacker", "brand-strategy"],
        "routing": "Marketing, ventas, publicidad, propuestas, generación de leads, relaciones públicas",
        "automatizable": False,
    },
    "HELIOS": {
        "dominio": "Web/GIS",
        "division": "gis + spatial-computing",
        "emoji": "🌍",
        "especialidades": ["web-gis", "gis-analyst", "spatial-data", "cartography", "geoai-ml", "spatial-computing", "drone-mapping", "3d-scene", "bim-gis"],
        "routing": "Sistemas de información geográfica, mapas, web espacial, realidad extendida",
        "automatizable": False,
    },
    "CRONUS": {
        "dominio": "Game Dev",
        "division": "game-development",
        "emoji": "🎮",
        "especialidades": ["game-design", "level-design", "narrative-design", "economy-design", "game-audio", "technical-artist"],
        "routing": "Diseño de juegos, mecánicas, niveles, narrativa de juegos",
        "automatizable": False,
    },
    "MNEMOS": {
        "dominio": "Memoria/Salud",
        "division": "healthcare + specialized",
        "emoji": "🧠",
        "especialidades": ["clinical-evidence", "healthcare-innovation", "sovereign-health", "customer-support", "hr-onboarding", "legal-document", "operations", "change-management", "business-strategy"],
        "routing": "Salud, memoria organizacional, soporte, operaciones, legal, recursos humanos",
        "automatizable": False,
    },
    "PROPHET": {
        "dominio": "IA/ML",
        "division": "cross → usa NEXUS",
        "emoji": "🤖",
        "especialidades": ["ml-engineering", "model-training", "data-science", "fine-tuning", "rlhf", "evaluation", "mcp-builder"],
        "routing": "Machine learning, entrenamiento de modelos, evaluación, fine-tuning",
        "automatizable": True,
    },
    "ECHO": {
        "dominio": "Comunicación",
        "division": "cross → usa AGENCY",
        "emoji": "📡",
        "especialidades": ["copywriting", "translation", "community-management", "developer-advocacy", "technical-writing", "documentation"],
        "routing": "Comunicación escrita, traducción, community management, developer relations",
        "automatizable": False,
    },
    "DOMUS": {
        "dominio": "Hogar Inteligente",
        "division": "cross → usa MNEMOS",
        "emoji": "🏠",
        "especialidades": ["home-automation", "energy-management", "security-systems"],
        "routing": "Domótica, automatización del hogar, gestión energética",
        "automatizable": True,
    },
    "SANUS": {
        "dominio": "Salud Personal",
        "division": "cross → usa MNEMOS",
        "emoji": "🏥",
        "especialidades": ["fitness", "nutrition", "mental-health", "aging-care"],
        "routing": "Salud personal, fitness, nutrición, bienestar",
        "automatizable": False,
    },
    "FORTIS": {
        "dominio": "Pagos",
        "division": "cross → usa AURUM",
        "emoji": "💳",
        "especialidades": ["payment-processing", "billing", "subscription", "crypto-payments", "treasury"],
        "routing": "Procesamiento de pagos, suscripciones, tesorería",
        "automatizable": False,
    },
    "CHAIN": {
        "dominio": "Blockchain",
        "division": "cross → usa NEXUS",
        "emoji": "⛓️",
        "especialidades": ["smart-contracts", "defi", "tokenization", "web3-integration", "nft", "crypto-trading"],
        "routing": "Desarrollo blockchain, DeFi, smart contracts, Web3",
        "automatizable": False,
    },
    "PERSONA": {
        "dominio": "Personalización",
        "division": "cross → usa ARCAN",
        "emoji": "👤",
        "especialidades": ["user-personas", "journey-mapping", "behavioral-design", "cRO"],
        "routing": "Personalización, experiencia de usuario, optimización de conversión",
        "automatizable": False,
    },
    "APPLE": {
        "dominio": "Ecosistema Apple",
        "division": "cross → usa NEXUS",
        "emoji": "🍎",
        "especialidades": ["ios-dev", "macos-dev", "visionos", "swift", "swiftui", "metal"],
        "routing": "Desarrollo iOS/macOS/visionOS, Apple frameworks",
        "automatizable": False,
    },
    "INFRA": {
        "dominio": "Infraestructura",
        "division": "cross → usa NEXUS",
        "emoji": "🏗️",
        "especialidades": ["cloud-ops", "networking", "monitoring", "disaster-recovery", "cost-optimization"],
        "routing": "Infraestructura cloud, redes, monitoreo, DR",
        "automatizable": True,
    },
    "LAB": {
        "dominio": "Experimentos",
        "division": "cross → usa NEXUS",
        "emoji": "🧪",
        "especialidades": ["ab-testing", "prototyping", "hypothesis-validation", "data-analysis"],
        "routing": "Experimentos, testing A/B, prototipado rápido",
        "automatizable": True,
    },
    "LIBRARY": {
        "dominio": "Documentación",
        "division": "cross → usa ORION",
        "emoji": "📚",
        "especialidades": ["api-docs", "tutorials", "knowledge-base", "changelog"],
        "routing": "Documentación técnica, guías, bases de conocimiento",
        "automatizable": True,
    },
    "PHOENIX": {
        "dominio": "Delegación",
        "division": "cross → orquesta todos",
        "emoji": "🔄",
        "especialidades": ["orchestration", "routing", "escalation", "load-balancing"],
        "routing": "Orquestación central, delegación entre agentes",
        "automatizable": True,
    },
    "CONFIG": {
        "dominio": "Configuración",
        "division": "cross → usa NEXUS",
        "emoji": "⚙️",
        "especialidades": ["settings", "env-management", "feature-flags", "secrets"],
        "routing": "Configuración de sistemas, variables de entorno, secretos",
        "automatizable": True,
    },
    "EVENT": {
        "dominio": "Webhooks",
        "division": "cross → usa INFRA",
        "emoji": "🔗",
        "especialidades": ["webhook-management", "event-driven", "streaming", "pubsub"],
        "routing": "Webhooks, arquitectura event-driven, streaming",
        "automatizable": True,
    },
    "BOT": {
        "dominio": "Bots",
        "division": "cross → usa AGENCY",
        "emoji": "🤖",
        "especialidades": ["chatbot", "automation-bot", "notification-bot", "moderation-bot"],
        "routing": "Bots de chat, automatización, moderación",
        "automatizable": True,
    },
    "GEO": {
        "dominio": "Geoespacial",
        "division": "cross → usa HELIOS",
        "emoji": "📍",
        "especialidades": ["geo-coding", "route-optimization", "spatial-analysis"],
        "routing": "Geocodificación, optimización de rutas, análisis espacial",
        "automatizable": False,
    },
    "SYNC": {
        "dominio": "Sincronización",
        "division": "cross → usa INFRA",
        "emoji": "🔄",
        "especialidades": ["data-sync", "realtime-sync", "conflict-resolution"],
        "routing": "Sincronización de datos, resolución de conflictos",
        "automatizable": True,
    },
    "MATH": {
        "dominio": "Matemáticas",
        "division": "cross → usa NEXUS",
        "emoji": "📐",
        "especialidades": ["algebra", "calculus", "statistics", "optimization"],
        "routing": "Cálculos matemáticos, optimización, estadística avanzada",
        "automatizable": True,
    },
    "DECIDE": {
        "dominio": "Decisiones",
        "division": "cross → usa ORION",
        "emoji": "🎯",
        "especialidades": ["decision-matrix", "cost-benefit", "risk-assessment", "prioritization"],
        "routing": "Frameworks de decisión, análisis costo-beneficio",
        "automatizable": False,
    },
    "DIVINER": {
        "dominio": "Monitoreo",
        "division": "cross → usa SENTINEL",
        "emoji": "👁️",
        "especialidades": ["uptime-monitoring", "alerting", "log-analysis", "anomaly-detection"],
        "routing": "Monitoreo de sistemas, alertas, detección de anomalías",
        "automatizable": True,
    },
    "SHERLOCK": {
        "dominio": "Identidad",
        "division": "cross → usa SENTINEL",
        "emoji": "🔍",
        "especialidades": ["identity-verification", "osint", "fraud-detection", "background-check"],
        "routing": "Verificación de identidad, OSINT, detección de fraude",
        "automatizable": False,
    },
    "CLEANER": {
        "dominio": "Limpieza",
        "division": "cross → usa INFRA",
        "emoji": "🧹",
        "especialidades": ["data-cleaning", "log-rotation", "cache-clearing", "deduplication"],
        "routing": "Limpieza de datos, rotación de logs, deduplicación",
        "automatizable": True,
    },
    "LAUNCH": {
        "dominio": "Lanzamientos",
        "division": "cross → usa AGENCY",
        "emoji": "🚀",
        "especialidades": ["product-launch", "go-to-market", "release-management", "feature-announcement"],
        "routing": "Lanzamientos de producto, Go-To-Market, releases",
        "automatizable": False,
    },
    "ACADEMY": {
        "dominio": "Educación",
        "division": "cross → usa ORION",
        "emoji": "🎓",
        "especialidades": ["curriculum-design", "learning-paths", "assessment", "certification"],
        "routing": "Diseño curricular, rutas de aprendizaje, evaluación",
        "automatizable": False,
    },
    "TREASURE": {
        "dominio": "Criptoactivos",
        "division": "cross → usa CHAIN",
        "emoji": "🏦",
        "especialidades": ["portfolio-management", "defi-yield", "token-analytics", "nft-valuation"],
        "routing": "Gestión de portafolio cripto, yield farming, análisis de tokens",
        "automatizable": False,
    },
    "ARCHITECT": {
        "dominio": "Arquitectura",
        "division": "cross → usa NEXUS",
        "emoji": "🏛️",
        "especialidades": ["system-design", "microservices", "event-sourcing", "ddd", "patterns"],
        "routing": "Arquitectura de sistemas, microservicios, DDD",
        "automatizable": False,
    },
    "SONUS": {
        "dominio": "Música",
        "division": "cross → usa ARCAN",
        "emoji": "🎵",
        "especialidades": ["composition", "sound-design", "music-theory", "audio-production"],
        "routing": "Composición musical, diseño de sonido, producción audio",
        "automatizable": False,
    },
    "VISIO": {
        "dominio": "Visual",
        "division": "cross → usa ARCAN",
        "emoji": "🎬",
        "especialidades": ["video-editing", "animation", "motion-graphics", "color-grading"],
        "routing": "Edición de video, animación, motion graphics",
        "automatizable": False,
    },
    "DATA": {
        "dominio": "Datos",
        "division": "cross → usa NEXUS",
        "emoji": "🗄️",
        "especialidades": ["etl", "data-warehousing", "data-catalog", "lineage", "quality"],
        "routing": "Pipelines de datos, data warehousing, catálogos, linaje",
        "automatizable": True,
    },
    "QUANTUM": {
        "dominio": "Rendimiento",
        "division": "cross → usa NEXUS",
        "emoji": "⚡",
        "especialidades": ["profiling", "optimization", "caching", "load-testing", "scaling"],
        "routing": "Optimización de rendimiento, profiling, caching, escalado",
        "automatizable": True,
    },
    "BIO": {
        "dominio": "Biotecnología",
        "division": "cross → usa MNEMOS",
        "emoji": "🧬",
        "especialidades": ["genomics", "protein-folding", "clinical-trials", "bioinformatics"],
        "routing": "Bioinformática, genómica, ensayos clínicos",
        "automatizable": False,
    },
    "LOCALIZATION": {
        "dominio": "Idiomas",
        "division": "cross → usa ORION",
        "emoji": "🌐",
        "especialidades": ["translation", "i18n", "l10n", "cultural-adaptation"],
        "routing": "Traducción, internacionalización, adaptación cultural",
        "automatizable": True,
    },
    "LEGACY": {
        "dominio": "Migración",
        "division": "cross → usa NEXUS",
        "emoji": "📦",
        "especialidades": ["data-migration", "system-migration", "upgrade-path", "compatibility"],
        "routing": "Migración de sistemas, datos, upgrades",
        "automatizable": True,
    },
    "SHOW": {
        "dominio": "Presentaciones",
        "division": "cross → usa ARCAN",
        "emoji": "🎤",
        "especialidades": ["slide-design", "storytelling", "public-speaking", "pitch-decks"],
        "routing": "Presentaciones, pitch decks, storytelling",
        "automatizable": False,
    },
    "VAULT": {
        "dominio": "Almacenamiento",
        "division": "cross → usa INFRA",
        "emoji": "🗃️",
        "especialidades": ["object-storage", "block-storage", "backup", "archival"],
        "routing": "Almacenamiento cloud, backups, archivado",
        "automatizable": True,
    },
    "WEBHOOK": {
        "dominio": "Integraciones",
        "division": "cross → usa INFRA",
        "emoji": "🔌",
        "especialidades": ["api-integration", "webhook-management", "event-driven", "middleware"],
        "routing": "Integración de APIs, webhooks, middleware",
        "automatizable": True,
    },
    "ROLEPLAY": {
        "dominio": "Simulación",
        "division": "cross → usa todos",
        "emoji": "🎭",
        "especialidades": ["scenario-modeling", "war-gaming", "red-teaming", "tabletop"],
        "routing": "Simulación de escenarios, red teaming, war gaming",
        "automatizable": False,
    },
    "ASSEMBLER": {
        "dominio": "Orquestador",
        "division": "cross → orquesta todos",
        "emoji": "🧩",
        "especialidades": ["task-decomposition", "dependency-graph", "parallel-execution", "recovery"],
        "routing": "Descomposición de tareas, ejecución paralela, recuperación",
        "automatizable": True,
    },
    "METRIX": {
        "dominio": "Analytics",
        "division": "cross → usa ORION",
        "emoji": "📈",
        "especialidades": ["metrics-dashboard", "kpi-tracking", "attribution", "funnel-analysis"],
        "routing": "Dashboards, KPIs, atribución, análisis de embudo",
        "automatizable": True,
    },
    "CLOUD": {
        "dominio": "Cloud Computing",
        "division": "cross → usa INFRA",
        "emoji": "☁️",
        "especialidades": ["multi-cloud", "serverless", "containers", "kubernetes", "cost-optimization"],
        "routing": "Multi-cloud, serverless, Kubernetes, optimización de costos",
        "automatizable": True,
    },
    "PAY": {
        "dominio": "Pagos",
        "division": "cross → usa FORTIS",
        "emoji": "💸",
        "especialidades": ["checkout", "subscription", "invoicing", "payment-links"],
        "routing": "Checkout, suscripciones, facturación, links de pago",
        "automatizable": True,
    },
    "MEDIA": {
        "dominio": "Media",
        "division": "cross → usa ARCAN",
        "emoji": "🎞️",
        "especialidades": ["image-processing", "video-transcoding", "cdn", "media-optimization"],
        "routing": "Procesamiento de imágenes, video, CDN",
        "automatizable": True,
    },
    "TRADE": {
        "dominio": "Trading",
        "division": "cross → usa AURUM",
        "emoji": "📉",
        "especialidades": ["technical-analysis", "risk-management", "portfolio-rebalance", "algorithmic-trading"],
        "routing": "Análisis técnico, gestión de riesgo, trading algorítmico",
        "automatizable": False,
    },
    "SEARCH": {
        "dominio": "Búsqueda",
        "division": "cross → usa ORION",
        "emoji": "🔎",
        "especialidades": ["full-text-search", "semantic-search", "ranking", "indexing"],
        "routing": "Búsqueda full-text, semántica, ranking, indexación",
        "automatizable": True,
    },
    "COMMS": {
        "dominio": "Comunicación",
        "division": "cross → usa ECHO",
        "emoji": "💬",
        "especialidades": ["internal-comms", "press-release", "crisis-comms", "stakeholder-updates"],
        "routing": "Comunicados de prensa, crisis, stakeholders",
        "automatizable": False,
    },
    "DB": {
        "dominio": "Bases de Datos",
        "division": "cross → usa NEXUS",
        "emoji": "🗃️",
        "especialidades": ["sql", "nosql", "graph-db", "time-series", "replication"],
        "routing": "SQL, NoSQL, grafos, time-series, replicación",
        "automatizable": True,
    },
    "MONITOR": {
        "dominio": "Monitoreo Avanzado",
        "division": "cross → usa DIVINER",
        "emoji": "📊",
        "especialidades": ["distributed-tracing", "metrics-collection", "slo-tracking", "incident-response"],
        "routing": "Distributed tracing, métricas, SLOs, respuesta a incidentes",
        "automatizable": True,
    },
    "CRM": {
        "dominio": "CRM",
        "division": "cross → usa AGENCY",
        "emoji": "👥",
        "especialidades": ["lead-scoring", "pipeline-management", "contact-enrichment", "sales-automation"],
        "routing": "Lead scoring, pipeline, enriquecimiento de contactos",
        "automatizable": True,
    },
    "LEARN": {
        "dominio": "Aprendizaje",
        "division": "cross → usa ACADEMY",
        "emoji": "📖",
        "especialidades": ["skill-assessment", "adaptive-learning", "knowledge-retention", "microlearning"],
        "routing": "Evaluación de habilidades, aprendizaje adaptativo, retención",
        "automatizable": False,
    },
    "TRAVEL": {
        "dominio": "Viajes",
        "division": "cross → usa ORION",
        "emoji": "✈️",
        "especialidades": ["itinerary-planning", "booking", "travel-insurance", "visa-assistance"],
        "routing": "Planificación de viajes, reservas, asistencia visa",
        "automatizable": False,
    },
    "LIFESTYLE": {
        "dominio": "Estilo de Vida",
        "division": "cross → usa MNEMOS",
        "emoji": "🌿",
        "especialidades": ["wellness", "productivity-habits", "minimalism", "work-life-balance"],
        "routing": "Bienestar, hábitos, minimalismo, balance vida-trabajo",
        "automatizable": False,
    },
    "SECURITY_OPS": {
        "dominio": "Seguridad Operativa",
        "division": "cross → usa SENTINEL",
        "emoji": "🔒",
        "especialidades": ["soc", "siem", "threat-hunting", "forensics"],
        "routing": "SOC, SIEM, threat hunting, forenses digitales",
        "automatizable": False,
    },
    "OPEN-GEN": {
        "dominio": "Generación Abierta",
        "division": "cross → usa todos",
        "emoji": "🌊",
        "especialidades": ["creative-generation", "multi-modal", "brainstorming", "innovation"],
        "routing": "Generación creativa, multi-modal, brainstorming, innovación",
        "automatizable": False,
    },
    "GAMER": {
        "dominio": "Videojuegos",
        "division": "cross → usa CRONUS",
        "emoji": "🕹️",
        "especialidades": ["game-modding", "speedrunning", "esports", "game-streaming"],
        "routing": "Modding, speedrun, esports, streaming de juegos",
        "automatizable": False,
    },
    "CHIEF": {
        "dominio": "Coordinación Ejecutiva",
        "division": "cross → orquesta todos",
        "emoji": "👔",
        "especialidades": ["executive-summary", "decision-support", "stakeholder-alignment", "resource-allocation"],
        "routing": "Resumen ejecutivo, soporte a decisiones, alineación de stakeholders",
        "automatizable": False,
    },
}

# ============================================================================
# AGENTES ESPECIALIZADOS — Nodos Hoja (85 agentes)
# ============================================================================

AGENTES_ESPECIALIZADOS = {
    # ARCAN — Creatividad
    "design-brand-guardian": {"maestro": "ARCAN", "capacidades": ["identidad-marca", "guía-estilo", "consistencia"]},
    "design-ui-designer": {"maestro": "ARCAN", "capacidades": ["interfaces", "componentes", "design-systems"]},
    "design-ux-architect": {"maestro": "ARCAN", "capacidades": ["arquitectura-ux", "css-systems"]},
    "design-ux-researcher": {"maestro": "ARCAN", "capacidades": ["user-testing", "behavior-analysis"]},
    "design-image-prompt-engineer": {"maestro": "ARCAN", "capacidades": ["prompts-imagen", "ai-generation"]},
    "design-visual-storyteller": {"maestro": "ARCAN", "capacidades": ["narrativa-visual", "multimedia"]},
    "design-whimsy-injector": {"maestro": "ARCAN", "capacidades": ["personalidad", "delight"]},
    "design-inclusive-visuals-specialist": {"maestro": "ARCAN", "capacidades": ["representación", "diversidad"]},
    "design-persona-walkthrough": {"maestro": "ARCAN", "capacidades": ["cognitive-walkthrough", "cRO"]},
    "design-ui-finish-gate-reviewer": {"maestro": "ARCAN", "capacidades": ["ui-review", "quality-gate"]},
    # NEXUS — Desarrollo
    "engineering-frontend-developer": {"maestro": "NEXUS", "capacidades": ["react", "vue", "typescript", "performance"]},
    "engineering-backend-architect": {"maestro": "NEXUS", "capacidades": ["scalable-systems", "databases", "apis"]},
    "engineering-mobile-app-builder": {"maestro": "NEXUS", "capacidades": ["ios", "android", "cross-platform"]},
    "engineering-devops-automator": {"maestro": "NEXUS", "capcidades": ["cicd", "cloud-ops", "infrastructure"]},  # TYPO FIXED below
    "engineering-database-optimizer": {"maestro": "NEXUS", "capacidades": ["schema-design", "query-optimization"]},
    "engineering-ai-engineer": {"maestro": "NEXUS", "capacidades": ["ml-models", "deployment", "llm-apps"]},
    "engineering-data-engineer": {"maestro": "NEXUS", "capacidades": ["data-pipelines", "lakehouse", "spark"]},
    "engineering-code-reviewer": {"maestro": "NEXUS", "capacidades": ["code-review", "correctness", "security"]},
    "engineering-software-architect": {"maestro": "NEXUS", "capacidades": ["system-design", "ddd", "patterns"]},
    "engineering-sre": {"maestro": "NEXUS", "capacidades": ["slos", "error-budgets", "observability"]},
    "engineering-prompt-engineer": {"maestro": "NEXUS", "capacidades": ["prompt-design", "optimization"]},
    "engineering-rag-pipeline-engineer": {"maestro": "NEXUS", "capacidades": ["chunking", "retrieval", "hybrid-search"]},
    "engineering-llm-post-training-engineer": {"maestro": "NEXUS", "capacidades": ["sft", "dpo", "rlhf", "grpo"]},
    "engineering-multi-agent-systems-architect": {"maestro": "NEXUS", "capacidades": ["agent-topology", "context-management", "trust"]},
    "engineering-rapid-prototyper": {"maestro": "NEXUS", "capacidades": ["mvp", "proof-of-concept"]},
    "engineering-privacy-engineer": {"maestro": "NEXUS", "capacidades": ["pii-discovery", "data-minimization", "dsar"]},  # TYPO FIXED
    # AGENCY — Comercial
    "marketing-seo-specialist": {"maestro": "AGENCY", "capacidades": ["technical-seo", "content-optimization"]},
    "marketing-content-creator": {"maestro": "AGENCY", "capacidades": ["editorial-calendar", "copywriting"]},
    "marketing-email-marketing-strategist": {"maestro": "AGENCY", "capacidades": ["crm-campaigns", "lifecycle-automation"]},
    "marketing-social-media-strategist": {"maestro": "AGENCY", "capacidades": ["linkedin", "twitter", "thought-leadership"]},
    "marketing-growth-hacker": {"maestro": "AGENCY", "capacidades": ["user-acquisition", "viral-loops"]},
    "sales-proposal-strategist": {"maestro": "AGENCY", "capacidades": ["proposals", "rfp-response", "deal-strategy"]},
    "sales-discovery-coach": {"maestro": "AGENCY", "capacidades": ["needs-analysis", "stakeholder-mapping", "pain-points"]},
    "sales-outbound-specialist": {"maestro": "AGENCY", "capacidades": ["cold-outreach", "sequences", "personalization"]},
    "paid-media-ppc-strategist": {"maestro": "AGENCY", "capacidades": ["google-ads", "meta-ads", "linkedin-ads"]},
    "paid-media-tracking-specialist": {"maestro": "AGENCY", "capacidades": ["attribution", "gtm", "conversion-tracking"]},
    # ORION — Investigación
    "research-literature-reviewer": {"maestro": "ORION", "capacidades": ["systematic-review", "meta-analysis", "citation-tracking"]},
    "research-data-analyst": {"maestro": "ORION", "capacidades": ["statistical-analysis", "visualization", "hypothesis-testing"]},
    "research-academic-writer": {"maestro": "ORION", "capacidades": ["paper-structure", "peer-review", "academic-style"]},
    "research-trend-analyst": {"maestro": "ORION", "capacidades": ["market-trends", "emerging-tech", "competitive-intel"]},
    "research-biostatistician": {"maestro": "ORION", "capacidades": ["clinical-trials", "survival-analysis", "regression"]},
    "research-geographer": {"maestro": "ORION", "capacidades": ["spatial-analysis", "cartography", "remote-sensing"]},
    "research-psychologist": {"maestro": "ORION", "capacidades": ["behavioral-studies", "survey-design", "cognitive-models"]},
    "research-historian": {"maestro": "ORION", "capacidades": ["historical-analysis", "primary-sources", "timeline-reconstruction"]},
    # AURUM — Finanzas
    "finance-modeler": {"maestro": "AURUM", "capacidades": ["financial-modeling", "forecasting", "scenario-analysis"]},
    "finance-fpna-analyst": {"maestro": "AURUM", "capacidades": ["budgeting", "variance-analysis", "management-reporting"]},
    "finance-bookkeeper": {"maestro": "AURUM", "capacidades": ["double-entry", "reconciliation", "chart-of-accounts"]},
    "finance-tax-advisor": {"maestro": "AURUM", "capacidades": ["tax-planning", "compliance", "transfer-pricing"]},
    "finance-investment-analyst": {"maestro": "AURUM", "capacidades": ["valuation", "due-diligence", "market-research"]},
    "finance-pricing-strategist": {"maestro": "AURUM", "capacidades": ["pricing-models", "elasticity", "revenue-optimization"]},
    "finance-lbo-analyst": {"maestro": "AURUM", "capacidades": ["leverage-models", "debt-scenarios", "irr-analysis"]},
    "finance-dcf-analyst": {"maestro": "AURUM", "capacidades": ["dcf-valuation", "wacc", "terminal-value"]},
    "finance-merger-analyst": {"maestro": "AURUM", "capacidades": ["merger-models", "accretion-dilution", "synergies"]},
    "finance-comps-analyst": {"maestro": "AURUM", "capacidades": ["comparable-companies", "precedent-transactions", "multiples"]},
    # SENTINEL — Seguridad
    "security-pentester": {"maestro": "SENTINEL", "capacidades": ["penetration-testing", "vulnerability-assessment", "exploit-dev"]},
    "security-appsec-engineer": {"maestro": "SENTINEL", "capacidades": ["owasp", "sast", "dast", "dependency-scanning"]},
    "security-compliance-auditor": {"maestro": "SENTINEL", "capacidades": ["soc2", "iso27001", "gdpr", "hipaa"]},
    "security-threat-intel-analyst": {"maestro": "SENTINEL", "capacidades": ["threat-landscape", "ioc-analysis", "dark-web-monitoring"]},
    "security-incident-responder": {"maestro": "SENTINEL", "capacidades": ["incident-handling", "forensics", "malware-analysis"]},
    "security-blockchain-security": {"maestro": "SENTINEL", "capacidades": ["smart-contract-audit", "defi-security", "rug-pull-detection"]},
    "security-secrets-hygiene": {"maestro": "SENTINEL", "capacidades": ["secret-scanning", "vault-management", "rotation-policies"]},
    "security-cloud-security": {"maestro": "SENTINEL", "capacidades": ["cloud-config-audit", "iam-review", "network-security"]},
    "security-code-reviewer": {"maestro": "SENTINEL", "capacidades": ["secure-code-review", "threat-modeling", "architecture-review"]},
    # MERIDIAN — Productividad
    "product-manager": {"maestro": "MERIDIAN", "capacidades": ["roadmap", "user-stories", "prioritization", "okrs"]},
    "sprint-prioritizer": {"maestro": "MERIDIAN", "capacidades": ["sprint-planning", "backlog-grooming", "estimation"]},
    "project-shepherd": {"maestro": "MERIDIAN", "capacidades": ["project-tracking", "risk-management", "stakeholder-updates"]},
    "experiment-tracker": {"maestro": "MERIDIAN", "capcidades": ["ab-test-design", "statistical-significance", "feature-flags"]},
    "meeting-notes-specialist": {"maestro": "MERIDIAN", "capacidades": ["meeting-summaries", "action-items", "decision-tracking"]},
    "studio-ops-manager": {"maestro": "MERIDIAN", "capacidades": ["resource-allocation", "capacity-planning", "vendor-management"]},
    "studio-producer": {"maestro": "MERIDIAN", "capacidades": ["production-timelines", "milestone-tracking", "cross-team-coordination"]},
    "feedback-synthesizer": {"maestro": "MERIDIAN", "capacidades": ["user-feedback-analysis", "sentiment-analysis", "insight-extraction"]},
    "trend-researcher": {"maestro": "MERIDIAN", "capacidades": ["industry-trends", "emerging-tools", "competitive-analysis"]},
    # HELIOS — Web/GIS
    "web-gis-developer": {"maestro": "HELIOS", "capacidades": ["web-mapping", "geospatial-apis", "spatial-databases"]},
    "gis-analyst": {"maestro": "HELIOS", "capacidades": ["spatial-analysis", "geoprocessing", "terrain-modeling"]},
    "spatial-data-engineer": {"maestro": "HELIOS", "capacidades": ["spatial-etl", "tile-services", "coordinate-systems"]},
    "cartographer": {"maestro": "HELIOS", "capacidades": ["map-design", "symbology", "print-maps"]},
    "geoai-ml-engineer": {"maestro": "HELIOS", "capacidades": ["geospatial-ml", "satellite-imagery", "location-intelligence"]},
    "spatial-computing-engineer": {"maestro": "HELIOS", "capacidades": ["point-clouds", "3d-tiles", "digital-twins"]},
    "drone-mapping-specialist": {"maestro": "HELIOS", "capacidades": ["uav-mapping", "photogrammetry", "orthomosaic"]},
    "scene-3d-creator": {"maestro": "HELIOS", "capacidades": ["3d-scenes", "web-3d", "augmented-reality"]},
    "bim-gis-integrator": {"maestro": "HELIOS", "capacidades": ["bim-models", "gis-integration", "digital-twin"]},
    # CRONUS — Game Dev
    "game-designer": {"maestro": "CRONUS", "capacidades": ["game-mechanics", "balance", "systems-design"]},
    "level-designer": {"maestro": "CRONUS", "capacidades": ["level-layout", "flow-design", "pacing"]},
    "narrative-designer": {"maestro": "CRONUS", "capacidades": ["story-scripts", "branching-narratives", "dialogue-trees"]},
    "economy-designer": {"maestro": "CRONUS", "capacidades": ["virtual-economies", "monetization", "reward-loops"]},
    "game-audio-designer": {"maestro": "CRONUS", "capacidades": ["sound-effects", "adaptive-music", "audio-implementation"]},
    "technical-artist": {"maestro": "CRONUS", "capacidades": ["shaders", "vfx", "pipeline-tools"]},
    # MNEMOS — Memoria/Salud
    "clinical-evidence-reviewer": {"maestro": "MNEMOS", "capacidades": ["clinical-trials", "evidence-synthesis", "medical-literature"]},
    "healthcare-innovator": {"maestro": "MNEMOS", "capacidades": ["health-tech", "patient-experience", "care-models"]},
    "sovereign-health-advisor": {"maestro": "MNEMOS", "capacidades": ["personalized-medicine", "longevity", "biomarkers"]},
    "customer-support-specialist": {"maestro": "MNEMOS", "capacidades": ["ticket-resolution", "knowledge-base", "escalation"]},
    "hr-onboarding-specialist": {"maestro": "MNEMOS", "capacidades": ["onboarding-flows", "policy-training", "culture-integration"]},
    "legal-document-analyst": {"maestro": "MNEMOS", "capacidades": ["contract-review", "compliance-docs", "legal-research"]},
    "operations-optimizer": {"maestro": "MNEMOS", "capacidades": ["process-improvement", "sop-creation", "efficiency-analysis"]},
    "change-management-specialist": {"maestro": "MNEMOS", "capacidades": ["change-strategy", "stakeholder-engagement", "adoption-metrics"]},
    "business-strategist": {"maestro": "MNEMOS", "capacidades": ["strategic-planning", "market-entry", "competitive-positioning"]},
}

# Fix typos in dictionary
AGENTES_ESPECIALIZADOS["engineering-devops-automator"]["capacidades"] = ["cicd", "cloud-ops", "infrastructure"]
AGENTES_ESPECIALIZADOS["experiment-tracker"]["capacidades"] = ["ab-test-design", "statistical-significance", "feature-flags"]


# ============================================================================
# ORQUESTADOR — Motor de Routing + Delegación
# ============================================================================

class Orquestador:
    """Routing inteligente de tareas a agentes maestros/especializados."""

    def __init__(self):
        self.routing_map = {
            "design": ["diseño", "ui", "ux", "marca", "visual", "css", "estilo", "branding", "ilustración"],
            "engineering": ["código", "programar", "app", "web", "api", "base de datos", "software", "devops"],
            "research": ["investigar", "estudio", "paper", "académico", "científico", "literature"],
            "finance": ["finanzas", "inversión", "presupuesto", "contabilidad", "impuestos", "valuation"],
            "security": ["seguridad", "pentest", "vulnerabilidad", "auditoría", "brecha", "compliance"],
            "marketing": ["marketing", "seo", "contenido", "redes", "campaña", "publicidad", "ads"],
            "sales": ["venta", "propuesta", "cliente", "prospecto", "lead", "outbound"],
            "product": ["producto", "roadmap", "feature", "priorización", "sprint"],
            "game": ["juego", "game", "minecraft", "pokemon", "videojuego", "gamedev"],
            "health": ["salud", "médico", "bienestar", "fitness", "nutrición", "clínico"],
            "memory": ["memoria", "conocimiento", "lección", "aprendizaje"],
            "creativity": ["creatividad", "arte", "diseño", "branding", "visual", "storytelling"],
            "commercial": ["comercial", "ventas", "marketing", "propuestas", "leads"],
            "web": ["web", "gis", "mapas", "espacial", "geoespacial"],
        }

    def determinar_maestro(self, tarea: str) -> dict:
        """Determina el maestro óptimo para una tarea."""
        tarea_lower = tarea.lower()
        scores = {}

        for maestro_id, info in AGENTES_MAESTROS.items():
            score = 0
            # Match por nombre de maestro
            if maestro_id.lower() in tarea_lower:
                score += 50
            # Match por dominio
            if info["dominio"].lower() in tarea_lower:
                score += 40
            # Match por especialidades
            for esp in info.get("especialidades", []):
                if esp.lower().replace("-", " ") in tarea_lower:
                    score += 25
            # Match por routing keywords
            for keyword in self.routing_map.get(info["division"].split(" → ")[0].split(" + ")[0], []):
                if keyword in tarea_lower:
                    score += 15
            # Match por routing text
            if any(kw in tarea_lower for kw in info.get("routing", "").lower().split(", ")[:3]):
                score += 10

            if score > 0:
                scores[maestro_id] = score

        if not scores:
            return {"maestro": "PHOENIX", "confianza": 0, "motivo": "Sin match → orquestador"}

        best_maestro = max(scores, key=scores.get)
        return {
            "maestro": best_maestro,
            "confianza": min(scores[best_maestro], 100),
            "motivo": f"Match scoring: {scores[best_maestro]} pts"
        }

    def determinar_especialista(self, tarea: str, maestro: str = None) -> dict:
        """Encuentra el mejor especialista para una tarea."""
        tarea_lower = tarea.lower()
        best_match = None
        best_score = 0

        for agent_id, info in AGENTES_ESPECIALIZADOS.items():
            if maestro and info["maestro"] != maestro:
                continue
            score = 0
            # Match por capacidades
            for cap in info.get("capacidades", []):
                if cap.lower().replace("-", " ") in tarea_lower:
                    score += 30
            # Match por nombre
            if agent_id.lower().replace("-", " ") in tarea_lower:
                score += 20
            # Bonus si el maestro coincide
            if info["maestro"] == maestro:
                score += 10

            if score > best_score:
                best_score = score
                best_match = {
                    "especialista": agent_id,
                    "maestro": info["maestro"],
                    "confianza": min(score, 100),
                    "capacidades": info.get("capacidades", [])
                }

        return best_match or {"especialista": None, "maestro": maestro or "PHOENIX", "confianza": 0, "capacidades": []}

    def ruta_completa(self, tarea: str) -> dict:
        """Routing completo: maestro + especialista."""
        maestro_result = self.determinar_maestro(tarea)
        especialista_result = self.determinar_especialista(tarea, maestro_result["maestro"])
        return {
            "tarea": tarea,
            "maestro": maestro_result,
            "especialista": especialista_result,
            "automatizable": AGENTES_MAESTROS.get(maestro_result["maestro"], {}).get("automatizable", False)
        }


# ============================================================================
# DETECTOR DE TAREAS
# ============================================================================

class DetectorTareas:
    """Escanea el knowledge base en busca de tareas pendientes."""

    def __init__(self):
        self.sources = [
            (PROJECTS_DIR, "*.md", self._extract_md_tasks),
            (ACTIVE_DIR, "*/task_plan.md", self._extract_md_tasks),
        ]

    def _extract_md_tasks(self, filepath: Path) -> list:
        """Extrae tareas de un archivo markdown."""
        tasks = []
        try:
            content = filepath.read_text(encoding="utf-8")
            for line in content.split("\n"):
                line = line.strip()
                # Extraer checkboxes sin marcar
                if line.startswith("- [ ]") or line.startswith("- [x]"):
                    task_text = line[5:].strip()
                    if task_text:
                        tasks.append({
                            "texto": task_text,
                            "fuente": str(filepath),
                            "tipo": "checkbox",
                            "completada": line.startswith("- [x]")
                        })
                # Extraer secciones pendiente
                elif line.startswith("## Pendiente") or line.startswith("## TODO"):
                    continue
                elif line.startswith("- ") and not line.startswith("- ["):
                    task_text = line[2:].strip()
                    if task_text and not task_text.startswith("#"):
                        tasks.append({
                            "texto": task_text,
                            "fuente": str(filepath),
                            "tipo": "bullet",
                            "completada": False
                        })
        except Exception:
            pass
        return tasks

    def scan_all(self) -> list:
        """Escanea todas las fuentes de tareas."""
        all_tasks = []
        for directory, pattern, extractor in self.sources:
            if directory.exists():
                for filepath in directory.glob(pattern):
                    all_tasks.extend(extractor(filepath))
        # También TODAY.md
        if TODAY_FILE.exists():
            all_tasks.extend(self._extract_md_tasks(TODAY_FILE))
        return all_tasks

    def get_stats(self) -> dict:
        """Estadísticas de tareas."""
        tasks = self.scan_all()
        completed = sum(1 for t in tasks if t.get("completada"))
        pending = len(tasks) - completed
        return {
            "total": len(tasks),
            "pendientes": pending,
            "completadas": completed,
            "fuentes_escaneadas": len(set(t["fuente"] for t in tasks))
        }


# ============================================================================
# AUTO-EXECUTOR
# ============================================================================

class AutoExecutor:
    """Ejecuta tareas mecánicas de forma segura."""

    # Comandos permitidos (whitelist)
    SAFE_COMMANDS = {
        "mkdir": ["mkdir", "-p"],
        "touch": ["touch"],
        "cp": ["cp", "-r"],
        "mv": ["mv"],
        "rm": ["rm", "-rf"],
        "git_commit": ["git", "commit", "-m"],
        "git_push": ["git", "push"],
        "git_pull": ["git", "pull"],
        "git_add": ["git", "add", "."],
        "pip_install": ["pip", "install"],
        "npm_install": ["npm", "install"],
        "create_md": None,  # Manejado específicamente
        "run_cmd": None,    # Requiere validación
    }

    # Patrones de tareas automatizables
    PATTERNS = {
        r"crear? carpeta (\S+)": "mkdir",
        r"crear? directorio (\S+)": "mkdir",
        r"crear? archivo (\S+)": "touch",
        r"crear? archivo md (\S+)": "create_md",
        r"copiar (\S+) (?:a|en) (\S+)": "cp",
        r"mover (\S+) (?:a|en) (\S+)": "mv",
        r"eliminar (?:archivo|carpeta) (\S+)": "rm",
        r"git commit (.+)": "git_commit",
        r"git push": "git_push",
        r"git pull": "git_pull",
        r"pip install (.+)": "pip_install",
        r"npm install (.+)": "npm_install",
        r"ejecutar (.+)": "run_cmd",
    }

    def __init__(self):
        self.history = []

    def detectar_tipo(self, tarea_texto: str) -> tuple:
        """Detecta si una tarea es automatizable y qué tipo."""
        texto_lower = tarea_texto.lower().strip()
        for pattern, action in self.PATTERNS.items():
            match = re.match(pattern, texto_lower)
            if match:
                return action, match.groups()
        return None, None

    def ejecutar(self, tarea_texto: str, dry_run: bool = False) -> dict:
        """Ejecuta una tarea mecánica."""
        action, params = self.detectar_tipo(tarea_texto)
        if not action:
            return {"status": "no_automatizable", "tarea": tarea_texto}

        result = {
            "tarea": tarea_texto,
            "accion": action,
            "dry_run": dry_run,
            "timestamp": datetime.now().isoformat()
        }

        if dry_run:
            result["status"] = "dry_run"
            result["comando"] = f"{action} {params}"
            return result

        try:
            if action == "mkdir":
                path = HOME / params[0]
                path.mkdir(parents=True, exist_ok=True)
                result["status"] = "success"
                result["mensaje"] = f"Carpeta creada: {path}"

            elif action == "touch":
                path = HOME / params[0]
                path.parent.mkdir(parents=True, exist_ok=True)
                path.touch(exist_ok=True)
                result["status"] = "success"
                result["mensaje"] = f"Archivo creado: {path}"

            elif action == "create_md":
                path = HOME / params[0]
                path.parent.mkdir(parents=True, exist_ok=True)
                if not path.exists():
                    path.write_text(f"# {path.stem}\n\n", encoding="utf-8")
                result["status"] = "success"
                result["mensaje"] = f"Archivo MD creado: {path}"

            elif action == "cp":
                src = HOME / params[0]
                dst = HOME / params[1]
                import shutil
                shutil.copy2(src, dst)
                result["status"] = "success"
                result["mensaje"] = f"Copiado: {src} → {dst}"

            elif action == "mv":
                src = HOME / params[0]
                dst = HOME / params[1]
                import shutil
                shutil.move(str(src), str(dst))
                result["status"] = "success"
                result["mensaje"] = f"Movido: {src} → {dst}"

            elif action == "rm":
                path = HOME / params[0]
                if path.exists():
                    if path.is_dir():
                        import shutil
                        shutil.rmtree(path)
                    else:
                        path.unlink()
                    result["status"] = "success"
                    result["mensaje"] = f"Eliminado: {path}"
                else:
                    result["status"] = "not_found"

            elif action == "git_commit":
                subprocess.run(["git", "add", "."], cwd=HOME, check=True, capture_output=True)
                subprocess.run(["git", "commit", "-m", params[0]], cwd=HOME, check=True, capture_output=True)
                result["status"] = "success"
                result["mensaje"] = f"Git commit: {params[0]}"

            elif action == "git_push":
                subprocess.run(["git", "push"], cwd=HOME, check=True, capture_output=True)
                result["status"] = "success"
                result["mensaje"] = "Git push exitoso"

            elif action == "git_pull":
                subprocess.run(["git", "pull"], cwd=HOME, check=True, capture_output=True)
                result["status"] = "success"
                result["mensaje"] = "Git pull exitoso"

            elif action == "pip_install":
                subprocess.run([sys.executable, "-m", "pip", "install"] + params[0].split(), check=True, capture_output=True)
                result["status"] = "success"
                result["mensaje"] = f"Pip install: {params[0]}"

            elif action == "npm_install":
                subprocess.run(["npm", "install"] + params[0].split(), cwd=HOME, check=True, capture_output=True)
                result["status"] = "success"
                result["mensaje"] = f"Npm install: {params[0]}"

            elif action == "run_cmd":
                # SECURITY: Solo permitir comandos específicos
                cmd = params[0] if params else ""
                allowed_prefixes = ("python", "node", "ls", "cat", "echo", "grep", "find")
                if not any(cmd.strip().startswith(p) for p in allowed_prefixes):
                    result["status"] = "denied"
                    result["mensaje"] = f"Comando no permitido: {cmd}"
                else:
                    subprocess.run(cmd, shell=True, check=True, capture_output=True, timeout=30)
                    result["status"] = "success"
                    result["mensaje"] = f"Ejecutado: {cmd}"

            else:
                result["status"] = "unknown_action"

        except subprocess.CalledProcessError as e:
            result["status"] = "error"
            result["error"] = str(e)
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)

        self.history.append(result)
        return result


# ============================================================================
# STATE MANAGER
# ============================================================================

class StateManager:
    """Persistencia de estado para no re-ejecutar tareas."""

    def __init__(self):
        self.state = self._load_state()

    def _load_state(self) -> dict:
        if STATE_FILE.exists():
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        return {"executed": [], "failed": []}

    def _save_state(self):
        STATE_FILE.write_text(json.dumps(self.state, indent=2, ensure_ascii=False), encoding="utf-8")

    def is_executed(self, task_hash: str) -> bool:
        return any(e.get("hash") == task_hash for e in self.state["executed"])

    def mark_executed(self, task_hash: str, result: dict):
        self.state["executed"].append({
            "hash": task_hash,
            "result": result,
            "executed_at": datetime.now().isoformat()
        })
        self._save_state()

    def mark_failed(self, task_hash: str, error: str):
        self.state["failed"].append({
            "hash": task_hash,
            "error": error,
            "failed_at": datetime.now().isoformat()
        })
        self._save_state()


# ============================================================================
# QUEUE MANAGER
# ============================================================================

class QueueManager:
    """Cola de tareas para agentes IA."""

    def __init__(self):
        self.queue = self._load_queue()

    def _load_queue(self) -> list:
        if QUEUE_FILE.exists():
            return json.loads(QUEUE_FILE.read_text(encoding="utf-8"))
        return []

    def _save_queue(self):
        QUEUE_FILE.write_text(json.dumps(self.queue, indent=2, ensure_ascii=False), encoding="utf-8")

    def enqueue(self, task: dict):
        task["enqueued_at"] = datetime.now().isoformat()
        task["status"] = "queued"
        self.queue.append(task)
        self._save_queue()

    def dequeue(self) -> Optional[dict]:
        for i, task in enumerate(self.queue):
            if task.get("status") == "queued":
                task["status"] = "processing"
                self._save_queue()
                return task
        return None

    def complete(self, task_id: str, result: str):
        for task in self.queue:
            if task.get("id") == task_id:
                task["status"] = "completed"
                task["result"] = result
                task["completed_at"] = datetime.now().isoformat()
                self._save_queue()
                break

    def get_queued(self) -> list:
        return [t for t in self.queue if t.get("status") == "queued"]


# ============================================================================
# MEMORY SYSTEM (Consolidado)
# ============================================================================

class MemorySystem:
    """Sistema de memoria neuronal: grafo + lecciones + contexto + tags."""

    def __init__(self):
        self.index = self._load_index()

    def _load_index(self) -> dict:
        if MEMORY_INDEX.exists():
            return json.loads(MEMORY_INDEX.read_text(encoding="utf-8"))
        return {
            "conexiones": [],
            "lecciones": [],
            "contexto": {},
            "tags": {}
        }

    def _save_index(self):
        MEMORY_INDEX.write_text(json.dumps(self.index, indent=2, ensure_ascii=False), encoding="utf-8")

    def conectar(self, concepto_a: str, concepto_b: str, relacion: str, fuerza: int = 5):
        conexion = {
            "a": concepto_a,
            "b": concepto_b,
            "relacion": relacion,
            "fuerza": max(1, min(10, fuerza)),
            "creada_en": datetime.now().isoformat()
        }
        # Evitar duplicados
        for c in self.index["conexiones"]:
            if c["a"] == concepto_a and c["b"] == concepto_b:
                c["fuerza"] = max(c["fuerza"], fuerza)
                self._save_index()
                return c
        self.index["conexiones"].append(conexion)
        self._save_index()
        return conexion

    def buscar_conexiones(self, concepto: str, min_fuerza: int = 1) -> list:
        resultados = []
        for c in self.index["conexiones"]:
            if c["a"] == concepto or c["b"] == concepto:
                if c["fuerza"] >= min_fuerza:
                    otro = c["b"] if c["a"] == concepto else c["a"]
                    resultados.append({
                        "concepto": otro,
                        "relacion": c["relacion"],
                        "fuerza": c["fuerza"]
                    })
        return sorted(resultados, key=lambda x: x["fuerza"], reverse=True)

    def agregar_leccion(self, agent_id: str, error: str, contexto: str, solucion: str, tags: list = None):
        leccion = {
            "agent_id": agent_id,
            "error": error,
            "contexto": contexto,
            "solucion": solucion,
            "tags": tags or [],
            "creada_en": datetime.now().isoformat(),
            "usada": 0
        }
        for l in self.index["lecciones"]:
            if l["agent_id"] == agent_id and l["error"] == error:
                l["usada"] += 1
                l["ultima_uso"] = datetime.now().isoformat()
                self._save_index()
                return l
        self.index["lecciones"].append(leccion)
        self._save_index()
        return leccion

    def buscar_lecciones(self, agent_id: str = None, tag: str = None, error: str = None) -> list:
        resultados = self.index["lecciones"]
        if agent_id:
            resultados = [l for l in resultados if l["agent_id"] == agent_id]
        if tag:
            resultados = [l for l in resultados if tag in l.get("tags", [])]
        if error:
            resultados = [l for l in resultados if error.lower() in l["error"].lower()]
        return sorted(resultados, key=lambda x: x["usada"], reverse=True)

    def obtener_contexto(self, agent_id: str) -> dict:
        return self.index["contexto"].get(agent_id, {})

    def guardar_contexto(self, agent_id: str, key: str, value: str):
        if agent_id not in self.index["contexto"]:
            self.index["contexto"][agent_id] = {}
        self.index["contexto"][agent_id][key] = {
            "value": value,
            "updated_at": datetime.now().isoformat()
        }
        self._save_index()

    def buscar_en_memoria(self, query: str) -> list:
        query_lower = query.lower()
        resultados = []
        for tag, items in self.index.get("tags", {}).items():
            if query_lower in tag.lower():
                resultados.extend(items.get("items", []) if isinstance(items, dict) else items)
        for leccion in self.index["lecciones"]:
            if any(query_lower in v.lower() for v in leccion.values() if isinstance(v, str)):
                resultados.append(leccion)
        for conexion in self.index["conexiones"]:
            if query_lower in conexion["a"].lower() or query_lower in conexion["b"].lower():
                resultados.append(conexion)
        return resultados

    def tag(self, nombre: str, descripcion: str, items: list = None):
        self.index["tags"][nombre] = {
            "descripcion": descripcion,
            "items": items or [],
            "creado_en": datetime.now().isoformat()
        }
        self._save_index()

    def get_stats(self) -> dict:
        return {
            "conexiones": len(self.index["conexiones"]),
            "lecciones": len(self.index["lecciones"]),
            "agentes_con_contexto": len(self.index["contexto"]),
            "tags": len(self.index["tags"])
        }


# ============================================================================
# LEARNING SYSTEM (Consolidado)
# ============================================================================

class LearningSystem:
    """Sistema de aprendizaje de errores con checklists pre-ejecución."""

    def __init__(self):
        self.lessons = self._load_lessons()

    def _load_lessons(self) -> list:
        if LESSONS_FILE.exists():
            return json.loads(LESSONS_FILE.read_text(encoding="utf-8"))
        return []

    def _save_lessons(self):
        LESSONS_FILE.write_text(json.dumps(self.lessons, indent=2, ensure_ascii=False), encoding="utf-8")

    def record_error(self, agent_id: str, error: str, context: str, solution: str, tags: list = None) -> dict:
        lesson = {
            "agent_id": agent_id,
            "error": error,
            "context": context,
            "solution": solution,
            "tags": tags or [],
            "learned_at": datetime.now().isoformat(),
            "occurrences": 1,
            "last_seen": datetime.now().isoformat()
        }
        for existing in self.lessons:
            if existing["agent_id"] == agent_id and existing["error"].lower() == error.lower():
                existing["occurrences"] += 1
                existing["last_seen"] = datetime.now().isoformat()
                self._save_lessons()
                return existing
        self.lessons.append(lesson)
        self._save_lessons()
        return lesson

    def get_warnings_for_agent(self, agent_id: str) -> list:
        warnings = []
        for lesson in self.lessons:
            if lesson["agent_id"] == agent_id and lesson["occurrences"] >= 2:
                warnings.append({
                    "error": lesson["error"],
                    "context": lesson["context"],
                    "solution": lesson["solution"],
                    "occurrences": lesson["occurrences"]
                })
        return sorted(warnings, key=lambda x: x["occurrences"], reverse=True)

    def get_relevant_lessons(self, agent_id: str, task_description: str) -> list:
        relevant = []
        task_lower = task_description.lower()
        for lesson in self.lessons:
            if lesson["agent_id"] == agent_id:
                if any(word in lesson["error"].lower() or word in lesson["context"].lower()
                       for word in task_lower.split() if len(word) > 3):
                    relevant.append(lesson)
        return relevant

    def get_all_lessons(self) -> list:
        return self.lessons

    def get_agent_lessons(self, agent_id: str) -> list:
        return [l for l in self.lessons if l["agent_id"] == agent_id]

    def generate_pre_execution_checklist(self, agent_id: str, task: str) -> list:
        warnings = self.get_warnings_for_agent(agent_id)
        relevant = self.get_relevant_lessons(agent_id, task)
        checklist = []
        for w in warnings[:5]:
            checklist.append(f"⚠️ EVITAR: {w['error']} → SOLUCIÓN: {w['solution']}")
        for r in relevant[:3]:
            checklist.append(f"📝 RECORDAR: {r['error']} en contexto '{r['context']}' → {r['solution']}")
        return checklist

    def get_stats(self) -> dict:
        agents = set(l["agent_id"] for l in self.lessons)
        return {
            "total_lessons": len(self.lessons),
            "agents_with_lessons": len(agents),
            "most_common_error": max(self.lessons, key=lambda x: x["occurrences"])["error"] if self.lessons else None,
            "total_occurrences": sum(l["occurrences"] for l in self.lessons)
        }


# ============================================================================
# ORCHESTRATOR (Consolidado)
# ============================================================================

class Orchestrator:
    """Coordinador central de agentes."""

    def __init__(self):
        self.state = self._load_state()
        self.max_iterations = 10
        self.timeout_minutes = 30

    def _load_state(self) -> dict:
        if ORCHESTRATOR_STATE.exists():
            return json.loads(ORCHESTRATOR_STATE.read_text(encoding="utf-8"))
        return {
            "active_agents": {},
            "completed_tasks": [],
            "failed_tasks": [],
            "shared_context": {},
            "iteration": 0,
            "started_at": None
        }

    def _save_state(self):
        ORCHESTRATOR_STATE.write_text(json.dumps(self.state, indent=2, ensure_ascii=False), encoding="utf-8")

    def register_agent(self, agent_id: str, goal: str, context: str, maestro: str = None):
        self.state["active_agents"][agent_id] = {
            "goal": goal,
            "context": context,
            "maestro": maestro,
            "status": "active",
            "started_at": datetime.now().isoformat(),
            "iterations": 0,
            "progress": []
        }
        self._save_state()

    def update_progress(self, agent_id: str, message: str):
        if agent_id in self.state["active_agents"]:
            self.state["active_agents"][agent_id]["progress"].append({
                "time": datetime.now().isoformat(),
                "message": message
            })
            self._save_state()

    def complete_task(self, agent_id: str, result: str):
        if agent_id in self.state["active_agents"]:
            self.state["active_agents"][agent_id]["status"] = "completed"
            self.state["active_agents"][agent_id]["result"] = result
            self.state["completed_tasks"].append({
                "agent_id": agent_id,
                "result": result,
                "completed_at": datetime.now().isoformat()
            })
            self._save_state()

    def fail_task(self, agent_id: str, error: str):
        if agent_id in self.state["active_agents"]:
            self.state["active_agents"][agent_id]["status"] = "failed"
            self.state["active_agents"][agent_id]["error"] = error
            self.state["failed_tasks"].append({
                "agent_id": agent_id,
                "error": error,
                "failed_at": datetime.now().isoformat()
            })
            self._save_state()

    def delegate_to(self, from_agent: str, to_agent: str, task: str, reason: str):
        if "delegations" not in self.state:
            self.state["delegations"] = []
        self.state["delegations"].append({
            "from": from_agent,
            "to": to_agent,
            "task": task,
            "reason": reason,
            "delegated_at": datetime.now().isoformat()
        })
        self._save_state()

    def get_shared_context(self, key: str = None) -> dict:
        if key:
            return self.state["shared_context"].get(key)
        return self.state["shared_context"]

    def set_shared_context(self, key: str, value: str):
        self.state["shared_context"][key] = value
        self._save_state()

    def should_continue(self) -> bool:
        active = [a for a in self.state["active_agents"].values() if a["status"] == "active"]
        if not active:
            return False
        if self.state["iteration"] >= self.max_iterations:
            return False
        if self.state["started_at"]:
            started = datetime.fromisoformat(self.state["started_at"])
            elapsed = (datetime.now() - started).total_seconds() / 60
            if elapsed >= self.timeout_minutes:
                return False
        return True

    def get_status(self) -> dict:
        active_count = sum(1 for a in self.state["active_agents"].values() if a["status"] == "active")
        completed_count = len(self.state["completed_tasks"])
        failed_count = len(self.state["failed_tasks"])
        return {
            "active_agents": active_count,
            "completed_tasks": completed_count,
            "failed_tasks": failed_count,
            "total_agents": len(self.state["active_agents"]),
            "iteration": self.state["iteration"],
            "should_continue": self.should_continue()
        }

    def reset(self):
        self.state = {
            "active_agents": {},
            "completed_tasks": [],
            "failed_tasks": [],
            "shared_context": {},
            "iteration": 0,
            "started_at": datetime.now().isoformat()
        }
        self._save_state()


# ============================================================================
# CLI
# ============================================================================

def main():
    """CLI principal del sistema."""
    import argparse

    parser = argparse.ArgumentParser(description="Neural Fellowship — Sistema Neuronal de Agentes")
    parser.add_argument("--maestros", action="store_true", help="Listar solo maestros")
    parser.add_argument("--agents", action="store_true", help="Listar todos los agentes")
    parser.add_argument("--route", type=str, help="Ruta de una tarea al agente correcto")
    parser.add_argument("--auto", action="store_true", help="Auto-ejecutar tareas mecánicas")
    parser.add_argument("--scan", action="store_true", help="Escanear tareas pendientes")
    parser.add_argument("--status", action="store_true", help="Estado del sistema")
    parser.add_argument("--memory", type=str, help="Buscar en memoria")
    parser.add_argument("--lesson", type=str, metavar="AGENT:ERROR:CTX:SOL", help="Registrar lección")
    parser.add_argument("--orchestrate", type=str, help="Iniciar orquestación de tarea")

    args = parser.parse_args()

    if args.maestros:
        print("🎯 AGENTES MAESTROS (63)")
        print("=" * 50)
        for mid, info in sorted(AGENTES_MAESTROS.items()):
            auto_str = "⚡auto" if info.get("automatizable") else "🧠ia"
            print(f"  {info['emoji']} {mid:20s} {info['dominio']:20s} [{info['division']}] {auto_str}")

    elif args.agents:
        print("🎯 TODOS LOS AGENTES")
        print("=" * 50)
        print(f"\n--- MAESTROS ({len(AGENTES_MAESTROS)}) ---")
        for mid, info in sorted(AGENTES_MAESTROS.items()):
            print(f"  {info['emoji']} {mid} — {info['dominio']}")
        print(f"\n--- ESPECIALIZADOS ({len(AGENTES_ESPECIALIZADOS)}) ---")
        for aid, info in sorted(AGENTES_ESPECIALIZADOS.items()):
            print(f"  └─ {aid} → {info['maestro']}")

    elif args.route:
        orch = Orquestador()
        resultado = orch.ruta_completa(args.route)
        print(f"📋 Tarea: {resultado['tarea']}")
        print(f"🎯 Maestro: {resultado['maestro']['maestro']} (confianza: {resultado['maestro']['confianza']}%)")
        print(f"🔧 Especialista: {resultado['especialista'].get('especialista', 'N/A')} (confianza: {resultado['especialista'].get('confianza', 0)}%)")
        print(f"⚡ Automatizable: {resultado['automatizable']}")
        print(f"📝 Motivo: {resultado['maestro']['motivo']}")

    elif args.auto:
        print("🤖 AUTO-EXECUTOR — Escaneando tareas mecánicas...")
        detector = DetectorTareas()
        executor = AutoExecutor()
        tareas = detector.scan_all()
        ejecutadas = 0
        for tarea in tareas:
            if tarea.get("completada"):
                continue
            resultado = executor.ejecutar(tarea["texto"], dry_run=True)
            if resultado["status"] != "no_automatizable":
                print(f"  ⚡ {tarea['texto'][:60]}... → {resultado['accion']}")
                ejecutadas += 1
        print(f"\n  {ejecutadas} tareas detectadas para auto-ejecución")

    elif args.scan:
        print("🔍 ESCANEO DE TAREAS")
        print("=" * 50)
        detector = DetectorTareas()
        stats = detector.get_stats()
        print(f"  Total: {stats['total']}")
        print(f"  Pendientes: {stats['pendientes']}")
        print(f"  Completadas: {stats['completadas']}")
        print(f"  Fuentes: {stats['fuentes_escaneadas']}")
        print()
        tareas = detector.scan_all()
        for t in tareas[:20]:
            status = "✅" if t.get("completada") else "⬜"
            print(f"  {status} {t['texto'][:70]}")
        if len(tareas) > 20:
            print(f"  ... y {len(tareas) - 20} más")

    elif args.status:
        print("📊 ESTADO DEL SISTEMA")
        print("=" * 50)
        orch = Orchestrator()
        status = orch.get_status()
        print(f"  Agentes activos: {status['active_agents']}")
        print(f"  Tareas completadas: {status['completed_tasks']}")
        print(f"  Tareas fallidas: {status['failed_tasks']}")
        print(f"  Iteración: {status['iteration']}")
        print()
        mem = MemorySystem()
        mem_stats = mem.get_stats()
        print(f"  🧠 Memoria:")
        print(f"     Conexiones: {mem_stats['conexiones']}")
        print(f"     Lecciones: {mem_stats['lecciones']}")
        print(f"     Tags: {mem_stats['tags']}")
        print()
        learn = LearningSystem()
        learn_stats = learn.get_stats()
        print(f"  📚 Aprendizaje:")
        print(f"     Lecciones: {learn_stats['total_lessons']}")
        print(f"     Agentes: {learn_stats['agents_with_lessons']}")
        if learn_stats['most_common_error']:
            print(f"     Error más común: {learn_stats['most_common_error']}")

    elif args.memory:
        mem = MemorySystem()
        resultados = mem.buscar_en_memoria(args.memory)
        print(f"🧠 Búsqueda en memoria: '{args.memory}'")
        print(f"  {len(resultados)} resultados")
        for r in resultados[:10]:
            print(f"  • {r.get('error', r.get('a', ''))}")

    elif args.lesson:
        parts = args.lesson.split(":", 3)
        if len(parts) == 4:
            learn = LearningSystem()
            learn.record_error(parts[0], parts[1], parts[2], parts[3])
            print(f"📚 Lección registrada: {parts[0]} → {parts[1]}")
        else:
            print("Formato: AGENT_ID:ERROR:CONTEXT:SOLUTION")

    elif args.orchestrate:
        print(f"🔄 ORQUESTANDO: {args.orchestrate}")
        orch = Orquestador()
        ruta = orch.ruta_completa(args.orchestrate)
        print(f"  Maestro: {ruta['maestro']['maestro']}")
        print(f"  Especialista: {ruta['especialista'].get('especialista', 'N/A')}")
        print(f"  Automatizable: {ruta['automatizable']}")

    else:
        # Default: scan + propuestas
        print("🧠 NEURAL FELLOWSHIP — Sistema Neuronal de Agentes")
        print("=" * 50)
        print()

        # Estado del orquestador
        orch_sys = Orchestrator()
        status = orch_sys.get_status()
        print(f"📊 Orquestador: {status['active_agents']} activos, {status['completed_tasks']} completadas, {status['failed_tasks']} fallidas")
        print()

        # Tareas pendientes
        detector = DetectorTareas()
        stats = detector.get_stats()
        print(f"🔍 Tareas pendientes: {stats['pendientes']} (de {stats['total']} total)")
        print()

        # Propuestas de auto-ejecución
        executor = AutoExecutor()
        tareas = detector.scan_all()
        auto_tareas = []
        for t in tareas:
            if t.get("completada"):
                continue
            tipo, params = executor.detectar_tipo(t["texto"])
            if tipo:
                auto_tareas.append((t["texto"], tipo))

        if auto_tareas:
            print("⚡ TAREAS AUTOMATIZABLES DETECTADAS:")
            for texto, tipo in auto_tareas:
                print(f"  • [{tipo}] {texto[:60]}")
            print()
        else:
            print("⚡ No se detectaron tareas automatizables.")
            print()

        # Estadísticas de memoria
        mem = MemorySystem()
        mem_stats = mem.get_stats()
        learn = LearningSystem()
        learn_stats = learn.get_stats()
        print(f"🧠 Memoria: {mem_stats['conexiones']} conexiones, {mem_stats['lecciones']} lecciones")
        print(f"📚 Aprendizaje: {learn_stats['total_lessons']} lecciones, {learn_stats['agents_with_lessons']} agentes")


if __name__ == "__main__":
    main()
