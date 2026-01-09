<<<<<<< HEAD
# BotCompressor Web Dashboard

Sistema web de control y monitoreo para el bot BotCompressor de Telegram.

## 📋 Descripción

Este proyecto es una migración completa del bot BotCompressor (un bot de Telegram para compresión de audio y video) a una aplicación web moderna con dashboard de control en tiempo real.

### Características Principales

- ✅ **Dashboard Web Moderno**: Interfaz con Next.js 15, TypeScript y shadcn/ui
- ✅ **Control del Bot**: Iniciar, detener y reiniciar el bot desde el dashboard
- ✅ **Monitoreo en Tiempo Real**: Logs en tiempo real vía WebSocket
- ✅ **API REST Completa**: Endpoints para control del bot
- ✅ **Optimizado**: TgCrypto instalado para máxima velocidad
- ✅ **Diseño Responsive**: Funciona en todos los dispositivos
- ✅ **Logs Exportables**: Descarga de logs como archivo .txt

## 🏗️ Arquitectura

```
/home/z/my-project/
├── src/app/                          # Frontend Next.js 15
│   ├── page.tsx                      # Dashboard principal
│   └── api/bot/                     # API Routes
│       ├── status/route.ts             # Estado del bot
│       ├── start/route.ts              # Iniciar bot
│       ├── stop/route.ts               # Detener bot
│       ├── logs/route.ts               # Obtener logs
│       └── restart/route.ts            # Reiniciar bot
├── src/components/bot-dashboard/       # Componentes del dashboard
│   ├── StatusCard.tsx                 # Estado y controles
│   ├── LogViewer.tsx                  # Visualizador de logs
│   ├── StatsCard.tsx                  # Estadísticas
│   └── InfoCard.tsx                  # Información del bot
├── src/hooks/                        # Custom hooks
│   └── useBotMonitor.ts              # Hook de monitoreo
└── mini-services/bot-service/        # Servidor del bot
    ├── index.ts                       # Controlador Node.js/Bun
    ├── venv/                          # Entorno virtual Python
    └── src/                            # Código del bot Python
        ├── bot.py                      # Bot principal
        ├── config.py                    # Configuración
        ├── services/                    # Servicios de compresión
        ├── repositories/                 # Repositorios
        ├── interfaces/                   # Interfaces
        └── strategies/                   # Estrategias de compresión
```

## 🚀 Tecnologías Utilizadas

### Frontend
- **Framework**: Next.js 15 con App Router
- **Lenguaje**: TypeScript 5
- **Estyling**: Tailwind CSS 4
- **UI Components**: shadcn/ui (New York style)
- **Icons**: Lucide React
- **State Management**: React Hooks (useState, useCallback, useEffect)
- **Real-time Communication**: Socket.io Client

### Backend (Bot Service)
- **Runtime**: Node.js/Bun
- **Server**: Express.js
- **WebSocket**: Socket.io
- **Bot Language**: Python 3.12
- **Bot Framework**: Pyrogram
- **Compression**: FFmpeg (video), Pydub (audio)
- **Optimization**: TgCrypto (speedup)

### DevOps
- **Virtual Environment**: Python venv
- **Hot Reload**: Bun --hot
- **Proxy**: Caddy gateway para múltiples puertos

## 📦 Instalación

### Requisitos Previos
- Bun runtime
- Python 3.12+
- FFmpeg (para compresión de video)
- Node.js/Bun

### Pasos de Instalación

1. **Clonar el repositorio**
   ```bash
   git clone <repository-url>
   cd my-project
   ```

2. **Instalar dependencias del frontend**
   ```bash
   bun install
   ```

3. **Configurar entorno virtual del bot**
   ```bash
   cd mini-services/bot-service
   python3 -m venv venv
   ./venv/bin/pip install -r requirements.txt
   ./venv/bin/pip install TgCrypto
   ```

4. **Configurar credenciales del bot**
   ```bash
   # Editar mini-services/bot-service/src/config.py
   API_ID = 'your_api_id'
   API_HASH = 'your_api_hash'
   API_TOKEN = 'your_bot_token'
   ```

## 🎯 Uso

### Iniciar Servicios

#### Servidor Next.js (Frontend)
```bash
bun run dev
```
Acceder a: http://localhost:3000

#### Bot Service (Backend)
```bash
cd mini-services/bot-service
bun run dev
```
Se ejecuta en: http://localhost:3002

### Usar el Dashboard

1. **Acceder al Dashboard**
   - Abre el navegador en http://localhost:3000
   - Verás el dashboard con 4 cards principales

2. **Controlar el Bot**
   - **Start**: Inicia el bot de Telegram
   - **Stop**: Detiene el bot
   - **Restart**: Reinicia el bot

3. **Monitorear**
   - Observa el estado en tiempo real
   - Ver logs en la sección "Live Logs"
   - Usa "Export" para descargar logs

## 🔧 Configuración

### Configuración del Bot (Python)

Archivo: `mini-services/bot-service/src/config.py`

```python
# API Credentials
API_ID = 'your_api_id'
API_HASH = 'your_api_hash'
API_TOKEN = 'your_bot_token'

# Audio compression settings
AUDIO_BITRATE = "32k"
AUDIO_FORMAT = "mp3"
AUDIO_CHANNELS = 1
AUDIO_SAMPLE_RATE = 44100

# Video compression settings
VIDEO_SCALE = "640:360"
VIDEO_FPS = 24
VIDEO_CODEC = "libx265"
VIDEO_BITRATE = "100k"
VIDEO_CRF = 30
VIDEO_PRESET = "ultrafast"
VIDEO_PIXEL_FORMAT = "yuv420p"
VIDEO_PROFILE = "main"
VIDEO_AUDIO_CODEC = "aac"
VIDEO_AUDIO_BITRATE = "64k"
VIDEO_AUDIO_CHANNELS = 1
VIDEO_AUDIO_SAMPLE_RATE = 44100
```

## 📡 API Endpoints

### Bot Service (Port 3002)

- `GET /health` - Health check del servicio
- `GET /status` - Estado actual del bot
- `POST /start` - Iniciar el bot
- `POST /stop` - Detener el bot
- `GET /logs?limit=N` - Obtener últimos N logs
- `POST /restart` - Reiniciar el bot

### WebSocket Events (Port 3002)

- `connect` - Cliente conectado
- `disconnect` - Cliente desconectado
- `status` - Actualización de estado del bot
- `log` - Nuevo log del bot
- `logs` - Array de logs

### Next.js API Routes (Port 3000)

- `GET /api/bot/status` - Proxy para estado del bot
- `POST /api/bot/start` - Proxy para iniciar bot
- `POST /api/bot/stop` - Proxy para detener bot
- `GET /api/bot/logs` - Proxy para obtener logs
- `POST /api/bot/restart` - Proxy para reiniciar bot

## 🎨 Componentes del Dashboard

### StatusCard
Muestra el estado actual del bot con:
- Badge de estado (Stopped/Starting/Running/Error)
- PID y uptime del bot
- Botones Start, Stop, Restart
- Visualización de errores

### LogViewer
Visualiza logs del bot en tiempo real:
- Scroll area con overflow
- Colores según tipo de log (info, error, success)
- Botón de exportar logs a archivo

### StatsCard
Muestra estadísticas del bot:
- Total Logs
- Active Sessions
- Uptime
- Status del sistema

### InfoCard
Información sobre el bot:
- Descripción del BotCompressor
- Capacidades de compresión de audio
- Capacidades de compresión de video

## 🔒 Seguridad

- ⚠️ **Credenciales sensibles** en `config.py` deben protegerse
- **No incluir tokens** en commits públicos
- Usar variables de entorno para producción

## 🐛 Problemas Conocidos y Soluciones

### Error: ModuleNotFoundError: No module named 'pyrogram'
**Solución**: Instalar dependencias en el venv
```bash
cd mini-services/bot-service
./venv/bin/pip install pyrogram pydub
```

### Error: ImportError: attempted relative import beyond top-level package
**Solución**: Los imports relativos `..` fueron corregidos a imports absolutos
- Cambiado `from src.services import` a `from services import`
- Aplicado en todos los módulos Python

### Advertencia: TgCrypto is missing!
**Solución**: Instalar TgCrypto para optimización de velocidad
```bash
./venv/bin/pip install TgCrypto
```

## 📝 Documentación de Desarrollo

Para detalles completos del proceso de desarrollo y migración, ver:
- `worklog.md` - Registro completo de todas las tareas y decisiones
- Documentación in-line en el código fuente

## 🎓 Historial del Proyecto

### Migración del Repositorio Original
- **Fuente**: https://github.com/RolanZamvel/BotCompressor
- **Fecha**: 2026-01-09
- **Objetivo**: Migrar bot Python a aplicación web con dashboard de control

### Etapas de Desarrollo

1. **Análisis del repositorio original**
   - Clonado y revisión del código Python
   - Identificación de componentes principales
   - Análisis de arquitectura SOLID

2. **Creación del mini servicio**
   - Implementación de controlador Node.js/Bun
   - Setup de WebSocket para comunicación en tiempo real
   - Sistema de gestión de procesos del bot

3. **Desarrollo del frontend**
   - Dashboard con Next.js 15 y TypeScript
   - Componentes shadcn/ui para UI moderna
   - Hook personalizado para monitoreo

4. **Integración y optimización**
   - API Routes como proxy al bot service
   - Instalación de dependencias Python
   - Instalación de TgCrypto para optimización

5. **Corrección de errores**
   - Corrección de imports relativos en Python
   - Configuración de entorno virtual
   - Resolución de problemas de puerto

## 🔄 Flujo de Trabajo

1. **Usuario** accede al dashboard web (http://localhost:3000)
2. **Dashboard** muestra estado actual del bot
3. **Usuario** hace click en "Start" para iniciar el bot
4. **Next.js API** llama al bot service (http://localhost:3002)
5. **Bot Service** inicia el proceso Python del bot
6. **Bot** intenta conectarse a Telegram
7. **WebSocket** emite logs en tiempo real
8. **Dashboard** muestra logs y actualiza estado

## 📊 Estadísticas del Proyecto

- **Líneas de código TypeScript**: ~800
- **Líneas de código Python**: ~1,500
- **Componentes React**: 4
- **API Routes**: 5
- **Endpoints Bot Service**: 6
- **WebSocket Events**: 5

## 🚀 Despliegue

Para desplegar en producción:

1. **Configurar variables de entorno**
2. **Compilar Next.js**: `bun run build`
3. **Iniciar servidor de producción**
4. **Ejecutar bot service**: `bun start` (en mini-services/bot-service)
5. **Configurar reverse proxy** (nginx, Caddy, etc.)

## 📄 Licencia

Este proyecto mantiene la licencia original del BotCompressor.

## 👥 Contribuciones

Las contribuciones son bienvenidas. Por favor:
1. Fork el repositorio
2. Crea una rama para tu feature
3. Commit tus cambios
4. Push a la rama
5. Abre un Pull Request

## 📧 Mantenimiento

### Monitoreo del Sistema
- Verificar logs del dashboard
- Monitorear estado del bot
- Verificar consumo de recursos

### Actualizaciones
- Actualizar dependencias regularmente
- Mantener TgCrypto actualizado
- Revisar actualizaciones de Next.js

---

**Desarrollado por**: Z.ai Code Assistant
**Fecha**: 2026-01-09
**Versión**: 1.0.0
=======
# 🎧 CompressBot 🎥

![Screenshot from 2024-08-10 09-12-16](https://github.com/user-attachments/assets/935c3079-5da2-4bf9-9362-c922b410d1a8)

Welcome to **CompressBot**—your all-in-one Telegram bot for compressing audio and video files with ease! 🚀

## 🌟 Features

- **Compress Audio 🎧**: Convert and compress your audio files to a smaller size while maintaining good quality.
- **Compress Video 🎥**: Reduce the size of your video files with efficient compression without significant loss in quality.
- **User-Friendly**: Simple commands and easy-to-use interface.
- **Fast Processing ⚡**: Get your compressed files quickly.

## 🛠 Installation

Follow these steps to set up the bot locally:

1. **Clone the repository**:
   ```bash
   git clone https://github.com/RolanZamvel/BotCompressor.git
   cd BotCompressor
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**:
   - Open the `config.py` file in the root directory.
   - Add your credentials:
     ```python
     API_ID = 'api_id'
     API_HASH = 'api_hash'
     API_TOKEN = 'bot_token'
     ```

4. **Run the bot**:
   ```bash
   python bot.py
   ```

## 📦 Requirements

- Python 3.7+
- [Pyrogram](https://docs.pyrogram.org/) - For Telegram bot API interaction
- [Pydub](https://pydub.com/) - For audio processing
- [FFmpeg](https://ffmpeg.org/) - For video compression

## 🚀 Usage

1. **Start the bot** by sending the `/start` command.
2. **Choose** between compressing audio or video files.
3. **Upload** your media file.
4. **Receive** the compressed file instantly!

## 🛠 Configuration

You can adjust the compression parameters in the script to suit your needs:

- **Audio Compression**: Adjust the `bitrate` and `format` in the `handle_audio` function.
- **Video Compression**: Modify the FFmpeg command in the `handle_video` function to tweak video resolution, bitrate, etc.

## 🐛 Issues

If you encounter any issues or have suggestions, please feel free to open an [issue](https://github.com/superhexa/CompressBot/issues) or submit a pull request.

## 📜 License

This project is licensed under the MIT License—see the [LICENSE](LICENSE) file for details.

---

**Enjoy CompressBot and make your media sharing easier! 🎉**
>>>>>>> 5e5b789adca7794e64690a9f4c9bb00058460b52
