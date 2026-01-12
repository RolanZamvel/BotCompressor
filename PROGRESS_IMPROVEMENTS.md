# Mejoras en la Captura de Progreso de Compresión

## Resumen
Se ha implementado un sistema de captura de progreso en tiempo real para la compresión de videos y audios, utilizando una técnica similar a la proporcionada en el ejemplo de FFmpeg con Python.

## Cambios Realizados

### 1. Interfaz `IMediaCompressor` (`src/interfaces/media_compressor.py`)
- **Cambio**: Agregado parámetro opcional `progress_callback` al método `compress`
- **Tipo**: `Optional[Callable[[int], None]]` - Recibe un porcentaje de progreso (0-100)
- **Propósito**: Permitir que los compresores notifiquen el progreso durante la compresión

### 2. VideoCompressor (`src/services/video_compressor.py`)
- **Cambio Principal**: Implementación de captura de progreso en tiempo real desde FFmpeg
- **Nuevo Método**: `_compress_with_progress()`
  - Usa `subprocess.Popen` en lugar de `subprocess.run`
  - Captura `stderr` línea por línea mientras FFmpeg se ejecuta
  - Analiza la salida de FFmpeg con expresiones regulares:
    - `Duration: (\d{2}):(\d{2}):(\d{2}\.\d+)` - Extrae duración total del video
    - `time=(\d{2}):(\d{2}):(\d{2}\.\d+)` - Extrae tiempo actual procesado
  - Calcula porcentaje de progreso: `(current_time / duration) * 100`
  - Llama al callback de progreso con cada actualización
- **Beneficios**:
  - Progreso en tiempo real basado en el tiempo de video procesado
  - Mayor precisión que el estimado anterior
  - Detección de errores y advertencias de FFmpeg

### 3. AudioCompressor (`src/services/audio_compressor.py`)
- **Cambio Principal**: Implementación de simulación de progreso para audio
- **Nuevo Método**: `_simulate_progress()`
  - Ejecuta en un thread separado (daemon thread)
  - Simula progreso basándose en el tiempo transcurrido de compresión
  - Estima tiempo de compresión: `duration * 0.5` segundos por segundo de audio
  - Notifica progreso cada 0.5 segundos mientras haya cambios significativos
- **Nota**: Pydub no proporciona un callback nativo, por lo que se usa una estimación basada en tiempo

### 4. CompressionOrchestrator (`src/services/compression_orchestrator.py`)
- **Cambio**: Integración del callback de progreso con el sistema de notificaciones
- **Nueva Función**: `compression_progress_callback()`
  - Convierte el porcentaje de progreso (0-100) a bytes
  - Usa el tamaño del archivo original (`file_size_bytes`) para la conversión
  - Llama a `update_compression_progress()` del notificador
- **Integración**: El callback se pasa a ambos compresores (video y audio)

## Comparación con el Ejemplo Proporcionado

### Similitudes:
- ✅ Uso de `subprocess.Popen` para ejecutar FFmpeg
- ✅ Captura de `stderr` línea por línea
- ✅ Análisis de `Duration` para obtener duración total
- ✅ Análisis de `time=` para obtener tiempo actual
- ✅ Cálculo de porcentaje: `(current / total) * 100`
- ✅ Callback de progreso en tiempo real

### Adaptaciones:
- 🔧 Integración con el sistema existente de notificaciones de Telegram
- 🔧 Callback opcional para mantener compatibilidad backward
- 🔧 Manejo de errores robusto con logging
- 🔧 Implementación también para compresión de audio
- 🔧 Conversión de porcentaje a bytes para el notificador

## Flujo de Datos del Progreso

```
FFmpeg (stderr)
    ↓
VideoCompressor._compress_with_progress()
    ↓
Analiza líneas con regex (Duration y time)
    ↓
Calcula progreso (0-100)
    ↓
progress_callback(percent)
    ↓
CompressionOrchestrator.compression_progress_callback()
    ↓
Convierte a bytes: (percent / 100) * total_bytes
    ↓
ProgressNotifier.update_compression_progress(bytes)
    ↓
Actualiza mensaje en Telegram con barra de progreso
```

## Mejoras en la Experiencia del Usuario

### Antes:
- Solo se mostraba un mensaje "Comprimiendo archivo..." sin progreso
- El usuario no sabía cuánto tiempo faltaba
- No había indicación visual del avance

### Después:
- 📊 Barra de progreso visual en tiempo real
- ⏱️ Estimación de tiempo restante
- 🔢 Porcentaje exacto de avance
- 💬 Actualizaciones cada segundo en el mensaje de Telegram
- 🎯 Progreso basado en el tiempo real procesado por FFmpeg

## Logs de Debug

Se han añadido logs para monitorear el progreso:

```
⏱️ [COMPRESIÓN] Tiempo: 15.3s, Progreso: 45.2% (12345678/27345678 bytes)
✅ [COMPRESIÓN] Procediendo con actualización...
🔄 [COMPRESIÓN] Intentando editar mensaje...
✅ [COMPRESIÓN] Mensaje editado exitosamente
```

## Compatibilidad

- ✅ **Backward Compatible**: El callback es opcional, el código existente sigue funcionando
- ✅ **No requiere cambios en bot.py**: El orquestador maneja la integración
- ✅ **Mantiene SOLID**: Principios de diseño preservados
- ✅ **Thread-safe**: El audio usa un thread daemon separado para no bloquear

## Pruebas Recomendadas

1. **Video corto** (< 10s): Verificar progreso rápido
2. **Video largo** (> 1min): Verificar actualizaciones consistentes
3. **Audio corto**: Verificar simulación de progreso
4. **Audio largo**: Verificar estimación de tiempo
5. **Video corrupto**: Verificar manejo de errores de FFmpeg

## Archivos Modificados

1. `src/interfaces/media_compressor.py` - Interfaz actualizada
2. `src/services/video_compressor.py` - Captura de progreso de FFmpeg
3. `src/services/audio_compressor.py` - Simulación de progreso
4. `src/services/compression_orchestrator.py` - Integración del callback

## Notas Técnicas

### FFmpeg Progress Format
FFmpeg escribe el progreso en stderr con formato:
```
Duration: 00:01:30.45, start: 0.000000, bitrate: 2500 kb/s
...
frame=  123 fps= 25 q=28.0 size=    1234kB time=00:00:05.20 bitrate=1945.2kbits/s speed=1.04x
```

### Regex Patterns
- **Duración**: `r'Duration: (\d{2}):(\d{2}):(\d{2}\.\d+)'`
- **Tiempo**: `r'time=(\d{2}):(\d{2}):(\d{2}\.\d+)'`

## Conclusión

La implementación proporciona una mejora significativa en la experiencia del usuario al ofrecer visibilidad en tiempo real del progreso de compresión, manteniendo la compatibilidad con el código existente y siguiendo las mejores prácticas de diseño.
