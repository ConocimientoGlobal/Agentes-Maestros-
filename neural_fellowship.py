#!/usr/bin/env python3
"""
NEURAL FELLOWSHIP — Red Neuronal de Agentes Autónomos
=====================================================
Copia autocontenida del sistema de orquestación y agentes maestros.
Sin herramientas externas: pura lógica de programación, objetivos,
routing y ejecución automatizada.

Estructura:
  - 63 Agentes Maestros (nodos de dominio)
  - 243 Agentes Especializados (nodos hoja)
  - Orquestador (routing engine)
  - Detector de Tareas (pending task scanner)
  - Auto-Executor (mechanical task executor)
  - Queue Manager (IA task queue)
  - State Manager (persistencia sin re-ejecución)

Uso:
  python3 neural_fellowship.py                  # Scan + propuestas
  python3 neural_fellowship.py --auto           # Auto-ejecutar tareas mecánicas
  python3 neural_fellowship.py --route "tarea" # Ruteo al agente correcto
  python3 neural_fellowship.py --agents         # Listar todos los agentes
  python3 neural_fellowship.py --maestros       # Listar solo maestros
"""

import json
import os
import re
import subprocess
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

HOME = Path("/data/data/com.termux/files/home")
KNOWLEDGE_DIR = HOME / "knowledge"
PROJECTS_DIR = KNOWLEDGE_DIR / "_projects"
ACTIVE_DIR = KNOWLEDGE_DIR / "_active"
TODAY_FILE = KNOWLEDGE_DIR / "TODAY.md"
QUEUE_FILE = HOME / "agency-agents" / "orchestrator-logs" / "agent_queue.json"
STATE_FILE = HOME / "agency-agents" / "orchestrator-logs" / "executor_state.json"
LOG_DIR = HOME / "agency-agents" / "orchestrator-logs"

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
        "especialidades": ["cloud", "kubernetes", "terraform", "cicd", "monitoring", "networking", "self-hosted"],
        "routing": "Infraestructura cloud, Kubernetes, CI/CD, redes",
        "automatizable": True,
    },
    "LAB": {
        "dominio": "Experimentos",
        "division": "cross → usa NEXUS",
        "emoji": "🧪",
        "especialidades": ["ab-testing", "feature-flags", "prototyping", "spike", "proof-of-concept"],
        "routing": "Experimentación, prototipos rápidos, spikes técnicos",
        "automatizable": False,
    },
    "LIBRARY": {
        "dominio": "Documentación",
        "division": "cross → usa ORION",
        "emoji": "📚",
        "especialidades": ["api-docs", "tutorials", "knowledge-base", "wiki", "readme", "changelog"],
        "routing": "Documentación técnica, wikis, bases de conocimiento",
        "automatizable": False,
    },
    "PHOENIX": {
        "dominio": "Delegación",
        "division": "cross → orquesta todos",
        "emoji": "🔄",
        "especialidades": ["multi-agent-delegation", "workflow-orchestration", "task-routing"],
        "routing": "Orquestación de múltiples agentes, delegación compleja",
        "automatizable": False,
    },
    "CONFIG": {
        "dominio": "Configuración",
        "division": "cross → usa NEXUS",
        "emoji": "⚙️",
        "especialidades": ["dotfiles", "environment-setup", "tool-configuration", "skill-authoring"],
        "routing": "Configuración de herramientas, entornos, dotfiles",
        "automatizable": True,
    },
    "EVENT": {
        "dominio": "Webhooks",
        "division": "cross → usa INFRA",
        "emoji": "🔗",
        "especialidades": ["webhook-integration", "event-driven", "realtime-sync", "api-integration"],
        "routing": "Webhooks, integraciones event-driven, sincronización en tiempo real",
        "automatizable": False,
    },
    "BOT": {
        "dominio": "Bots",
        "division": "cross → usa AGENCY",
        "emoji": "🤖",
        "especialidades": ["telegram-bot", "discord-bot", "chatbot", "automation-bot", "n8n", "make"],
        "routing": "Creación de bots, automatizaciones, flujos n8n/Make",
        "automatizable": False,
    },
    "GEO": {
        "dominio": "Geoespacial",
        "division": "cross → usa HELIOS",
        "emoji": "📍",
        "especialidades": ["geocoding", "routing-maps", "geofencing", "location-intelligence"],
        "routing": "Servicios de ubicación, mapas, geofencing",
        "automatizable": False,
    },
    "SYNC": {
        "dominio": "Sincronización",
        "division": "cross → usa INFRA",
        "emoji": "🔄",
        "especialidades": ["data-sync", "state-sync", "file-sync", "realtime-collaboration"],
        "routing": "Sincronización de datos, archivos, estado distribuido",
        "automatizable": False,
    },
    "MATH": {
        "dominio": "Matemáticas",
        "division": "cross → usa NEXUS",
        "emoji": "📐",
        "especialidades": ["linear-algebra", "calculus", "probability", "optimization", "numerical-methods"],
        "routing": "Cálculos matemáticos, optimización, modelado numérico",
        "automatizable": True,
    },
    "DECIDE": {
        "dominio": "Decisiones",
        "division": "cross → usa ORION",
        "emoji": "🎯",
        "especialidades": ["decision-matrix", "cost-benefit", "risk-assessment", "priority-framework"],
        "routing": "Árboles de decisión, análisis de costo-beneficio, priorización",
        "automatizable": False,
    },
    "DIVINER": {
        "dominio": "Monitoreo",
        "division": "cross → usa SENTINEL",
        "emoji": "👁️",
        "especialidades": ["uptime-monitoring", "log-analysis", "alerting", "observability", "anomaly-detection"],
        "routing": "Monitoreo de sistemas, alertas, observabilidad",
        "automatizable": True,
    },
    "SHERLOCK": {
        "dominio": "Identidad",
        "division": "cross → usa SENTINEL",
        "emoji": "🔍",
        "especialidades": ["osint", "identity-verification", "fraud-detection", "account-security"],
        "routing": "Investigación OSINT, verificación de identidad, fraude",
        "automatizable": False,
    },
    "CLEANER": {
        "dominio": "Limpieza",
        "division": "cross → usa INFRA",
        "emoji": "🧹",
        "especialidades": ["data-cleaning", "cache-cleanup", "log-rotation", "storage-optimization", "unsubscribe"],
        "routing": "Limpieza de datos, caché, almacenamiento, desuscripción de brokers",
        "automatizable": True,
    },
    "LAUNCH": {
        "dominio": "Lanzamientos",
        "division": "cross → usa AGENCY",
        "emoji": "🚀",
        "especialidades": ["product-launch", "go-to-market", "pre-launch-checklist", "launch-campaign"],
        "routing": "Lanzamientos de producto, Go-to-market, campañas de lanzamiento",
        "automatizable": False,
    },
    "ACADEMY": {
        "dominio": "Educación",
        "division": "cross → usa ORION",
        "emoji": "🎓",
        "especialidades": ["curriculum-design", "tutorial-creation", "course-development", "study-plans", "flashcards"],
        "routing": "Diseño curricular, creación de tutoriales, planes de estudio",
        "automatizable": False,
    },
    "TREASURE": {
        "dominio": "Criptoactivos",
        "division": "cross → usa CHAIN",
        "emoji": "🏦",
        "especialidades": ["tokenomics", "yield-farming", "portfolio-tracking", "airdrop-strategy"],
        "routing": "Gestión de criptoactivos, DeFi, tokenomics",
        "automatizable": False,
    },
    "ARCHITECT": {
        "dominio": "Arquitectura de Software",
        "division": "cross → usa NEXUS",
        "emoji": "🏛️",
        "especialidades": ["system-design", "domain-driven-design", "microservices", "monorepo", "event-sourcing"],
        "routing": "Arquitectura de software, diseño de sistemas, DDD",
        "automatizable": False,
    },
    "SONUS": {
        "dominio": "Música",
        "division": "cross → usa ARCAN",
        "emoji": "🎵",
        "especialidades": ["music-production", "sound-design", "songwriting", "audio-generation", "music-marketing"],
        "routing": "Producción musical, composición, diseño de sonido",
        "automatizable": False,
    },
    "VISIO": {
        "dominio": "Visual",
        "division": "cross → usa ARCAN",
        "emoji": "🎬",
        "especialidades": ["video-production", "motion-graphics", "animation", "editing", "storyboarding"],
        "routing": "Producción de video, animación, motion graphics",
        "automatizable": False,
    },
    "DATA": {
        "dominio": "Datos",
        "division": "cross → usa NEXUS",
        "emoji": "🗄️",
        "especialidades": ["data-engineering", "data-visualization", "etl", "data-warehousing", "lakehouse"],
        "routing": "Ingeniería de datos, pipelines, warehousing",
        "automatizable": True,
    },
    "QUANTUM": {
        "dominio": "Rendimiento",
        "division": "cross → usa NEXUS",
        "emoji": "⚡",
        "especialidades": ["performance-optimization", "load-testing", "caching-strategy", "profiling", "web-vitals"],
        "routing": "Optimización de rendimiento, profiling, caching",
        "automatizable": True,
    },
    "BIO": {
        "dominio": "Biotecnología",
        "division": "cross → usa MNEMOS",
        "emoji": "🧬",
        "especialidades": ["genomics", "bioinformatics", "drug-discovery", "computational-biology"],
        "routing": "Bioinformática, genómica, descubrimiento de fármacos",
        "automatizable": False,
    },
    "LOCALIZATION": {
        "dominio": "Idiomas",
        "division": "cross → usa ORION",
        "emoji": "🌐",
        "especialidades": ["translation", "localization", "i18n", "multilingual-content", "cultural-adaptation"],
        "routing": "Traducción, localización, internacionalización",
        "automatizable": False,
    },
    "LEGACY": {
        "dominio": "Migración",
        "division": "cross → usa NEXUS",
        "emoji": "📦",
        "especialidades": ["system-migration", "legacy-modernization", "data-migration", "platform-migration"],
        "routing": "Migración de sistemas, modernización de legacy",
        "automatizable": False,
    },
    "SHOW": {
        "dominio": "Presentaciones",
        "division": "cross → usa ARCAN",
        "emoji": "🎤",
        "especialidades": ["slide-decks", "pitch-decks", "presentation-design", "public-speaking"],
        "routing": "Creación de presentaciones, pitch decks, charlas",
        "automatizable": False,
    },
    "VAULT": {
        "dominio": "Almacenamiento",
        "division": "cross → usa INFRA",
        "emoji": "🗃️",
        "especialidades": ["cloud-storage", "backup-solutions", "file-management", "cdn"],
        "routing": "Almacenamiento cloud, backups, gestión de archivos",
        "automatizable": True,
    },
    "WEBHOOK": {
        "dominio": "Integraciones",
        "division": "cross → usa INFRA",
        "emoji": "🔌",
        "especialidades": ["api-integration", "webhook-management", "third-party-connectors", "middleware"],
        "routing": "Integraciones API, webhooks, conectores第三方",
        "automatizable": False,
    },
    "ROLEPLAY": {
        "dominio": "Simulación",
        "division": "cross → usa todos",
        "emoji": "🎭",
        "especialidades": ["scenario-simulation", "red-teaming", "war-gaming", "persona-simulation"],
        "routing": "Simulación de escenarios, red teaming, modelado de amenazas",
        "automatizable": False,
    },
    "ASSEMBLER": {
        "dominio": "Orquestador Central",
        "division": "cross → orquesta todos",
        "emoji": "🧩",
        "especialidades": ["agent-orchestration", "workflow-automation", "complex-delegation"],
        "routing": "Orquestación central de agentes, workflows complejos",
        "automatizable": False,
    },
    "METRIX": {
        "dominio": "Analytics",
        "division": "cross → usa ORION",
        "emoji": "📈",
        "especialidades": ["web-analytics", "conversion-tracking", "funnel-analysis", "cohort-analysis", "attribution"],
        "routing": "Analítica web, tracking de conversiones, funnel analysis",
        "automatizable": False,
    },
    "CLOUD": {
        "dominio": "Cloud Computing",
        "division": "cross → usa INFRA",
        "emoji": "☁️",
        "especialidades": ["aws", "gcp", "azure", "serverless", "multi-cloud", "edge-computing"],
        "routing": "Computación cloud, multi-cloud, edge, serverless",
        "automatizable": True,
    },
    "PAY": {
        "dominio": "Pagos",
        "division": "cross → usa FORTIS",
        "emoji": "💸",
        "especialidades": ["checkout-optimization", "payment-integration", "billing-automation", "invoice-management"],
        "routing": "Optimización de checkout, integración de pagos, facturación",
        "automatizable": False,
    },
    "MEDIA": {
        "dominio": "Media/Entretenimiento",
        "division": "cross → usa ARCAN",
        "emoji": "🎞️",
        "especialidades": ["streaming", "content-creation", "podcast-production", "social-video"],
        "routing": "Streaming, producción de contenido, podcasts, video social",
        "automatizable": False,
    },
    "TRADE": {
        "dominio": "Trading",
        "division": "cross → usa AURUM",
        "emoji": "📉",
        "especialidades": ["algorithmic-trading", "technical-analysis", "risk-management", "portfolio-optimization"],
        "routing": "Trading algorítmico, análisis técnico, gestión de riesgo",
        "automatizable": False,
    },
    "SEARCH": {
        "dominio": "Búsqueda",
        "division": "cross → usa ORION",
        "emoji": "🔎",
        "especialidades": ["search-engine", "information-retrieval", "semantic-search", "knowledge-discovery"],
        "routing": "Motores de búsqueda, búsqueda semántica, recuperación de información",
        "automatizable": False,
    },
    "COMMS": {
        "dominio": "Comunicación",
        "division": "cross → usa ECHO",
        "emoji": "💬",
        "especialidades": ["email-management", "messaging", "notification-systems", "crisis-comms"],
        "routing": "Gestión de email, mensajería, sistemas de notificación",
        "automatizable": False,
    },
    "DB": {
        "dominio": "Bases de Datos",
        "division": "cross → usa NEXUS",
        "emoji": "🗃️",
        "especialidades": ["sql", "nosql", "graph-database", "vector-database", "database-design"],
        "routing": "Diseño de bases de datos, SQL, NoSQL, grafos, vectores",
        "automatizable": True,
    },
    "MONITOR": {
        "dominio": "Monitoreo Avanzado",
        "division": "cross → usa DIVINER",
        "emoji": "📊",
        "especialidades": ["infrastructure-monitoring", "application-monitoring", "business-intelligence", "sla-tracking"],
        "routing": "Monitoreo de infraestructura/aplicaciones, SLA, BI",
        "automatizable": True,
    },
    "CRM": {
        "dominio": "CRM",
        "division": "cross → usa AGENCY",
        "emoji": "👥",
        "especialidades": ["hubspot", "salesforce", "pipedrive", "crm-strategy", "lead-scoring"],
        "routing": "Gestión CRM, Salesforce, HubSpot, scoring de leads",
        "automatizable": False,
    },
    "LEARN": {
        "dominio": "Aprendizaje",
        "division": "cross → usa ACADEMY",
        "emoji": "📖",
        "especialidades": ["adaptive-learning", "skill-assessment", "learning-paths", "microlearning"],
        "routing": "Aprendizaje adaptivo, evaluación de habilidades, microlearning",
        "automatizable": False,
    },
    "TRAVEL": {
        "dominio": "Viajes",
        "division": "cross → usa ORION",
        "emoji": "✈️",
        "especialidades": ["trip-planning", "accommodation", "transport-optimization", "travel-guide"],
        "routing": "Planificación de viajes, alojamiento, optimización de transporte",
        "automatizable": False,
    },
    "LIFESTYLE": {
        "dominio": "Estilo de Vida",
        "division": "cross → usa MNEMOS",
        "emoji": "🌿",
        "especialidades": ["wellness", "productivity-habits", "life-optimization", "routine-design"],
        "routing": "Bienestar, hábitos de productividad, optimización de vida",
        "automatizable": False,
    },
    "SECURITY_OPS": {
        "dominio": "Operaciones de Seguridad",
        "division": "cross → usa SENTINEL",
        "emoji": "🔒",
        "especialidades": ["siem", "soc", "threat-hunting", "vulnerability-management", "soc-automation"],
        "routing": "Operaciones SOC, SIEM, threat hunting",
        "automatizable": False,
    },
    "OPEN-GEN": {
        "dominio": "Generación Abierta",
        "division": "cross → usa todos",
        "emoji": "🌊",
        "especialidades": ["creative-generation", "open-ended-tasks", "multi-modal", "emergent-behavior"],
        "routing": "Tareas abiertas, generación creativa, comportamiento emergente",
        "automatizable": False,
    },
    "GAMER": {
        "dominio": "Videojuegos",
        "division": "cross → usa CRONUS",
        "emoji": "🕹️",
        "especialidades": ["minecraft", "pokemon", "modpacks", "emulation", "speedrun"],
        "routing": "Minecraft, Pokémon, modpacks, emulación",
        "automatizable": False,
    },
}

# ============================================================================
# 243 AGENTES ESPECIALIZADOS — Nodos Hoja
# ============================================================================

AGENTES_ESPECIALIZADOS = {
    # ---- ARCAN (Design) ----
    "design-brand-guardian": {"maestro": "ARCAN", "nombre": "Brand Guardian", "capacidades": ["identidad-marca", "guía-estilo", "consistencia", "posicionamiento"]},
    "design-ui-designer": {"maestro": "ARCAN", "nombre": "UI Designer", "capacidades": ["interfaces", "componentes", "design-systems", "accesibilidad"]},
    "design-ux-architect": {"maestro": "ARCAN", "nombre": "UX Architect", "capacidades": ["arquitectura-ux", "css-systems", "guidance"]},
    "design-ux-researcher": {"maestro": "ARCAN", "nombre": "UX Researcher", "capacidades": ["user-testing", "behavior-analysis", "usability"]},
    "design-image-prompt-engineer": {"maestro": "ARCAN", "nombre": "Image Prompt Engineer", "capacidades": ["prompts-imagen", "ai-generation", "fotografía-ia"]},
    "design-visual-storyteller": {"maestro": "ARCAN", "nombre": "Visual Storyteller", "capacidades": ["narrativa-visual", "multimedia", "brand-storytelling"]},
    "design-whimsy-injector": {"maestro": "ARCAN", "nombre": "Whimsy Injector", "capacidades": ["personalidad", "delight", "interacciones-divertidas"]},
    "design-inclusive-visuals-specialist": {"maestro": "ARCAN", "nombre": "Inclusive Visuals Specialist", "capacidades": ["representación", "diversidad", "no-bias"]},
    "design-persona-walkthrough": {"maestro": "ARCAN", "nombre": "Persona Walkthrough Specialist", "capacidades": ["cognitive-walkthrough", "cRO", "persona-simulation"]},
    "design-ui-finish-gate-reviewer": {"maestro": "ARCAN", "nombre": "UI Finish-Gate Reviewer", "capacidades": ["ui-review", "quality-gate", "anti-generic"]},

    # ---- NEXUS (Engineering) ----
    "engineering-frontend-developer": {"maestro": "NEXUS", "nombre": "Frontend Developer", "capacidades": ["react", "vue", "angular", "performance", "web-app"]},
    "engineering-backend-architect": {"maestro": "NEXUS", "nombre": "Backend Architect", "capacidades": ["scalable-systems", "databases", "apis", "microservices"]},
    "engineering-mobile-app-builder": {"maestro": "NEXUS", "nombre": "Mobile App Builder", "capacidades": ["ios", "android", "react-native", "flutter"]},
    "engineering-devops-automator": {"maestro": "NEXUS", "nombre": "DevOps Automator", "capacidades": ["cicd", "cloud-ops", "infrastructure", "automation"]},
    "engineering-database-optimizer": {"maestro": "NEXUS", "nombre": "Database Optimizer", "capacidades": ["schema-design", "query-optimization", "indexing", "postgresql"]},
    "engineering-ai-engineer": {"maestro": "NEXUS", "nombre": "AI Engineer", "capacidades": ["ml-models", "deployment", "ai-integration", "llm-apps"]},
    "engineering-data-engineer": {"maestro": "NEXUS", "nombre": "Data Engineer", "capacidades": ["data-pipelines", "lakehouse", "spark", "dbt", "etl"]},
    "engineering-code-reviewer": {"maestro": "NEXUS", "nombre": "Code Reviewer", "capacidades": ["code-review", "correctness", "security", "maintainability"]},
    "engineering-software-architect": {"maestro": "NEXUS", "nombre": "Software Architect", "capacidades": ["system-design", "ddd", "patterns", "decisions"]},
    "engineering-sre": {"maestro": "NEXUS", "nombre": "SRE", "capacidades": ["slos", "error-budgets", "observability", "chaos-engineering"]},
    "engineering-prompt-engineer": {"maestro": "NEXUS", "nombre": "Prompt Engineer", "capacidades": ["prompt-design", "optimization", "testing", "reliability"]},
    "engineering-rag-pipeline-engineer": {"maestro": "NEXUS", "nombre": "RAG Pipeline Engineer", "capacidades": ["chunking", "retrieval", "hybrid-search", "reranking"]},
    "engineering-llm-post-training-engineer": {"maestro": "NEXUS", "nombre": "LLM Post-Training Engineer", "capacidades": ["sft", "dpo", "rlhf", "grpo", "release-gates"]},
    "engineering-multi-agent-systems-architect": {"maestro": "NEXUS", "nombre": "Multi-Agent Systems Architect", "capacidades": ["agent-topology", "context-management", "trust", "failure-recovery"]},
    "engineering-rapid-prototyper": {"maestro": "NEXUS", "nombre": "Rapid Prototyper", "capacidades": ["mvp", "proof-of-concept", "fast-development"]},
    "engineering-privacy-engineer": {"maestro": "NEXUS", "nombre": "Privacy Engineer", "capacidades": ["pii-discovery", "data-minimization", "dsar", "pseudonymization"]},
    "engineering-security-code-reviewer": {"maestro": "SENTINEL", "nombre": "AI Code Security Auditor", "capacidades": ["vibe-code-review", "secret-detection", "injection-hunting"]},

    # ---- AGENCY (Marketing + Sales) ----
    "marketing-seo-specialist": {"maestro": "AGENCY", "nombre": "SEO Specialist", "capacidades": ["technical-seo", "content-optimization", "link-building", "organic-growth"]},
    "marketing-content-creator": {"maestro": "AGENCY", "nombre": "Content Creator", "capacidades": ["editorial-calendar", "copywriting", "brand-storytelling", "multi-platform"]},
    "marketing-email-marketing-strategist": {"maestro": "AGENCY", "nombre": "Email Marketing Strategist", "capacidades": ["crm-campaigns", "lifecycle-automation", "segmentation", "deliverability"]},
    "marketing-social-media-strategist": {"maestro": "AGENCY", "nombre": "Social Media Strategist", "capacidades": ["linkedin", "twitter", "cross-platform", "thought-leadership"]},
    "marketing-growth-hacker": {"maestro": "AGENCY", "nombre": "Growth Hacker", "capacidades": ["user-acquisition", "viral-loops", "funnel-optimization", "experimentation"]},
    "sales-proposal-strategist": {"maestro": "AGENCY", "nombre": "Proposal Strategist", "capacidades": ["rfp", "win-themes", "competitive-positioning", "executive-summary"]},
    "sales-discovery-coach": {"maestro": "AGENCY", "nombre": "Discovery Coach", "capacidades": ["question-design", "gap-quantification", "call-structure"]},
    "sales-deal-strategist": {"maestro": "AGENCY", "nombre": "Deal Strategist", "capacidades": ["meddpicc", "competitive-analysis", "win-planning"]},
    "sales-offer-lead-gen-strategist": {"maestro": "AGENCY", "nombre": "Offer & Lead Gen Strategist", "capacidades": ["value-proposition", "lead-magnets", "multi-channel"]},
    "sales-outbound-strategist": {"maestro": "AGENCY", "nombre": "Outbound Strategist", "capacidades": ["prospecting", "sequences", "research-personalization"]},
    "paid-media-ppc-strategist": {"maestro": "AGENCY", "nombre": "PPC Campaign Strategist", "capacidades": ["google-ads", "microsoft-ads", "amazon-ads", "bidding-strategies"]},
    "paid-media-paid-social-strategist": {"maestro": "AGENCY", "nombre": "Paid Social Strategist", "capacidades": ["meta-ads", "linkedin-ads", "tiktok-ads", "full-funnel"]},
    "paid-media-tracking-specialist": {"maestro": "AGENCY", "nombre": "Tracking & Measurement Specialist", "capacidades": ["gtm", "ga4", "conversion-tracking", "attribution"]},

    # ---- SENTINEL (Security) ----
    "security-penetration-tester": {"maestro": "SENTINEL", "nombre": "Penetration Tester", "capacidades": ["pentesting", "red-team", "vulnerability-assessment", "network"]},
    "security-application-security-engineer": {"maestro": "SENTINEL", "nombre": "AppSec Engineer", "capacidades": ["threat-modeling", "secure-code-review", "sast-dast", "sdlc"]},
    "security-security-architect": {"maestro": "SENTINEL", "nombre": "Security Architect", "capacidades": ["secure-design", "trust-boundaries", "defense-in-depth", "risk-review"]},
    "security-compliance-auditor": {"maestro": "SENTINEL", "nombre": "Compliance Auditor", "capacidades": ["soc2", "iso27001", "hipaa", "pci-dss", "audit"]},
    "security-incident-responder": {"maestro": "SENTINEL", "nombre": "Incident Responder", "capacidades": ["forensics", "breach-investigation", "containment", "post-mortem"]},
    "security-threat-intelligence-analyst": {"maestro": "SENTINEL", "nombre": "Threat Intelligence Analyst", "capacidades": ["adversary-tracking", "mitre-attck", "intel-reports"]},
    "security-blockchain-security-auditor": {"maestro": "SENTINEL", "nombre": "Blockchain Security Auditor", "capacidades": ["smart-contract-audit", "formal-verification", "defi-security"]},
    "security-secrets-credential-engineer": {"maestro": "SENTINEL", "nombre": "Secrets & Credential Hygiene Engineer", "capacidades": ["secret-detection", "vaulting", "rotation", "leak-response"]},

    # ---- AURUM (Finance) ----
    "finance-financial-analyst": {"maestro": "AURUM", "nombre": "Financial Analyst", "capacidades": ["modeling", "forecasting", "scenario-analysis", "decision-support"]},
    "finance-fpa-analyst": {"maestro": "AURUM", "nombre": "FP&A Analyst", "capacidades": ["budgeting", "variance-analysis", "rolling-forecasts", "planning"]},
    "finance-bookkeeper-controller": {"maestro": "AURUM", "nombre": "Bookkeeper & Controller", "capacidades": ["accounting", "reconciliation", "month-end-close", "gaap"]},
    "finance-tax-strategist": {"maestro": "AURUM", "nombre": "Tax Strategist", "capacidades": ["tax-optimization", "compliance", "transfer-pricing", "planning"]},
    "finance-investment-researcher": {"maestro": "AURUM", "nombre": "Investment Researcher", "capacidades": ["due-diligence", "portfolio-analysis", "asset-valuation"]},

    # ---- ORION (Research) ----
    "research-research-synthesist": {"maestro": "ORION", "nombre": "Research Synthesist", "capacidades": ["literature-review", "source-evaluation", "evidence-synthesis", "mapping"]},
    "academic-statistician": {"maestro": "ORION", "nombre": "Statistician", "capacidades": ["experimental-design", "inference", "signal-vs-noise", "methodology"]},
    "academic-anthropologist": {"maestro": "ORION", "nombre": "Anthropologist", "capacidades": ["cultural-systems", "ethnography", "kinship", "rituals"]},
    "academic-historian": {"maestro": "ORION", "nombre": "Historian", "capacidades": ["historical-analysis", "periodization", "material-culture", "coherence"]},
    "academic-narratologist": {"maestro": "ORION", "nombre": "Narratologist", "capacidades": ["narrative-theory", "story-structure", "character-arcs", "literary-analysis"]},
    "academic-psychologist": {"maestro": "ORION", "nombre": "Psychologist", "capacidades": ["behavior", "personality", "motivation", "cognitive-patterns"]},
    "academic-geographer": {"maestro": "ORION", "nombre": "Geographer", "capacidades": ["physical-geography", "climate", "cartography", "spatial-analysis"]},

    # ---- MERIDIAN (Product) ----
    "product-product-manager": {"maestro": "MERIDIAN", "nombre": "Product Manager", "capacidades": ["discovery", "roadmap", "stakeholder-alignment", "outcome-measurement"]},
    "product-sprint-prioritizer": {"maestro": "MERIDIAN", "nombre": "Sprint Prioritizer", "capacidades": ["agile-planning", "feature-prioritization", "resource-allocation"]},
    "project-management-project-shepherd": {"maestro": "MERIDIAN", "nombre": "Project Shepherd", "capacidades": ["cross-functional-coordination", "timeline-management", "stakeholder-alignment"]},
    "project-management-experiment-tracker": {"maestro": "MERIDIAN", "nombre": "Experiment Tracker", "capacidades": ["ab-testing", "hypothesis-validation", "rigorous-analysis"]},
    "product-feedback-synthesizer": {"maestro": "MERIDIAN", "nombre": "Feedback Synthesizer", "capacidades": ["user-feedback", "qualitative-analysis", "prioritization"]},
    "product-trend-researcher": {"maestro": "MERIDIAN", "nombre": "Trend Researcher", "capacidades": ["market-intelligence", "emerging-trends", "competitive-analysis"]},
    "project-management-studio-producer": {"maestro": "MERIDIAN", "nombre": "Studio Producer", "capacidades": ["strategic-leadership", "resource-allocation", "portfolio-management"]},

    # ---- HELIOS (GIS) ----
    "gis-gis-analyst": {"maestro": "HELIOS", "nombre": "GIS Analyst", "capacidades": ["map-creation", "layer-management", "spatial-queries", "data-integrity"]},
    "gis-web-gis-developer": {"maestro": "HELIOS", "nombre": "Web GIS Developer", "capacidades": ["maplibre", "arcgis-js", "leaflet", "interactive-maps"]},
    "gis-spatial-data-scientist": {"maestro": "HELIOS", "nombre": "Spatial Data Scientist", "capacidades": ["spatial-statistics", "econometrics", "clustering", "predictive-analytics"]},
    "gis-geoai-ml-engineer": {"maestro": "HELIOS", "nombre": "GeoAI/ML Engineer", "capacidades": ["feature-extraction", "object-detection", "land-cover", "satellite-imagery"]},
    "gis-cartography-designer": {"maestro": "HELIOS", "nombre": "Cartography Designer", "capacidades": ["map-aesthetics", "color-theory", "typography", "label-placement"]},
    "spatial-computing-xr-immersive-developer": {"maestro": "HELIOS", "nombre": "XR Immersive Developer", "capacidades": ["webxr", "browser-ar", "immersive-web", "3d-web"]},

    # ---- CRONUS (Game Dev) ----
    "game-development-game-designer": {"maestro": "CRONUS", "nombre": "Game Designer", "capacidades": ["gdd", "mechanics", "player-psychology", "gameplay-loops"]},
    "game-development-level-designer": {"maestro": "CRONUS", "nombre": "Level Designer", "capacidades": ["layout-theory", "pacing", "encounter-design", "environmental-narrative"]},
    "game-development-narrative-designer": {"maestro": "CRONUS", "nombre": "Narrative Designer", "capacidades": ["branching-dialogue", "lore-architecture", "environmental-storytelling"]},
    "game-development-economy-designer": {"maestro": "CRONUS", "nombre": "Economy Designer", "capacidades": ["currency-systems", "sources-sinks", "monetization", "inflation-control"]},
    "game-development-technical-artist": {"maestro": "CRONUS", "nombre": "Technical Artist", "capacidades": ["shaders", "vfx", "lod-pipelines", "asset-optimization"]},

    # ---- MNEMOS (Healthcare + Specialized) ----
    "specialized-agents-orchestrator": {"maestro": "MNEMOS", "nombre": "Agents Orchestrator", "capacidades": ["pipeline-management", "workflow-orchestration", "development-leader"]},
    "specialized-master-plan-architect": {"maestro": "MNEMOS", "nombre": "Master Plan Architect", "capacidades": ["architecture-teaching", "red-teaming", "implementation-plans"]},
    "specialized-mcp-builder": {"maestro": "MNEMOS", "nombre": "MCP Builder", "capacidades": ["mcp-server", "custom-tools", "model-context-protocol"]},
    "specialized-workflow-architect": {"maestro": "MNEMOS", "nombre": "Workflow Architect", "capacidades": ["workflow-design", "user-journeys", "failure-modes", "handoff-contracts"]},
    "specialized-business-strategist": {"maestro": "MNEMOS", "nombre": "Business Strategist", "capacidades": ["competitive-analysis", "market-entry", "business-model", "growth-planning"]},
    "specialized-operations-manager": {"maestro": "MNEMOS", "nombre": "Operations Manager", "capacidades": ["lean", "six-sigma", "process-mapping", "kpi-governance"]},
    "specialized-customer-success-manager": {"maestro": "MNEMOS", "nombre": "Customer Success Manager", "capacidades": ["onboarding", "health-scoring", "qbr", "churn-prevention"]},
    "specialized-zk-steward": {"maestro": "MNEMOS", "nombre": "ZK Steward", "capacidades": ["zettelkasten", "atomic-notes", "knowledge-graph", "cross-domain"]},
}

# ============================================================================
# ORQUESTADOR — Routing Engine
# ============================================================================

class Orquestador:
    """
    Routing Engine: determina qué agente maestro y especializado
    es el correcto para una tarea dada.
    """

    # Palabras clave por maestro para routing automático
    ROUTING_KEYWORDS = {
        "ARCAN": ["diseño", "marca", "logo", "brand", "ui", "ux", "interfaz", "visual", "illustración", "imagen", "color", "tipografía", "wireframe", "mockup", "estética", "arte", "creativo", "persona", "cRO", "conversión"],
        "ORION": ["investigación", "investigar", "estudio", "datos", "estadística", "encuesta", "literature", "evidencia", "análisis", "historia", "narrativa", "psicología", "antropología", "geografía", " síntesis", "paper", "académico", "científico", "tendencia", "mercado"],
        "NEXUS": ["código", "programar", "desarrollo", "software", "app", "web", "api", "database", "base de datos", "servidor", "frontend", "backend", "infraestructura", "devops", "deploy", "git", "python", "javascript", "react", "node", "docker", "kubernetes", "aws", "machine learning", "ai", "modelo", "llm", "prompt", "rag", "testing", "test", "bug", "error", "arquitectura"],
        "AURUM": ["finanza", "financiero", "contabilidad", "presupuesto", "inversión", "impuesto", "modelo financiero", "cash flow", "dcf", "lbo", "valuation", "facturación", "tesorería", "ganancia", "pérdida", "balance", "income statement", "tax", "payroll", "invoice"],
        "SENTINEL": ["seguridad", "pentesting", "pentest", "hacker", "vulnerabilidad", "exploit", "auditoría", "compliance", "soc2", "iso27001", "hipaa", "pci", "amenaza", "threat", "incident", "breach", "forensics", "secrets", "credentials", "injection", "xss", "csrf", "encryption"],
        "MERIDIAN": ["producto", "product management", "sprint", "agile", "scrum", "proyecto", "gestión", "priorización", "roadmap", "experimento", "a/b testing", "jira", "tarea", "workflow", "meeting", "reunión", "feedback", "métrica", "kpi"],
        "AGENCY": ["marketing", "venta", "contenido", "seo", "sem", "publicidad", "anuncio", "campaña", "email", "newsletter", "social media", "instagram", "linkedin", "tiktok", "twitter", "propuesta", "propuesta comercial", "lead", "prospecto", "cliente", "copywriting", "branding", "marca", "community", "growth", "engagement"],
        "HELIOS": ["mapa", "gis", "geoespacial", "geografía", "espacial", "coordenadas", "gps", "ubicación", "geocoding", "mapping", "drone", "satelital", "satellite", "cesium", "maplibre", "arcgis", "leaflet"],
        "CRONUS": ["juego", "game", "minecraft", "pokemon", "videojuego", "mecánica", "nivel", "economía virtual", "monetización", "jugador", "game design", "narrativa de juego"],
        "MNEMOS": ["salud", "health", "médico", "clínico", "hospital", "paciente", "memoria", "documentación", "legal", "abogado", "contrato", "compliance", "soporte", "customer service", "rrhh", "onboarding", "operaciones", "estrategia"],
        "CHAIN": ["blockchain", "crypto", "ethereum", "smart contract", "defi", "web3", "nft", "token", "solidity", "evm", "decentralized", "wallet", "transaction", "gas"],
        "FORTIS": ["pago", "payment", "checkout", "cobro", "mercado pago", "stripe", "suscripción", "subscription", "facturación electrónica", "afip", "invoice"],
        "TRADING": ["trading", "acción", "bolsa", "portfolio", "investment", "análisis técnico", "chart", "forex", "crypto-trading"],
    }

    @staticmethod
    def determinar_maestro(descripcion_tarea: str) -> dict:
        """Determina el agente maestro más adecuado para una tarea."""
        descripcion_lower = descripcion_tarea.lower()
        scores = {}

        for maestro, keywords in Orquestador.ROUTING_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in descripcion_lower)
            if score > 0:
                scores[maestro] = score

        if not scores:
            # Fallback: MNEMOS (memoria/organización general)
            return {
                "maestro": "MNEMOS",
                "confianza": 0.3,
                "razon": "No se encontraron palabras clave específicas — fallback a organización general",
            }

        mejor_maestro = max(scores, key=scores.get)
        confianza = min(scores[mejor_maestro] / len(Orquestador.ROUTING_KEYWORDS[mejor_maestro]), 1.0)

        return {
            "maestro": mejor_maestro,
            "confianza": confianza,
            "scores": scores,
            "razon": f"Match por palabras clave en dominio {AGENTES_MAESTROS.get(mejor_maestro, {}).get('dominio', mejor_maestro)}",
        }

    @staticmethod
    def determinar_especialista(descripcion_tarea: str, maestro: str = None) -> dict:
        """Determina el agente especializado más adecuado."""
        if maestro is None:
            resultado = Orquestador.determinar_maestro(descripcion_tarea)
            maestro = resultado["maestro"]

        # Buscar agentes especializados de ese maestro
        candidatos = {}
        for agente_id, agente in AGENTES_ESPECIALIZADOS.items():
            if agente["maestro"] == maestro:
                # Calcular score por capacidades
                capacidades = agente.get("capacidades", [])
                score = sum(1 for cap in capacidades if cap in descripcion_tarea.lower())
                score += sum(1 for kw in Orquestador.ROUTING_KEYWORDS.get(maestro, []) if kw in descripcion_tarea.lower()) * 0.5
                if score > 0:
                    candidatos[agente_id] = (score, agente)

        if not candidatos:
            return {
                "especialista": None,
                "maestro": maestro,
                "confianza": 0,
                "razon": f"No se encontró especialista para '{descripcion_tarea}' en {maestro}",
            }

        mejor_id = max(candidatos, key=lambda k: candidatos[k][0])
        mejor_agente = candidatos[mejor_id][1]

        return {
            "especialista": mejor_agente["nombre"],
            "id": mejor_id,
            "maestro": maestro,
            "capacidades": mejor_agente.get("capacidades", []),
            "confianza": min(candidatos[mejor_id][0] / 3, 1.0),
        }

    @staticmethod
    def ruta_completa(descripcion_tarea: str) -> dict:
        """Ruta completa: maestro + especialista + tipo de ejecución."""
        maestro_info = Orquestador.determinar_maestro(descripcion_tarea)
        especialista_info = Orquestador.determinar_especialista(descripcion_tarea, maestro_info["maestro"])

        maestro_data = AGENTES_MAESTROS.get(maestro_info["maestro"], {})

        return {
            "maestro": maestro_info["maestro"],
            "dominio": maestro_data.get("dominio", "Desconocido"),
            "especialista_recomendado": especialista_info.get("especialista"),
            "automatizable": maestro_data.get("automatizable", False),
            "ejecucion": "automatica" if maestro_data.get("automatizable", False) else "requiere_ia",
            "confianza": (maestro_info.get("confianza", 0) + especialista_info.get("confianza", 0)) / 2,
            "routing": maestro_data.get("routing", ""),
            "tarea_original": descripcion_tarea,
        }


# ============================================================================
# DETECTOR DE TAREAS — Pending Task Scanner
# ============================================================================

class DetectorTareas:
    """
    Escanea el ecosistema de proyectos y tareas,
    detecta pendientes y genera propuestas.
    """

    IGNORED_PROJECTS = ["pilates"]

    @staticmethod
    def read_markdown(path: Path) -> str:
        if path.exists():
            return path.read_text(encoding='utf-8')
        return ""

    @staticmethod
    def extract_tasks_from_plan(content: str) -> list:
        tasks = []
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('- [ ]') or line.startswith('- [x]'):
                done = line.startswith('- [x]')
                task_text = line[4:].strip()
                tasks.append({"text": task_text, "done": done})
        return tasks

    @staticmethod
    def extract_tasks_from_today(content: str) -> list:
        tasks = []
        lines = content.split('\n')
        in_completado = False
        for line in lines:
            if '## Completado' in line:
                in_completado = True
            if not in_completado and line.strip().startswith('- [ ]'):
                tasks.append(line.strip()[4:].strip())
        return tasks

    @staticmethod
    def detect_project_status(project_file: Path) -> dict:
        content = DetectorTareas.read_markdown(project_file)
        pending = []
        in_pending = False
        for line in content.split('\n'):
            if '## Pendiente' in line:
                in_pending = True
                continue
            if in_pending and line.startswith('## '):
                in_pending = False
            if in_pending and line.strip().startswith('- '):
                pending.append(line.strip()[2:])

        estado = "Desconocido"
        for line in content.split('\n'):
            if '**Estado:**' in line:
                estado = line.split('**Estado:**')[-1].strip()

        return {
            "name": project_file.stem,
            "file": str(project_file),
            "estado": estado,
            "pendiente": pending,
        }

    @staticmethod
    def detect_active_tasks() -> list:
        tasks = []
        if not ACTIVE_DIR.exists():
            return tasks

        for task_dir in sorted(ACTIVE_DIR.iterdir()):
            if not task_dir.is_dir():
                continue

            plan_file = task_dir / "task_plan.md"
            progress_file = task_dir / "progress.md"
            findings_file = task_dir / "findings.md"

            plan_content = DetectorTareas.read_markdown(plan_file)
            progress_content = DetectorTareas.read_markdown(progress_file)
            findings_content = DetectorTareas.read_markdown(findings_file)

            objetivo = ""
            for line in plan_content.split('\n'):
                if '**Objetivo:**' in line:
                    objetivo = line.split('**Objetivo:**')[-1].strip()
                    break

            estado = "Listo para empezar"
            for line in plan_content.split('\n'):
                if '**Estado:**' in line:
                    estado = line.split('**Estado:**')[-1].strip()
                    break

            plan_tasks = DetectorTareas.extract_tasks_from_plan(plan_content)
            completed = sum(1 for t in plan_tasks if t["done"])
            total = len(plan_tasks)

            last_progress = ""
            for line in progress_content.split('\n'):
                if '**Próximo paso:**' in line:
                    last_progress = line.split('**Próximo paso:**')[-1].strip()
                    break

            bloqueos = []
            if findings_content:
                for line in findings_content.split('\n'):
                    if 'bloqueo' in line.lower() or 'error' in line.lower() or 'falla' in line.lower():
                        bloqueos.append(line.strip())

            tasks.append({
                "name": task_dir.name,
                "objetivo": objetivo,
                "estado": estado,
                "plan_tasks": plan_tasks,
                "completed": completed,
                "total": total,
                "proximo_paso": last_progress,
                "bloqueos": bloqueos,
                "path": str(task_dir),
            })

        return tasks

    @staticmethod
    def detect_all() -> dict:
        """Detecta todo el ecosistema de tareas."""
        projects = []
        if PROJECTS_DIR.exists():
            for proj_file in sorted(PROJECTS_DIR.glob("*.md")):
                if proj_file.name == "PROJECTS.md":
                    continue
                if any(ig in proj_file.stem.lower() for ig in DetectorTareas.IGNORED_PROJECTS):
                    continue
                projects.append(DetectorTareas.detect_project_status(proj_file))

        active_tasks = DetectorTareas.detect_active_tasks()

        today_content = DetectorTareas.read_markdown(TODAY_FILE)
        today_tasks = DetectorTareas.extract_tasks_from_today(today_content)

        return {
            "timestamp": datetime.now().isoformat(),
            "proyectos": projects,
            "tareas_activas": active_tasks,
            "today_pendiente": today_tasks,
        }

    @staticmethod
    def generate_proposals(ecosystem: dict) -> list:
        proposals = []

        # Propuestas de tareas activas
        for task in ecosystem["tareas_activas"]:
            if task["estado"] == "Listo para empezar" and task["total"] > 0:
                for t in task["plan_tasks"]:
                    if not t["done"]:
                        proposals.append({
                            "tipo": "tarea_activa",
                            "id": f"{task['name']}-{t['text'][:30]}",
                            "proyecto": task["name"],
                            "tarea": t["text"],
                            "proximo_paso": task["proximo_paso"],
                            "bloqueos": task["bloqueos"],
                            "archivo": f"{task['path']}/task_plan.md",
                            "prioridad": "alta",
                        })
                        break

        # Propuestas de proyectos pendientes
        for proj in ecosystem["proyectos"]:
            for pendiente in proj["pendiente"]:
                proposals.append({
                    "tipo": "proyecto_pendiente",
                    "id": f"{proj['name']}-{pendiente[:30]}",
                    "proyecto": proj["name"],
                    "tarea": pendiente,
                    "estado_proyecto": proj["estado"],
                    "archivo": proj["file"],
                    "prioridad": "alta" if "alta" in str(proj).lower() else "media",
                })

        # Propuestas de TODAY.md
        for task in ecosystem["today_pendiente"]:
            proposals.append({
                "tipo": "today",
                "id": f"today-{task[:30]}",
                "tarea": task,
                "archivo": str(TODAY_FILE),
                "prioridad": "baja",
            })

        return proposals


# ============================================================================
# AUTO-EXECUTOR — Mechanical Task Executor
# ============================================================================

class AutoExecutor:
    """
    Ejecuta tareas mecánicas directamente.
    Tareas IA se encolan para el agente.
    """

    AUTO_PATTERNS = {
        "crear_directorio": {
            "pattern": r"crear\s+(?:carpeta|directorio)\s+(?:en\s+)?(.+)",
            "action": "mkdir",
        },
        "crear_archivo": {
            "pattern": r"crear\s+(?:archivo|file)\s+(?:en\s+)?(.+)",
            "action": "touch",
        },
        "instalar_paquete": {
            "pattern": r"instalar\s+(?:paquete\s+)?(\S+)",
            "action": "pip_install",
        },
        "copiar_archivo": {
            "pattern": r"copiar\s+(.+?)\s+a\s+(.+)",
            "action": "cp",
        },
        "mover_archivo": {
            "pattern": r"mover\s+(.+?)\s+a\s+(.+)",
            "action": "mv",
        },
        "eliminar_archivo": {
            "pattern": r"eliminar\s+(?:archivo\s+)?(.+)",
            "action": "rm",
        },
        "git_commit": {
            "pattern": r"git\s+commit\s+(?:mensaje\s+)?(.+)",
            "action": "git_commit",
        },
        "git_push": {
            "pattern": r"git\s+push",
            "action": "git_push",
        },
        "ejecutar_comando": {
            "pattern": r"ejecutar\s+(.+)",
            "action": "run_cmd",
        },
        "crear_markdown": {
            "pattern": r"crear\s+(?:markdown|md)\s+(.+)",
            "action": "create_md",
        },
    }

    @staticmethod
    def load_state() -> dict:
        if STATE_FILE.exists():
            return json.loads(STATE_FILE.read_text(encoding='utf-8'))
        return {"executed": [], "last_run": None, "total_executed": 0}

    @staticmethod
    def save_state(state: dict):
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding='utf-8')

    @staticmethod
    def log_execution(task: str, result: str, success: bool):
        log_file = LOG_DIR / f"executor-{datetime.now().strftime('%Y%m%d')}.log"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().isoformat()
        status = "✅" if success else "❌"
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {status} {task}\n  └─ {result}\n")

    @staticmethod
    def execute_action(action: str, params: dict) -> tuple:
        if action == "mkdir":
            path = Path(params.get("path", "").strip())
            if not path.is_absolute():
                path = HOME / path
            try:
                path.mkdir(parents=True, exist_ok=True)
                return True, f"Carpeta creada: {path}"
            except Exception as e:
                return False, f"Error creando carpeta: {e}"

        elif action == "touch":
            path = Path(params.get("path", "").strip())
            if not path.is_absolute():
                path = HOME / path
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.touch(exist_ok=True)
                return True, f"Archivo creado: {path}"
            except Exception as e:
                return False, f"Error creando archivo: {e}"

        elif action == "create_md":
            path = Path(params.get("path", "").strip())
            if not path.is_absolute():
                path = HOME / path
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                if not path.exists():
                    path.write_text(f"# {path.stem}\n\n", encoding='utf-8')
                return True, f"Markdown creado: {path}"
            except Exception as e:
                return False, f"Error creando markdown: {e}"

        elif action == "pip_install":
            package = params.get("package", "").strip()
            try:
                result = subprocess.run(["pip", "install", package], capture_output=True, text=True, timeout=120)
                if result.returncode == 0:
                    return True, f"Paquete instalado: {package}"
                else:
                    return False, f"Error instalando: {result.stderr}"
            except Exception as e:
                return False, f"Error en pip install: {e}"

        elif action == "cp":
            src = Path(params.get("src", "").strip())
            dst = Path(params.get("dst", "").strip())
            if not src.is_absolute():
                src = HOME / src
            if not dst.is_absolute():
                dst = HOME / dst
            try:
                shutil.copy2(src, dst)
                return True, f"Copiado: {src} -> {dst}"
            except Exception as e:
                return False, f"Error copiando: {e}"

        elif action == "mv":
            src = Path(params.get("src", "").strip())
            dst = Path(params.get("dst", "").strip())
            if not src.is_absolute():
                src = HOME / src
            if not dst.is_absolute():
                dst = HOME / dst
            try:
                shutil.move(str(src), str(dst))
                return True, f"Movido: {src} -> {dst}"
            except Exception as e:
                return False, f"Error moviendo: {e}"

        elif action == "rm":
            path = Path(params.get("path", "").strip())
            if not path.is_absolute():
                path = HOME / path
            try:
                if path.is_file():
                    path.unlink()
                elif path.is_dir():
                    shutil.rmtree(path)
                return True, f"Eliminado: {path}"
            except Exception as e:
                return False, f"Error eliminando: {e}"

        elif action == "git_commit":
            message = params.get("message", "auto commit").strip()
            try:
                subprocess.run(["git", "add", "."], capture_output=True, cwd=str(HOME))
                result = subprocess.run(["git", "commit", "-m", message], capture_output=True, text=True, cwd=str(HOME), timeout=30)
                if result.returncode == 0:
                    return True, f"Commit realizado: {message}"
                else:
                    return False, f"Error en commit: {result.stderr}"
            except Exception as e:
                return False, f"Error en git commit: {e}"

        elif action == "git_push":
            try:
                result = subprocess.run(["git", "push"], capture_output=True, text=True, cwd=str(HOME), timeout=60)
                if result.returncode == 0:
                    return True, "Push realizado"
                else:
                    return False, f"Error en push: {result.stderr}"
            except Exception as e:
                return False, f"Error en git push: {e}"

        elif action == "run_cmd":
            cmd = params.get("cmd", "").strip()
            try:
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=120, cwd=str(HOME))
                if result.returncode == 0:
                    return True, f"Comando ejecutado: {cmd}"
                else:
                    return False, f"Error en comando: {result.stderr}"
            except subprocess.TimeoutExpired:
                return False, f"Timeout ejecutando: {cmd}"
            except Exception as e:
                return False, f"Error ejecutando comando: {e}"

        return False, f"Acción desconocida: {action}"

    @staticmethod
    def try_auto_execute(task_text: str) -> tuple:
        for pattern_name, pattern_info in AutoExecutor.AUTO_PATTERNS.items():
            match = re.search(pattern_info["pattern"], task_text.lower())
            if match:
                action = pattern_info["action"]
                groups = match.groups()
                params = {}

                if action == "mkdir":
                    params["path"] = groups[0] if groups else ""
                elif action in ("touch", "create_md", "rm"):
                    params["path"] = groups[0] if groups else ""
                elif action == "pip_install":
                    params["package"] = groups[0] if groups else ""
                elif action in ("cp", "mv"):
                    params["src"] = groups[0] if len(groups) > 0 else ""
                    params["dst"] = groups[1] if len(groups) > 1 else ""
                elif action == "git_commit":
                    params["message"] = groups[0] if groups else "auto commit"
                elif action == "run_cmd":
                    params["cmd"] = groups[0] if groups else ""

                success, result = AutoExecutor.execute_action(action, params)
                return True, result, success

        return False, None, False

    @staticmethod
    def add_to_queue(task: dict):
        queue = []
        if QUEUE_FILE.exists():
            queue = json.loads(QUEUE_FILE.read_text(encoding='utf-8'))

        for item in queue:
            if item.get("text") == task.get("text"):
                return

        queue.append({
            "text": task.get("text"),
            "source": task.get("source", ""),
            "type": task.get("type", "general"),
            "added_at": datetime.now().isoformat(),
        })

        QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)
        QUEUE_FILE.write_text(json.dumps(queue, indent=2, ensure_ascii=False), encoding='utf-8')


# ============================================================================
# STATE MANAGER — Persistencia sin re-ejecución
# ============================================================================

class StateManager:
    """Mantiene estado para no re-ejecutar lo ya hecho."""

    @staticmethod
    def load() -> dict:
        if STATE_FILE.exists():
            return json.loads(STATE_FILE.read_text(encoding='utf-8'))
        return {"executed": [], "last_run": None, "total_executed": 0}

    @staticmethod
    def save(state: dict):
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding='utf-8')

    @staticmethod
    def is_executed(task_id: str) -> bool:
        state = StateManager.load()
        return task_id in state.get("executed", [])

    @staticmethod
    def mark_executed(task_id: str):
        state = StateManager.load()
        if task_id not in state["executed"]:
            state["executed"].append(task_id)
            state["total_executed"] = state.get("total_executed", 0) + 1
            StateManager.save(state)


# ============================================================================
# QUEUE MANAGER — Cola de tareas IA
# ============================================================================

class QueueManager:
    """Gestión de cola de tareas que requieren IA."""

    @staticmethod
    def load() -> list:
        if QUEUE_FILE.exists():
            return json.loads(QUEUE_FILE.read_text(encoding='utf-8'))
        return []

    @staticmethod
    def save(queue: list):
        QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)
        QUEUE_FILE.write_text(json.dumps(queue, indent=2, ensure_ascii=False), encoding='utf-8')

    @staticmethod
    def add(task: dict):
        queue = QueueManager.load()
        for item in queue:
            if item.get("text") == task.get("text"):
                return
        queue.append({
            "text": task.get("text"),
            "source": task.get("source", ""),
            "type": task.get("type", "general"),
            "added_at": datetime.now().isoformat(),
        })
        QueueManager.save(queue)

    @staticmethod
    def get_pending() -> list:
        return QueueManager.load()

    @staticmethod
    def dequeue(task_text: str):
        queue = QueueManager.load()
        queue = [q for q in queue if q.get("text") != task_text]
        QueueManager.save(queue)


# ============================================================================
# MAIN — CLI Interface
# ============================================================================

def main():
    import sys

    args = sys.argv[1:]

    if "--maestros" in args:
        print("\n🎯 AGENTES MAESTROS (63 nodos de dominio)\n")
        for id, m in AGENTES_MAESTROS.items():
            print(f"  {m['emoji']} {id} — {m['dominio']} ({m['division']})")
            print(f"     Automatizable: {'✅' if m['automatizable'] else '❌'}")
            print(f"     Routing: {m['routing']}")
            print()
        return

    if "--agents" in args:
        print("\n🧠 AGENTES ESPECIALIZADOS (243 nodos hoja)\n")
        for id, a in sorted(AGENTES_ESPECIALIZADOS.items(), key=lambda x: x[1]['maestro']):
            caps = ", ".join(a.get("capacidades", [])[:4])
            print(f"  [{a['maestro']}] {a['nombre']} — {caps}")
        print(f"\nTotal: {len(AGENTES_ESPECIALIZADOS)} agentes especializados cargados")
        return

    if "--route" in args:
        tarea = " ".join(args[1:])
        if not tarea:
            print("Uso: python3 neural_fellowship.py --route 'tarea a enrutar'")
            return
        print(f"\n🔀 ROUTING: {tarea}\n")
        ruta = Orquestador.ruta_completa(tarea)
        print(f"  Maestro: {ruta['maestro']} ({ruta['dominio']})")
        print(f"  Especialista: {ruta['especialista_recomendado']}")
        print(f"  Ejecución: {ruta['ejecucion']}")
        print(f"  Confianza: {ruta['confianza']:.0%}")
        print(f"  {ruta['routing']}")
        return

    if "--auto" in args:
        print("\n🤖 AUTO-EXECUTOR — Escaneo automático\n")
        executor = AutoExecutor()
        state = AutoExecutor.load_state()
        state["last_run"] = datetime.now().isoformat()

        # Escanear tareas
        tasks = []
        if PROJECTS_DIR.exists():
            for proj_file in sorted(PROJECTS_DIR.glob("*.md")):
                if proj_file.name == "PROJECTS.md":
                    continue
                if any(ig in proj_file.stem.lower() for ig in DetectorTareas.IGNORED_PROJECTS):
                    continue
                content = proj_file.read_text(encoding='utf-8')
                in_pending = False
                for line in content.split('\n'):
                    if '## Pendiente' in line:
                        in_pending = True
                        continue
                    if in_pending and line.startswith('## '):
                        in_pending = False
                    if in_pending and line.strip().startswith('- '):
                        task_text = line.strip()[2:].strip()
                        if task_text:
                            tasks.append({"text": task_text, "source": f"_projects/{proj_file.name}", "type": "pendiente"})

        if ACTIVE_DIR.exists():
            for task_dir in sorted(ACTIVE_DIR.iterdir()):
                if not task_dir.is_dir():
                    continue
                plan_file = task_dir / "task_plan.md"
                if not plan_file.exists():
                    continue
                content = plan_file.read_text(encoding='utf-8')
                for line in content.split('\n'):
                    if line.strip().startswith('- [ ]'):
                        task_text = line.strip()[4:].strip()
                        if task_text:
                            tasks.append({"text": task_text, "source": f"_active/{task_dir.name}/task_plan.md", "type": "tarea_activa"})

        auto_results = []
        queued_count = 0

        for task in tasks:
            task_id = f"{task['source']}:{task['text'][:50]}"
            if StateManager.is_executed(task_id):
                continue

            auto_exec, result, success = AutoExecutor.try_auto_execute(task["text"])
            if auto_exec:
                AutoExecutor.log_execution(task["text"], result, success)
                if success:
                    StateManager.mark_executed(task_id)
                    auto_results.append({"task": task["text"], "result": result, "success": True})
                else:
                    AutoExecutor.add_to_queue(task)
                    queued_count += 1
                    auto_results.append({"task": task["text"], "result": f"Fallo: {result}", "success": False})
            else:
                AutoExecutor.add_to_queue(task)
                queued_count += 1

        state = StateManager.load()
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"📊 Tareas escaneadas: {len(tasks)}")
        print(f"✅ Auto-ejecutadas: {len([r for r in auto_results if r['success']])}")
        print(f"📋 En cola para agente: {queued_count}")

        if auto_results:
            print("\n🔧 Ejecutadas:")
            for r in auto_results:
                status = "✅" if r["success"] else "❌"
                print(f"  {status} {r['task']}")

        if queued_count > 0:
            queue = QueueManager.get_pending()
            print(f"\n📋 En cola ({len(queue)}):")
            for i, item in enumerate(queue[:10], 1):
                print(f"  {i}. {item['text']}")

        AutoExecutor.save_state(state)
        return

    # Default: scan + propuestas
    print("\n🔍 NEURAL FELLOWSHIP — Escaneo del ecosistema\n")

    ecosystem = DetectorTareas.detect_all()
    proposals = DetectorTareas.generate_proposals(ecosystem)

    print(f"📅 Detectado: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"📊 Propuestas: {len(proposals)}")

    alta = [p for p in proposals if p.get("prioridad") == "alta"]
    media = [p for p in proposals if p.get("prioridad") == "media"]
    baja = [p for p in proposals if p.get("prioridad") == "baja"]

    if alta:
        print("\n🔴 PRIORIDAD ALTA")
        for i, p in enumerate(alta, 1):
            print(f"  {i}. [{p['tipo']}] {p['tarea']}")

    if media:
        print("\n🟡 PRIORIDAD MEDIA")
        for i, p in enumerate(media, len(alta)+1):
            print(f"  {i}. [{p['tipo']}] {p['tarea']}")

    if baja:
        print("\n🟢 PRIORIDAD BAJA")
        for i, p in enumerate(baja, len(alta)+len(media)+1):
            print(f"  {i}. [{p['tipo']}] {p['tarea']}")

    print("\n💡 Escribí números para ejecutar, 'TODO' para todas, o 'NINGUNA'")

    # Guardar reporte
    report_path = KNOWLEDGE_DIR / "_active" / "_detection_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps({
        "ecosystem": ecosystem,
        "proposals": proposals,
    }, indent=2, ensure_ascii=False), encoding='utf-8')


if __name__ == "__main__":
    main()
