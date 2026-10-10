# Integración de Neural Fellowship con Hermes Runtime

Este documento explica cómo integrar y ejecutar Neural Fellowship con el runtime real de Hermes tanto en Termux (Android) como en PC.

## Requisitos Previos

- Python 3.8+
- Git
- Acceso a internet para descargar dependencias
- (Opcional) Termux (para Android) o sistema Linux/Windows/macOS

## Instalación en Termux (Android)

### 1. Instalar dependencias
```bash
pkg update && pkg upgrade
pkg install python git curl
```

### 2. Clonar el repositorio
```bash
cd ~
git clone https://github.com/ConocimientoGlobal/Agentes-Maestros-.git
cd Agentes-Maestros-
```

### 3. Instalar dependencias del proyecto
```bash
pip install -r requirements.txt
```

### 4. Configurar Hermes
```bash
# Instalar Hermes Agent (si no está disponible)
pip install hermes-agent
```

## Instalación en PC (Linux/macOS/Windows)

### 1. Clonar el repositorio
```bash
git clone https://github.com/ConocimientoGlobal/Agentes-Maestros-.git
cd Agentes-Maestros-
```

### 2. Crear entorno virtual (recomendado)
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# o
venv\Scripts\activate     # Windows
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Instalar Hermes Agent
```bash
pip install hermes-agent
```

## Configuración Básica

### 1. Verificar instalación de Hermes
```bash
hermes --version
```

### 2. Configurar el entorno de Neural Fellowship
```bash
# Ejecutar inicialización del sistema (si aplica)
python3 neural_fellowship.py --init
```

### 3. Probar integración
```bash
# Ejecutar prueba de integración
python3 -c "
from orquestar import ejecutar
resultado = ejecutar('¿Cuál es la capital de Francia?')
print('Master seleccionado:', resultado['master'])
print('Handler usado:', resultado.get('handler'))
"
```

## Uso Básico

### 1. Ejecutar Neural Fellowship
```bash
python3 neural_fellowship.py
```

### 2. Ejecutar una tarea con integración Hermes
```bash
# Tareas que pueden delegarse al runtime de Hermes:
# - Escribir un script complejo
# - Realizar cálculos avanzados  
# - Buscar información
# - Procesar datos

python3 -c "
from orquestar import ejecutar
# Delega tareas abiertas al runtime real de Hermes
tarea = 'Escribe un script en Python que calcule el promedio de una lista de números'
resultado = ejecutar(tarea)
print('Resultado:', resultado)
"
```

## Notas Importantes

- **Ejecución en Termux**: El ejecutable `hermes` debe estar en el PATH
- **Permisos**: Asegúrate de tener permisos de ejecución en directorios de trabajo
- **Integración**: La nueva estrategia `hermes_agent` permite delegar tareas complejas al runtime real de Hermes
- **Feedback**: Todos los resultados se registran en `learned_lessons.json` automáticamente

## Desarrollo

Para desarrollar nuevas estrategias de ejecución:
```python
# Crear nuevos ejecutores en ejecutor_real.py o ejecutor_hermes.py
# Agregar a EXECUTION_STRATEGIES en orquestar.py
```

## Problemas Comunes

### Error: 'hermes' no encontrado
- Verifica que `hermes` esté instalado y en el PATH
- En Termux: `pkg install hermes-agent`

### Error de permisos 
- Ejecutar con `chmod +x` en archivos necesarios
- Verificar permisos de directorio de trabajo

### Problemas de dependencias
- Reinstalar con: `pip install -r requirements.txt --force-reinstall`

## Pruebas de Integración

Ejecutar prueba simple para verificar conexión:
```bash
python3 -c "
from orquestar import ejecutar
print('Probando integración Hermes...')
try:
    resultado = ejecutar('Escribe un breve saludo en Python')
    print('✓ Integración ok:', resultado.get('handler', 'no handler'))
except Exception as e:
    print('✗ Error:', e)
"
```

## Documentación Adicional

- [Hermes Agent Docs](https://hermes-agent.nousresearch.com/docs)
- [Neural Fellowship Design](docs/neural_fellowship.md)