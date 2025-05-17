# 🧠 Greeum v0.5.0

<p align="center">
  <a href="../../README.md">🇰🇷 한국어</a> |
  <a href="README_EN.md">🇺🇸 English</a> |
  <a href="README_ZH.md">🇨🇳 中文</a> |
  <a href="README_JP.md">🇯🇵 日本語</a> |
  <a href="README_ES.md">🇪🇸 Español</a> |
  <a href="README_DE.md">🇩🇪 Deutsch</a> |
  <a href="README_FR.md">🇫🇷 Français</a>
</p>

Sistema de Gestión de Memoria Independiente de LLM Multilingüe

## 📌 Descripción General

Greeum es un sistema de memoria independiente de LLM basado en la arquitectura RAG (Generación Aumentada por Recuperación, Retrieval-Augmented Generation). Implementa componentes clave de RAG, incluyendo almacenamiento y recuperación de información (block_manager.py), gestión de memorias relacionadas (cache_manager.py) y aumento de prompts (prompt_wrapper.py) para generar respuestas más precisas y contextualmente relevantes.

**Greeum** (pronunciado: gri-eum) es un **módulo de memoria universal** que puede conectarse a cualquier LLM (Modelo de Lenguaje Grande) y proporciona las siguientes características:
- Seguimiento a largo plazo de expresiones, objetivos, emociones e intenciones del usuario
- Recuperación de recuerdos relacionados con el contexto actual
- Reconocimiento y procesamiento de expresiones temporales en entornos multilingües
- Funciona como una "IA con memoria"

El nombre "Greeum" está inspirado en la palabra coreana "그리움" (añoranza/reminiscencia), capturando perfectamente la esencia del sistema de memoria.

## 🔑 Características Principales

- **Memoria a Largo Plazo tipo Blockchain (LTM)**: Almacenamiento de memoria basado en bloques con inmutabilidad
- **Memoria a Corto Plazo basada en TTL (STM)**: Gestión eficiente de información temporalmente importante
- **Relevancia Semántica**: Sistema de recuperación de memoria basado en palabras clave/etiquetas/vectores
- **Caché de Puntos de Referencia**: Recuperación automática de recuerdos relacionados con el contexto actual
- **Compositor de Prompts**: Generación automática de prompts de LLM con recuerdos relevantes
- **Razonador Temporal**: Reconocimiento avanzado de expresiones temporales en entornos multilingües
- **Soporte Multilingüe**: Detección y procesamiento automático de idiomas para coreano, inglés, etc.
- **Protocolo de Control de Modelo**: Soporte de integración de herramientas externas para Cursor, Unity, Discord, etc. a través del paquete separado [GreeumMCP](https://github.com/DryRainEnt/GreeumMCP)

## ⚙️ Instalación

1. Clonar el repositorio
   ```bash
   git clone https://github.com/DryRainEnt/Greeum.git
   cd Greeum
   ```

2. Instalar dependencias
   ```bash
   pip install -r requirements.txt
   ```

## 🧪 Uso

### Interfaz de Línea de Comandos

```bash
# Añadir memoria a largo plazo
python cli/memory_cli.py add -c "Comencé un nuevo proyecto y es realmente emocionante"

# Buscar recuerdos por palabras clave
python cli/memory_cli.py search -k "proyecto,emocionante"

# Buscar recuerdos por expresión temporal
python cli/memory_cli.py search-time -q "¿Qué hice hace 3 días?" -l "es"

# Añadir memoria a corto plazo
python cli/memory_cli.py stm "El clima hoy está agradable"

# Obtener memorias a corto plazo
python cli/memory_cli.py get-stm

# Generar prompt
python cli/memory_cli.py prompt -i "¿Cómo va el proyecto?"
```

### Servidor REST API

```bash
# Ejecutar servidor API
python api/memory_api.py
```

Interfaz web: http://localhost:5000

Endpoints de API:
- GET `/api/v1/health` - Comprobación de salud
- GET `/api/v1/blocks` - Listar bloques
- POST `/api/v1/blocks` - Añadir bloque
- GET `/api/v1/search?keywords=keyword1,keyword2` - Búsqueda por palabras clave
- GET `/api/v1/search/time?query=yesterday&language=en` - Búsqueda por expresión temporal
- GET, POST, DELETE `/api/v1/stm` - Gestionar memorias a corto plazo
- POST `/api/v1/prompt` - Generar prompt
- GET `/api/v1/verify` - Verificar integridad de blockchain

### Biblioteca Python

```python
from greeum import BlockManager, STMManager, CacheManager, PromptWrapper
from greeum.text_utils import process_user_input
from greeum.temporal_reasoner import TemporalReasoner

# Procesar entrada del usuario
user_input = "Comencé un nuevo proyecto y es realmente emocionante"
processed = process_user_input(user_input)

# Almacenar memoria con gestor de bloques
block_manager = BlockManager()
block = block_manager.add_block(
    context=processed["context"],
    keywords=processed["keywords"],
    tags=processed["tags"],
    embedding=processed["embedding"],
    importance=processed["importance"]
)

# Búsqueda basada en tiempo (multilingüe)
temporal_reasoner = TemporalReasoner(db_manager=block_manager, default_language="auto")
time_query = "¿Qué hice hace 3 días?"
time_results = temporal_reasoner.search_by_time_reference(time_query)

# Generar prompt
cache_manager = CacheManager(block_manager=block_manager)
prompt_wrapper = PromptWrapper(cache_manager=cache_manager)

user_question = "¿Cómo va el proyecto?"
prompt = prompt_wrapper.compose_prompt(user_question)

# Pasar a LLM
# llm_response = call_your_llm(prompt)
```

## 🧱 Arquitectura

```
greeum/
├── greeum/                # Biblioteca principal
│   ├── block_manager.py    # Gestión de memoria a largo plazo
│   ├── stm_manager.py      # Gestión de memoria a corto plazo
│   ├── cache_manager.py    # Caché de puntos de referencia
│   ├── prompt_wrapper.py   # Composición de prompts
│   ├── text_utils.py       # Utilidades de procesamiento de texto
│   ├── temporal_reasoner.py # Razonamiento temporal
│   ├── embedding_models.py  # Integración de modelos de embedding
├── api/                   # Interfaz REST API
├── cli/                   # Herramientas de línea de comandos
├── data/                  # Directorio de almacenamiento de datos
├── tests/                 # Suite de pruebas
```

## Reglas de Gestión de Ramas

- **main**: Rama de versión estable de lanzamiento
- **dev**: Rama de desarrollo de características principales (fusionada a main después del desarrollo y pruebas)
- **test-collect**: Rama de recopilación de métricas de rendimiento y datos de pruebas A/B

## 📊 Pruebas de Rendimiento

Greeum realiza pruebas de rendimiento en las siguientes áreas:

### T-GEN-001: Tasa de Aumento de Especificidad de Respuesta
- Medición de la mejora de calidad de respuesta al usar la memoria Greeum
- Confirmación de mejora de calidad promedio del 18.6%
- Aumento de 4.2 inclusiones de información específica

### T-MEM-002: Latencia de Búsqueda de Memoria
- Medición de mejora de velocidad de búsqueda a través de caché de puntos de referencia
- Confirmación de mejora de velocidad promedio de 5.04 veces
- Hasta 8.67 veces de mejora de velocidad para más de 1,000 bloques de memoria

### T-API-001: Eficiencia de Llamadas API
- Medición de la tasa de reducción de re-preguntas debido a la provisión de contexto basada en memoria
- Confirmación de reducción del 78.2% en la necesidad de re-preguntas
- Efecto de reducción de costos debido a la disminución de llamadas API

## 📊 Estructura de Bloque de Memoria

```json
{
  "block_index": 143,
  "timestamp": "2025-05-08T01:02:33",
  "context": "Comencé un nuevo proyecto y es realmente emocionante",
  "keywords": ["proyecto", "comenzar", "emocionante"],
  "tags": ["positivo", "comienzo", "motivación"],
  "embedding": [0.131, 0.847, ...],
  "importance": 0.91,
  "hash": "...",
  "prev_hash": "..."
}
```

## 🔤 Idiomas Soportados

Greeum soporta el reconocimiento de expresiones temporales en los siguientes idiomas:
- 🇰🇷 Coreano: Soporte básico para expresiones temporales coreanas (어제, 지난주, 3일 전, etc.)
- 🇺🇸 Inglés: Soporte completo para formatos temporales en inglés (yesterday, 3 days ago, etc.)
- 🇪🇸 Español: Soporte para expresiones temporales en español (ayer, hace tres días, etc.)
- 🌐 Detección automática: Detecta automáticamente el idioma y lo procesa en consecuencia

## 🔍 Ejemplos de Razonamiento Temporal

```python
# Coreano
result = evaluate_temporal_query("3일 전에 뭐 했어?", language="ko")
# Valor de retorno: {detected: True, language: "ko", best_ref: {term: "3일 전"}}

# Inglés
result = evaluate_temporal_query("What did I do 3 days ago?", language="en")
# Valor de retorno: {detected: True, language: "en", best_ref: {term: "3 days ago"}}

# Español
result = evaluate_temporal_query("¿Qué hice hace 3 días?", language="es")
# Valor de retorno: {detected: True, language: "es", best_ref: {term: "hace 3 días"}}

# Detección automática
result = evaluate_temporal_query("What happened yesterday?")
# Valor de retorno: {detected: True, language: "en", best_ref: {term: "yesterday"}}
```

## 🔧 Planes de Expansión del Proyecto

- **Protocolo de Control de Modelo**: Consulta el repositorio [GreeumMCP](https://github.com/DryRainEnt/GreeumMCP) para soporte MCP - un paquete separado que permite a Greeum conectarse con herramientas como Cursor, Unity, Discord, etc.
- **Soporte Multilingüe Mejorado**: Soporte adicional para japonés, chino, español, etc.
- **Embeddings Mejorados**: Integración de modelos de embedding reales (p.ej., sentence-transformers)
- **Extracción de Palabras Clave Mejorada**: Implementación de extracción de palabras clave específica del idioma
- **Integración en la Nube**: Adición de backends de base de datos (SQLite, MongoDB, etc.)
- **Procesamiento Distribuido**: Implementación de procesamiento distribuido para gestión de memoria a gran escala

## 🌐 Sitio Web

Visita el sitio web: [greeum.app](https://greeum.app)

## 📄 Licencia

Licencia MIT

## 👥 Contribución

¡Todas las contribuciones son bienvenidas, incluyendo informes de errores, sugerencias de características, solicitudes de extracción, etc.!

## 📱 Contacto

Correo electrónico: playtart@play-t.art 