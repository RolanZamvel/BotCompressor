# 🚀 Instrucciones de Despliegue - Comandos Bun

## 📋 Resumen

El comando `bun run build` ahora hace lo siguiente:
1. **Compila** el Next.js frontend
2. **Inicia** el bot-service con auto-inicio del bot
3. **Inicia** el Next.js production server
4. **Ambos servicios corren en paralelo**

## 🎯 Comandos Disponibles

### Para Desarrollo Local

```bash
bun run dev
```
Inicia solo el dashboard en modo desarrollo (http://localhost:3000)

### Para Iniciar Ambos Servicios (Dev)

```bash
bun run dev:services
```
Inicia ambos servicios en modo desarrollo:
- Dashboard Next.js (http://localhost:3000)
- Bot Service (http://localhost:3002)
- Bot Python se inicia automáticamente

### Para Despliegue (Producción)

```bash
bun run build
```
**Este comando:**
1. Compila el Next.js para producción
2. Inicia el bot-service (con bot auto-iniciándose)
3. Inicia el Next.js production server
4. ¡Todo funciona automáticamente!

### Desde el Dashboard (API Route)

Alternativamente, puedes hacer el despliegue desde el dashboard web:

```bash
# Abre el dashboard en tu navegador
http://localhost:3000

# Hace POST a la API de despliegue
# (Si agregaste un botón de "Deploy" en el futuro)
POST http://localhost:3000/api/deploy
```

## 📱 Flujo Completo del Despliegue

### Paso 1: Ejecutar Build

```bash
cd /home/z/BotCompressor
bun run build
```

### Paso 2: Lo que Sucede Automáticamente

El comando `build` ejecuta estos 3 comandos en secuencia:

```bash
# Comando 1: Compilar Next.js
bun run build:frontend

# Comando 2: Iniciar bot-service
bun run start:bot-service

# Comando 3: Iniciar servidor de producción
bun run start
```

### Paso 3: Verificar que Todo Funciona

```bash
# Verificar Next.js production server
curl http://localhost:3000

# Verificar bot-service
curl http://localhost:3002/health

# Verificar estado del bot
curl http://localhost:3002/status
```

## 🔧 Comandos Individuales

### Compilar Solamente el Frontend

```bash
bun run build:frontend
```

### Iniciar Solamente el Bot Service

```bash
bun run start:bot-service
```

### Iniciar Solamente el Frontend (Production)

```bash
bun run start
```

### Iniciar Ambos Servicios (Modo Producción)

```bash
bun run start:frontend & bun run start:bot-service &
```

## 🎯 Scripts en package.json

| Script | Comando | Función |
|--------|---------|----------|
| `bun run dev` | `next dev -p 3000` | Inicia dashboard en desarrollo |
| `bun run dev:services` | `bun run start-all.ts` | Inicia ambos servicios con auto-inicio |
| `bun run start:frontend` | `next dev -p 3000` | Inicia solo dashboard |
| `bun run start:bot-service` | `cd mini-services/bot-service && bun run dev` | Inicia solo bot-service |
| `bun run build:frontend` | `next build + cp static` | Compila solo Next.js |
| `bun run start:bot-service` | Inicia bot-service | Inicia bot-service |
| `bun run build` | `bun run build:frontend && bun run start:bot-service` | Compila e inicia bot-service |
| `bun run start` | `bun run start:frontend & bun run start:bot-service &` | Inicia ambos en paralelo |
| `bun run lint` | `next lint` | Linter de código |

## 📊 Tiempos de Ejecución Estimados

| Comando | Tiempo Estimado | Notas |
|----------|------------------|-------|
| `bun run dev` | 2-3 seg | Inicia rápido en modo dev |
| `bun run build:frontend` | 30-60 seg | Compila Next.js para producción |
| `bun run start:bot-service` | 2-3 seg | Inicia el servicio |
| `bun run build` | 35-65 seg | Compila + inicia servicios |

## 🚀 Despliegue en Railway

### Desde el Navegador (Más Fácil)

1. Ve a https://railway.app
2. Click en "Deploy from GitHub repo"
3. Selecciona tu repositorio: `RolanZamvel/BotCompressor`
4. Railway detectará automáticamente los servicios
5. Configura las variables de entorno:
   - API_ID
   - API_HASH
   - API_TOKEN
6. Click en "Deploy"

**Ventaja:** Todo se despliega automáticamente en la nube.

### Desde la Línea de Comandos (Más Control)

```bash
# Instalar Railway CLI
bun install -g @railway/cli

# Login
railway login

# Inicializar proyecto
railway init

# Desplegar
railway up
```

## 🔍 Monitoreo del Despliegue

### Ver Logs del Frontend

```bash
# Terminal donde iniciaste
tail -f server.log
```

### Ver Logs del Bot Service

```bash
# Ir al directorio del bot-service
cd mini-services/bot-service
tail -f bot-service.log
```

### Ver Estado de los Servicios

```bash
# Verificar Next.js
curl http://localhost:3000

# Verificar bot-service
curl http://localhost:3002/health

# Verificar bot status
curl http://localhost:3002/status
```

## ⚠️ Problemas Comunes y Soluciones

### Problema: "Port 3000 already in use"

**Solución:**
```bash
# Matar proceso en puerto 3000
lsof -ti:3000 | xargs kill -9

# O usar otro puerto
bun run dev -- -p 3001
```

### Problema: "Port 3002 already in use"

**Solución:**
```bash
# Matar proceso en puerto 3002
lsof -ti:3002 | xargs kill -9

# O revisar logs del bot-service
cd mini-services/bot-service
cat bot-service.log
```

### Problema: "Bot not starting automatically"

**Solución:**
```bash
# Verificar logs del bot-service
cd mini-services/bot-service
tail -50 bot-service.log

# Iniciar manualmente desde el dashboard
http://localhost:3000
# Click en botón "Start"
```

### Problema: "Build failed"

**Solución:**
```bash
# Limpiar caché de Next.js
rm -rf .next

# Intentar build nuevamente
bun run build:frontend

# O usar modo verbose
bun run build:frontend --verbose
```

## 🎯 Resumen del Despliegue

**Para desarrollo local:**
```bash
bun run dev:services
```

**Para producción local:**
```bash
bun run build
```

**Para producción en Railway (Recomendado):**
```bash
# Desde navegador
https://railway.app
→ Conectar GitHub
→ Seleccionar repositorio BotCompressor
→ Configurar variables (API_ID, API_HASH, API_TOKEN)
→ Deploy
```

**Resultados esperados:**
- ✅ Dashboard web en http://localhost:3000 o HTTPS en Railway
- ✅ Bot service en http://localhost:3002 o HTTPS en Railway
- ✅ Bot Python corriendo y conectado a Telegram
- ✅ Monitoreo en tiempo real disponible
- ✅ Logs visibles en el dashboard

## 💡 Recomendaciones

### Para Desarrollo

- Usa `bun run dev` para iteraciones rápidas
- Usa Hot Reload para cambios en el frontend
- Revisa los logs del bot-service frecuentemente

### Para Producción

- Usa `bun run build` para despliegue completo
- Verifica que las credenciales de Telegram sean correctas
- Monitorea el consumo de RAM y CPU
- Configura logs externos (Papertrail, Loggly, etc.) si es necesario

### Para Nube (Railway, Vercel, etc.)

- Configura variables de entorno antes del despliegue
- Usa GitHub integration para auto-deploy en commits
- Revisa los logs de la plataforma después del despliegue
- Configura dominio personalizado si es necesario

---

**Última actualización:** 2026-01-09
**Versión:** 1.3.0
**Runtime:** Bun
**Framework:** Next.js 15 + Python/Pyrogram
