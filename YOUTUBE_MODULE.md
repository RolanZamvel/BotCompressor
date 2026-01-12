# YouTube Download Module

## Overview

Este módulo permite a los usuarios descargar videos de YouTube directamente en el bot de Telegram y luego comprimirlos, siguiendo estrictamente los principios SOLID de diseño de software.

## Arquitectura (SOLID)

### Single Responsibility Principle (SRP)

Cada clase tiene una única responsabilidad:

- **IYouTubeDownloader/YouTubeDownloader**: Solo gestiona la descarga de videos
- **IProgressTracker/YouTubeProgressNotifier**: Solo notifica el progreso al usuario
- **YouTubeInfoExtractor**: Solo extrae y formatea información del video
- **IDownloadStrategy/Estrategias**: Solo definen cómo descargar videos

### Open/Closed Principle (OCP)

El módulo está abierto para extensión pero cerrado para modificación:

- Nuevas estrategias de descarga se pueden agregar sin modificar el código existente
- Solo heredan de `IDownloadStrategy` e implementan los métodos requeridos

### Liskov Substitution Principle (LSP)

Las subclases pueden sustituir a sus superclases:

- `BestQualityStrategy`, `OptimalQualityStrategy`, `EfficientQualityStrategy`, `AudioOnlyStrategy` pueden ser usadas donde se espera `IDownloadStrategy`

### Interface Segregation Principle (ISP)

Las interfaces son específicas y enfocadas:

- `IYouTubeDownloader` solo define métodos de descarga
- `IProgressTracker` solo define métodos de seguimiento de progreso
- Los clientes no dependen de métodos que no usan

### Dependency Inversion Principle (DIP)

Los módulos dependen de abstracciones:

- `bot.py` depende de `IYouTubeDownloader` en lugar de la implementación concreta
- `YouTubeDownloader` inyecta dependencias a través del constructor
- Fácil cambiar la implementación sin afectar el código que la usa

## Estructura de Archivos

```
src/
├── interfaces/
│   ├── youtube_downloader.py      # Interface IYouTubeDownloader
│   └── progress_tracker.py         # Interface IProgressTracker
├── services/
│   ├── youtube_downloader.py       # Implementación de IYouTubeDownloader
│   ├── youtube_info_extractor.py   # Extracción de información
│   └── youtube_progress_notifier.py # Notificación de progreso
└── strategies/
    └── download_strategy.py        # Estrategias de descarga
```

## Flujo de Trabajo

1. **Detección**: El usuario envía un enlace de YouTube
   ```
   https://www.youtube.com/watch?v=VIDEO_ID
   ```

2. **Análisis**: El bot extrae información del video
   - Título
   - Duración
   - Tamaño original
   - Canal

3. **Selección**: El usuario elige la calidad de descarga
   - 🎬 Mejor calidad
   - ⚖️ Calidad óptima
   - 📊 Eficiente
   - 🎵 Solo audio

4. **Descarga**: El video se descarga con progreso en tiempo real
   - Barra de progreso visual
   - Porcentaje completado
   - Velocidad de descarga
   - Tiempo restante

5. **Compresión**: El usuario elige la compresión
   - 📊 Comprimir (menor tamaño)
   - 🎬 Mantener calidad (mayor tamaño)

6. **Entrega**: El video comprimido se envía al usuario

## Estrategias de Descarga

### BestQualityStrategy
Descarga en la mejor calidad disponible.
- Formato: `best[ext=mp4]/best`
- Uso: Cuando la calidad es más importante que el tamaño

### OptimalQualityStrategy
Balance entre calidad y tamaño (recomendado).
- Formato: `bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best`
- Uso: Para la mayoría de los casos

### EfficientQualityStrategy
Prioriza tamaño reducido.
- Formato: `bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]`
- Uso: Cuando el ancho de banda es limitado

### AudioOnlyStrategy
Descarga solo el audio en formato MP3.
- Formato: `bestaudio[ext=m4a]/bestaudio/best`
- Uso: Para podcasts, música, etc.

## Uso en el Bot

### Handlers en bot.py

1. **handle_text**: Detecta URLs de YouTube
   ```python
   @app.on_message(filters.text)
   def handle_text(client, message):
       # Detecta y procesa enlaces de YouTube
   ```

2. **handle_youtube_download_selection**: Muestra información del video
   ```python
   def handle_youtube_download_selection(client, callback_query):
       # Extrae y muestra info del video
   ```

3. **handle_youtube_strategy_selection**: Descarga con la estrategia elegida
   ```python
   def handle_youtube_strategy_selection(client, callback_query):
       # Descarga el video con progreso
   ```

4. **process_youtube_video_with_quality**: Comprime el video descargado
   ```python
   def process_youtube_video_with_quality(client, callback_query, quality_option):
       # Comprime y envía el video
   ```

## Ejemplo de Uso

```python
from src.services import YouTubeDownloader, YouTubeProgressNotifier
from src.strategies import OptimalQualityStrategy

# Crear downloader
downloader = YouTubeDownloader(download_dir='downloads')

# Crear notifier
notifier = YouTubeProgressNotifier(message)

# Seleccionar estrategia
strategy = OptimalQualityStrategy()

# Descargar con progreso
video_path = downloader.download_with_strategy(
    url="https://www.youtube.com/watch?v=VIDEO_ID",
    strategy=strategy,
    progress_callback=notifier.update
)

# El video ahora está listo para ser comprimido
```

## Dependencias

- `yt-dlp>=2024.1.1`: Motor de descarga de YouTube
- `pyrogram`: Cliente de Telegram

## Configuración

Las configuraciones relevantes están en `config.py`:

```python
# Extensiones de archivos temporales
TEMP_FILE_SUFFIX_VIDEO = ".mp4"
```

## Manejo de Errores

El módulo incluye manejo robusto de errores:

1. **Extracción de información**: Si falla, notifica al usuario
2. **Descarga**: Si falla, notifica el error específico
3. **Progreso**: Actualiza continuamente el progreso al usuario
4. **Cancelación**: Permite cancelar en cualquier momento
5. **Limpieza**: Elimina archivos temporales automáticamente

## Limitaciones

1. **Videos largos**: Videos muy largos pueden tomar mucho tiempo en descargar
2. **Tamaño máximo**: Telegram limita el tamaño de archivos a 2GB
3. **Videos privados**: Solo funciona con videos públicos
4. **Edad restringida**: Videos con restricción de edad pueden fallar

## Extensiones Futuras

El diseño SOLID facilita extensiones:

1. **Nuevas estrategias**: Agregar `IDownloadStrategy` para otros casos
2. **Otros sitios**: Extender para Vimeo, TikTok, etc.
3. **Caché**: Implementar caché de videos descargados
4. **Cola**: Implementar cola de descargas para múltiples usuarios
5. **Cookies**: Soporte para videos restringidos usando cookies

## Testing

Para probar el módulo:

```python
from src.services import YouTubeDownloader

downloader = YouTubeDownloader()

# Probar extracción de información
info = downloader.get_video_info("https://www.youtube.com/watch?v=VIDEO_ID")
print(f"Título: {info['title']}")
print(f"Duración: {info['duration_str']}")

# Probar obtención de formatos
formats = downloader.get_available_urls("https://www.youtube.com/watch?v=VIDEO_ID")
print(f"Formatos disponibles: {len(formats)}")
```

## Soporte

Para problemas o preguntas:
1. Revisa los logs del bot con `/log`
2. Verifica que `yt-dlp` esté instalado correctamente
3. Asegúrate de tener conexión a internet estable
