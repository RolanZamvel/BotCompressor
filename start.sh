#!/usr/bin/env bash

# BotCompressor 2.0 - Start Script
# Script unificado para iniciar todos los servicios

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/home/z/my-project/BotCompressor-2.0"
BOT_SERVICE_DIR="$PROJECT_DIR/services/bot-service"
FRONTEND_PORT=3000
BOT_SERVICE_PORT=3002

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to wait for service to be ready
wait_for_service() {
    local url=$1
    local service_name=$2
    local max_attempts=30
    local attempt=1
    
    print_status "Waiting for $service_name to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" >/dev/null 2>&1; then
            print_success "$service_name is ready!"
            return 0
        fi
        
        echo -n "."
        sleep 1
        attempt=$((attempt + 1))
    done
    
    echo
    print_error "$service_name failed to start within $max_attempts seconds"
    return 1
}

# Function to stop existing services
stop_services() {
    print_status "Stopping existing services..."
    
    # Kill any existing processes on our ports
    if check_port $FRONTEND_PORT; then
        print_status "Stopping frontend on port $FRONTEND_PORT..."
        lsof -ti:$FRONTEND_PORT | xargs kill -9 2>/dev/null || true
    fi
    
    if check_port $BOT_SERVICE_PORT; then
        print_status "Stopping bot service on port $BOT_SERVICE_PORT..."
        lsof -ti:$BOT_SERVICE_PORT | xargs kill -9 2>/dev/null || true
    fi
    
    # Kill any existing bot processes
    pkill -f "bot_wrapper.py" 2>/dev/null || true
    pkill -f "python.*bot" 2>/dev/null || true
    
    sleep 2
    print_success "Existing services stopped"
}

# Function to setup environment
setup_environment() {
    print_status "Setting up environment..."
    
    # Change to project directory
    cd "$PROJECT_DIR"
    
    # Check if .env exists, if not create from example
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            print_status "Created .env from .env.example"
        else
            print_error ".env.example not found!"
            exit 1
        fi
    fi
    
    # Install Node.js dependencies if needed
    if [ ! -d "node_modules" ]; then
        print_status "Installing Node.js dependencies..."
        bun install
    fi
    
    # Setup bot service environment
    cd "$BOT_SERVICE_DIR"
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        print_status "Creating Python virtual environment..."
        python3 -m venv venv
    fi
    
    # Install Python dependencies
    print_status "Installing/updating Python dependencies..."
    ./venv/bin/pip install -r requirements.txt --upgrade
    
    # Create logs directory
    mkdir -p logs
    
    cd "$PROJECT_DIR"
    print_success "Environment setup complete"
}

# Function to start frontend
start_frontend() {
    print_status "Starting frontend dashboard..."
    
    cd "$PROJECT_DIR"
    
    # Start frontend in background
    bun run dev > frontend.log 2>&1 &
    FRONTEND_PID=$!
    
    echo $FRONTEND_PID > .frontend.pid
    
    print_success "Frontend started (PID: $FRONTEND_PID)"
}

# Function to start bot service
start_bot_service() {
    print_status "Starting bot service..."
    
    cd "$BOT_SERVICE_DIR"
    
    # Start bot service in background
    bun run dev > bot-service.log 2>&1 &
    BOT_SERVICE_PID=$!
    
    echo $BOT_SERVICE_PID > .bot-service.pid
    
    print_success "Bot service started (PID: $BOT_SERVICE_PID)"
}

# Function to start bot
start_bot() {
    print_status "Starting Telegram bot..."
    
    cd "$BOT_SERVICE_DIR"
    
    # Set environment variables
    export PYTHONPATH="$BOT_SERVICE_DIR/src"
    export API_ID="39532396"
    export API_HASH="7dfa32c18bbac9c85c4bd65c2b6e253a"
    export API_TOKEN="8018262234:AAHb3GdVJy_DolhKTHt0F9miSxYwhBljqv0"
    export FORWARD_TO_USER_ID="RSmuel"
    export BOT_SERVICE_URL="http://localhost:3002"
    export BOT_SERVICE_MODE="true"
    
    # Start bot in background
    ./venv/bin/python bot_wrapper.py > bot.log 2>&1 &
    BOT_PID=$!
    
    echo $BOT_PID > .bot.pid
    
    print_success "Telegram bot started (PID: $BOT_PID)"
}

# Function to show status
show_status() {
    echo
    echo "=== BotCompressor 2.0 Status ==="
    echo
    
    # Frontend status
    if check_port $FRONTEND_PORT; then
        echo -e "📱 Frontend: ${GREEN}RUNNING${NC} (http://localhost:$FRONTEND_PORT)"
    else
        echo -e "📱 Frontend: ${RED}STOPPED${NC}"
    fi
    
    # Bot service status
    if check_port $BOT_SERVICE_PORT; then
        echo -e "🤖 Bot Service: ${GREEN}RUNNING${NC} (http://localhost:$BOT_SERVICE_PORT)"
    else
        echo -e "🤖 Bot Service: ${RED}STOPPED${NC}"
    fi
    
    # Bot status
    if [ -f "$BOT_SERVICE_DIR/.bot.pid" ]; then
        BOT_PID=$(cat "$BOT_SERVICE_DIR/.bot.pid")
        if ps -p $BOT_PID > /dev/null 2>&1; then
            echo -e "📱 Telegram Bot: ${GREEN}RUNNING${NC} (PID: $BOT_PID)"
        else
            echo -e "📱 Telegram Bot: ${RED}STOPPED${NC}"
        fi
    else
        echo -e "📱 Telegram Bot: ${RED}STOPPED${NC}"
    fi
    
    echo
    echo "=== Logs ==="
    echo "Frontend:     $PROJECT_DIR/frontend.log"
    echo "Bot Service:  $BOT_SERVICE_DIR/bot-service.log"
    echo "Telegram Bot: $BOT_SERVICE_DIR/bot.log"
    echo
}

# Function to cleanup on exit
cleanup() {
    print_status "Shutting down services..."
    
    # Kill processes by PID files
    if [ -f "$PROJECT_DIR/.frontend.pid" ]; then
        kill $(cat "$PROJECT_DIR/.frontend.pid") 2>/dev/null || true
        rm -f "$PROJECT_DIR/.frontend.pid"
    fi
    
    if [ -f "$BOT_SERVICE_DIR/.bot-service.pid" ]; then
        kill $(cat "$BOT_SERVICE_DIR/.bot-service.pid") 2>/dev/null || true
        rm -f "$BOT_SERVICE_DIR/.bot-service.pid"
    fi
    
    if [ -f "$BOT_SERVICE_DIR/.bot.pid" ]; then
        kill $(cat "$BOT_SERVICE_DIR/.bot.pid") 2>/dev/null || true
        rm -f "$BOT_SERVICE_DIR/.bot.pid"
    fi
    
    print_success "All services stopped"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Main execution
main() {
    echo "🚀 BotCompressor 2.0 - Unified Start Script"
    echo "=========================================="
    echo
    
    case "${1:-start}" in
        "start")
            stop_services
            setup_environment
            start_frontend
            start_bot_service
            
            # Wait for services to be ready
            wait_for_service "http://localhost:$FRONTEND_PORT" "Frontend"
            wait_for_service "http://localhost:$BOT_SERVICE_PORT/health" "Bot Service"
            
            # Start bot after services are ready
            sleep 2
            start_bot
            
            # Wait a bit for bot to initialize
            sleep 3
            
            show_status
            
            echo
            print_success "🎉 All services started successfully!"
            echo
            echo "📱 Dashboard:    http://localhost:$FRONTEND_PORT"
            echo "🤖 Bot Service:  http://localhost:$BOT_SERVICE_PORT"
            echo "📊 Health Check: http://localhost:$BOT_SERVICE_PORT/health"
            echo
            echo "Press Ctrl+C to stop all services"
            echo
            
            # Keep script running
            while true; do
                sleep 10
                # Check if all services are still running
                if ! check_port $FRONTEND_PORT || ! check_port $BOT_SERVICE_PORT; then
                    print_error "One or more services stopped unexpectedly!"
                    show_status
                    cleanup
                fi
            done
            ;;
            
        "stop")
            cleanup
            ;;
            
        "status")
            show_status
            ;;
            
        "restart")
            cleanup
            sleep 2
            main start
            ;;
            
        "logs")
            echo "=== Recent Logs ==="
            echo
            echo "📱 Frontend (last 20 lines):"
            tail -20 "$PROJECT_DIR/frontend.log" 2>/dev/null || echo "No frontend logs found"
            echo
            echo "🤖 Bot Service (last 20 lines):"
            tail -20 "$BOT_SERVICE_DIR/bot-service.log" 2>/dev/null || echo "No bot service logs found"
            echo
            echo "📱 Telegram Bot (last 20 lines):"
            tail -20 "$BOT_SERVICE_DIR/bot.log" 2>/dev/null || echo "No bot logs found"
            ;;
            
        *)
            echo "Usage: $0 {start|stop|restart|status|logs}"
            echo
            echo "Commands:"
            echo "  start   - Start all services"
            echo "  stop    - Stop all services"
            echo "  restart - Restart all services"
            echo "  status  - Show service status"
            echo "  logs    - Show recent logs"
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"