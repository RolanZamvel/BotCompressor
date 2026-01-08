# SOLID Principles Implementation

Este documento describe la refactorización del proyecto BotCompressor siguiendo los principios SOLID.

## Resumen

El código original violaba varios principios SOLID, haciéndolo difícil de mantener, escalar y probar. Esta refactorización aplica todos los principios SOLID para crear una arquitectura limpia y mantenible.

## Principios Aplicados

### 1. Single Responsibility Principle (SRP)

**Problema Original:**
- `bot.py` tenía múltiples responsabilidades en handlers de 180+ líneas
- Manejo de archivos, compresión, notificaciones, todo en un solo lugar

**Solución Implementada:**
- `AudioCompressor`: Solo comprime audio
- `VideoCompressor`: Solo comprime video
- `FileManager`: Solo maneja archivos temporales
- `MessageTracker`: Solo rastrea mensajes procesados
- `ProgressNotifier`: Solo notifica progreso al usuario
- `CompressionOrchestrator`: Solo coordina el workflow

**Beneficio:** Cada clase tiene una razón única para cambiar, facilitando mantenimiento.

### 2. Open/Closed Principle (OCP)

**Problema Original:**
- Añadir nuevas opciones de calidad requería modificar handlers existentes
- Estrategias de compresión hardcoded en el código

**Solución Implementada:**
- Patrón Strategy para opciones de calidad:
  - `ICompressionStrategy`: Interfaz base
  - `QualityPreservationStrategy`: Mantener alta calidad
  - `SizeReductionStrategy`: Priorizar reducción de tamaño
- Nuevas estrategias pueden añadirse sin modificar código existente

**Beneficio:** El sistema está abierto para extensión pero cerrado para modificación.

### 3. Liskov Substitution Principle (LSP)

**Problema Original:**
- No existía jerarquía de clases
- Código duplicado entre handlers de audio y video

**Solución Implementada:**
- `IMediaCompressor`: Interfaz base para compresores
- `AudioCompressor` y `VideoCompressor` son intercambiables
- Ambos implementan el mismo contrato: `compress()` y `get_output_format()`

**Beneficio:** Los compresores pueden sustituirse sin romper el funcionamiento.

### 4. Interface Segregation Principle (ISP)

**Problema Original:**
- No existían interfaces
- Todo dependía de implementaciones concretas

**Solución Implementada:**
Interfaces pequeñas y específicas:
- `IMediaCompressor`: Solo operaciones de compresión
- `IFileManager`: Solo operaciones de archivos
- `IMessageTracker`: Solo tracking de mensajes
- `IProgressNotifier`: Solo notificaciones

**Beneficio:** Los clientes dependen solo de los métodos que usan.

### 5. Dependency Inversion Principle (DIP)

**Problema Original:**
- Dependencias directas a Pyrogram, FFmpeg, Pydub
- Acoplamiento alto con implementaciones concretas

**Solución Implementada:**
- Módulos de alto nivel (bot.py) dependen de abstracciones (interfaces)
- Módulos de bajo nivel (services) implementan abstracciones
- Dependencias inyectadas en constructores:
  ```python
  orchestrator = CompressionOrchestrator(
      compressor=compressor,
      file_manager=file_manager,
      message_tracker=message_tracker,
      notifier=notifier
  )
  ```

**Beneficio:** Fácil cambiar implementaciones y hacer tests.

## Nueva Arquitectura

```
src/
├── interfaces/              # Abstracciones (DIP, ISP)
│   ├── media_compressor.py      # IMediaCompressor
│   ├── file_handler.py           # IFileManager
│   └── message_handler.py        # IMessageTracker, IProgressNotifier
│
├── services/               # Implementaciones (SRP)
│   ├── audio_compressor.py       # Compresión de audio
│   ├── video_compressor.py       # Compresión de video
│   ├── file_manager.py          # Manejo de archivos
│   ├── progress_notification.py # Notificaciones
│   └── compression_orchestrator.py # Coordinador (DIP)
│
├── strategies/             # Patrones extensibles (OCP)
│   ├── compression_strategy.py    # ICompressionStrategy
│   ├── quality_preservation.py   # Estrategia alta calidad
│   └── size_reduction.py         # Estrategia tamaño mínimo
│
└── repositories/           # Tracking de datos (SRP)
    └── message_tracker.py       # Tracking de mensajes
```

## Comparación de Código

### Antes (216 líneas en bot.py)
```python
@app.on_message(filters.voice | filters.audio)
def handle_audio(client, message):
    downloaded_file = None
    compressed_file = None
    backup_file = None
    status_message = None

    if message.id in processed_messages:
        return

    try:
        processed_messages.add(message.id)
        status_message = message.reply_text("📥 **Descargando archivo**...")
        file_id = message.voice.file_id if message.voice else message.audio.file_id
        downloaded_file = client.download_media(file_id)
        # ... 100+ líneas más de lógica mezclada
```

### Después (25 líneas en bot.py)
```python
@app.on_message(filters.voice | filters.audio)
def handle_audio(client, message):
    try:
        compressor = AudioCompressor()
        notifier = ProgressNotifier(message)

        orchestrator = CompressionOrchestrator(
            compressor=compressor,
            file_manager=file_manager,
            message_tracker=message_tracker,
            notifier=notifier
        )

        file_id = message.voice.file_id if message.voice else message.audio.file_id
        orchestrator.process(message, file_id, is_animation=False)
    except Exception as e:
        message.reply_text(f"❌ **Error al procesar audio:** {str(e)}")
```

## Beneficios Obtenidos

### Mantenibilidad
- Cada clase tiene una responsabilidad única
- Fácil encontrar dónde hacer cambios
- Reducción drástica de código duplicado

### Extensibilidad
- Añadir nuevos formatos: Crear nuevo compresor implementando IMediaCompressor
- Añadir nuevas estrategias: Crear nueva clase implementando ICompressionStrategy
- Sin modificar código existente

### Testabilidad
- Dependencias pueden mockearse fácilmente
- Testing unitario de cada componente
- Tests de integración con mocks

### Escalabilidad
- Arquitectura limpia soporta nuevas features
- Fácil añadir compresores para otros formatos (imágenes, documentos)
- Fácil añadir nuevas estrategias de compresión
- Fácil cambiar notificaciones (email, webhook, etc.)

## Ejemplo de Extensión

### Añadir nueva estrategia de compresión

```python
# src/strategies/custom_strategy.py
from typing import Dict
from .compression_strategy import ICompressionStrategy

class CustomStrategy(ICompressionStrategy):
    def get_parameters(self) -> Dict:
        return {
            "crf": 23,
            "bitrate": "1M",
            "preset": "medium",
            "quality": "medium"
        }

    def get_description(self) -> str:
        return "🎯 **Balance calidad/tamaño**"

    def get_estimated_time_factor(self) -> float:
        return 1.2
```

Uso en bot.py:
```python
from src.strategies import CustomStrategy

# ...
strategy = CustomStrategy()
compressor = VideoCompressor(strategy=strategy)
# ...
```

**Sin modificar código existente!**

## Migración desde bot_original.py

El archivo `bot_original.py` es un backup de la implementación anterior.

Cambios principales en `bot.py`:
- Líneas reducidas de ~216 a ~250 (más legible)
- Lógica de negocio movida a servicios especializados
- Inyección de dependencias en lugar de hardcoded
- Manejo de errores mejorado y consistente

**No hay cambios en funcionalidad visible al usuario.**

## Próximos Pasos

1. **Testing**: Añadir tests unitarios para cada servicio
2. **Logging**: Implementar logging estructurado
3. **Config**: Externalizar configuración (usando patrones Builder/Factory)
4. **Queues**: Implementar cola de procesamiento para archivos grandes
5. **Monitoring**: Añadir métricas y monitoreo
6. **API REST**: Exponer endpoints para integración con otros servicios

## Recursos

- [SOLID Principles - Wikipedia](https://en.wikipedia.org/wiki/SOLID)
- [Clean Architecture - Robert C. Martin](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Python Design Patterns](https://refactoring.guru/design-patterns/python)
