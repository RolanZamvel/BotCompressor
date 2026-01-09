# 🎧 BotCompressor Web Dashboard

![Version](https://img.shields.io/badge/version-1.1.0-blue)
![Next.js](https://img.shields.io/badge/Next.js-15.3-black)
![TypeScript](https://img.shields.io/badge/TypeScript-5-blue)
![License](https://img.shields.io/badge/license-MIT-green)

Sistema web de control y monitoreo para el bot BotCompressor de Telegram con dashboard moderno y despliegue optimizado.

## 📋 Descripción

Este proyecto es una migración completa del bot BotCompressor (un bot de Telegram para compresión de audio y video) a una aplicación web moderna con dashboard de control en tiempo real. **El bot se inicia automáticamente junto con el dashboard para optimizar el despliegue.**

### Características Principales

- ✅ **Dashboard Web Moderno**: Interfaz con Next.js 15, TypeScript y shadcn/ui
- ✅ **Control del Bot**: Iniciar, detener y reiniciar el bot desde el dashboard
- ✅ **Monitoreo en Tiempo Real**: Logs en tiempo real vía WebSocket
- ✅ **API REST Completa**: Endpoints para control del bot
- ✅ **Auto-inicio del Bot**: El bot se inicia automáticamente al arrancar los servicios
- ✅ **Optimizado**: TgCrypto instalado para máxima velocidad
- ✅ **Diseño Responsive**: Funciona en todos los dispositivos
- ✅ **Logs Exportables**: Descarga de logs como archivo .txt
- ✅ **Single Command Start**: Un solo comando inicia ambos servicios

## 🏗️ Arquitectura

```
/home/z/my-project/
├── start-all.ts                         # Script de inicio principal
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
    ├── index.ts                       # Controlador Node.js/Bun (auto-inicio)
    ├── venv/                          # Entorno virtual Python
    └── src/                            # Código del bot Python
        ├── bot.py                      # Bot principal
        ├── config.py                    # Configuración
        ├── services/                    # Servicios de compresión
        ├── repositories/                 # Repositorios
        ├── interfaces/                   # Interfaces
        └── strategies/                   # Estrategias de compresión
```

## 🚀 Instalación y Uso Rápido

### Opción 1: Modo Desarrollador (Auto-inicio)

```bash
# 1. Clonar el repositorio
git clone https://github.com/RolanZamvel/BotCompressor.git
cd BotCompressor

# 2. Instalar dependencias
bun install

# 3. Instalar dependencias del bot
cd mini-services/bot-service
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
./venv/bin/pip install TgCrypto

# 4. Configurar credenciales del bot
# Editar mini-services/bot-service/src/config.py
# Agregar tus credenciales de Telegram

# 5. ¡INICIAR TODO CON UN SOLO COMANDO! 🚀
cd ../
bun run dev:services
```

✅ **¡Listo!** Ambos servicios se inician automáticamente:
- 📱 Dashboard web: http://localhost:3000
- 🤖 Bot service: http://localhost:3002 (bot se inicia solo después de 2 seg)

---

### Opción 2: Iniciar Servicios por Separado

#### Iniciar solo el Dashboard (Frontend)
```bash
bun run dev
```
Acceder a: http://localhost:3000

#### Iniciar solo el Bot Service (Backend)
```bash
cd mini-services/bot-service
bun run dev
```
Se ejecuta en: http://localhost:3002 (bot auto-inicia después de 2 seg)

---

## 🎯 Modo Despliegue Optimizado

El proyecto está configurado para facilitar el despliegue en producción:

### Configuración Actual

1. **Bot Service Auto-inicio**: El bot se inicia automáticamente 2 segundos después de arrancar el bot-service
2. **Single Command**: `bun run dev:services` inicia todo con un solo comando
3. **Graceful Shutdown**: Ctrl+C detiene ambos servicios ordenadamente
4. **Error Handling**: Si un servicio falla, ambos se detienen

### Despliegue en Producción

#### Opción A: PM2 (Recomendado)

```bash
# Instalar PM2 globalmente
npm install -g pm2

# Iniciar ambos servicios
cd /home/z/my-project
pm2 start start-all.ts --name bot-dashboard --interpreter bun

# Verificar estado
pm2 status
pm2 logs bot-dashboard

# Detener
pm2 stop bot-dashboard
```

#### Opción B: Systemd (Para servidores Linux)

Crear archivo `/etc/systemd/system/bot-dashboard.service`:

```ini
[Unit]
Description=BotCompressor Dashboard
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/home/z/my-project
ExecStart=/usr/bin/bun run dev:services
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Iniciar el servicio:
```bash
sudo systemctl daemon-reload
sudo systemctl enable bot-dashboard
sudo systemctl start bot-dashboard
sudo systemctl status bot-dashboard
```

#### Opción C: Docker (Opcional)

Crear `Dockerfile`:

```dockerfile
FROM oven/bun:1

WORKDIR /app

# Instalar dependencias
COPY package.json bun.lock ./
RUN bun install

# Instalar dependencias del bot
COPY mini-services/bot-service/requirements.txt mini-services/
COPY mini-services/bot-service/src mini-services/bot-service/src
RUN cd mini-services && python3 -m venv venv && \
    venv/bin/pip install -r requirements.txt && \
    venv/bin/pip install TgCrypto

# Copiar scripts
COPY start-all.ts ./

# Exponer puertos
EXPOSE 3000 3002

# Iniciar servicios
CMD ["bun", "run", "start-all.ts"]
```

Construir y ejecutar:
```bash
docker build -t botcompressor-dashboard .
docker run -p 3000:3000 -p 3002:3002 botcompressor-dashboard
```

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

### Scripts Disponibles

- `bun run dev` - Inicia solo el frontend Next.js
- `bun run dev:services` - **RECOMENDADO** - Inicia ambos servicios con auto-inicio
- `bun run start:frontend` - Inicia solo el frontend
- `bun run start:bot-service` - Inicia solo el bot service
- `bun run build` - Compila el frontend para producción
- `bun run start` - Inicia el servidor de producción

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
- **TgCrypto** instalado para encriptación eficiente

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

### El bot no se inicia automáticamente

**Verificar**: Asegúrate de usar `bun run dev:services` en lugar de iniciar los servicios por separado

## 📝 Documentación de Desarrollo

Para detalles completos del proceso de desarrollo y migración, ver:
- `worklog.md` - Registro completo de todas las tareas y decisiones
- Documentación inline en el código fuente

## 🎓 Guía de Despliegue Rápido

### Para Desarrolladores Locales

```bash
# 1. Clonar y preparar
git clone https://github.com/RolanZamvel/BotCompressor.git
cd BotCompressor
bun install
cd mini-services/bot-service
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
./venv/bin/pip install TgCrypto
cd ../

# 2. Iniciar todo
bun run dev:services

# 3. ¡Listo! Ambos servicios corriendo automáticamente
```

### Para Producción con PM2

```bash
# Instalar PM2
npm install -g pm2

# Iniciar
pm2 start start-all.ts --name bot-dashboard --interpreter bun

# Monitorear
pm2 status
pm2 logs bot-dashboard --lines 100
```

### Para Servidores Linux (Systemd)

```bash
# Crear archivo de servicio
sudo nano /etc/systemd/system/bot-dashboard.service

# Copiar configuración (ver sección "Opción B: Systemd")

# Iniciar servicio
sudo systemctl daemon-reload
sudo systemctl start bot-dashboard
sudo systemctl enable bot-dashboard  # Auto-inicio al boot
```

## 📊 Estadísticas del Proyecto

- **Líneas de código TypeScript**: ~800
- **Líneas de código Python**: ~1,500
- **Componentes React**: 4
- **Hooks personalizados**: 1
- **API Routes**: 5
- **Endpoints Bot Service**: 6
- **WebSocket Events**: 5

## 🔄 Flujo de Trabajo Automatizado

1. **Ejecutar comando**: `bun run dev:services`
2. **Dashboard** inicia inmediatamente
3. **Bot Service** inicia con 2 segundos de delay
4. **Bot** se conecta a Telegram automáticamente
5. **WebSocket** emite logs en tiempo real
6. **Dashboard** muestra logs y actualiza estado

## 📄 Licencia

Este proyecto mantiene la licencia original del BotCompressor (MIT).

## 👥 Contribuciones

Las contribuciones son bienvenidas. Por favor:
1. Fork el repositorio
2. Crea una rama para tu feature
3. Commit tus cambios
4. Push a la rama
5. Abre un Pull Request

---

**Desarrollado por**: Z.ai Code Assistant
**Fecha**: 2026-01-09
**Versión**: 1.1.0
**URL del Repositorio**: https://github.com/RolanZamvel/BotCompressor

**¡El bot se inicia automáticamente junto con el dashboard!** 🚀
