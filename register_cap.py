#!/usr/bin/env python3
"""Registrar capacidad gestion-emocional para prueba de fuego."""
from hermes_bridge import register_maestro, build_maestro

# Create maestro for emotional management
maestro_spec = build_maestro(
    'gestion-emocional',
    'MNEMOS',
    'Gestión emocional: manejo de ansiedad, estrés y bienestar mental',
    {'tipo': 'salud-mental', 'dominio': 'bienestar'}
)
register_maestro('GESTION-EMOCIONAL', maestro_spec)
print('Registered GESTION-EMOCIONAL maestro')