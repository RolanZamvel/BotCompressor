#!/usr/bin/env python3
"""
Bot Wrapper for BotCompressor 2.0
Enhanced Python bot wrapper with better error handling and logging
"""

import os
import sys
import subprocess
import logging
import signal
import time
from pathlib import Path
from typing import Optional

# Add the src directory to Python path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class BotWrapper:
    """Enhanced bot wrapper with proper process management"""
    
    def __init__(self):
        self.bot_process: Optional[subprocess.Popen] = None
        self.running = False
        self.restart_count = 0
        self.max_restarts = 5
        self.restart_delay = 5
        
    def setup_environment(self):
        """Setup environment variables and configuration"""
        # Set Python path
        python_path = os.environ.get('PYTHONPATH', '')
        src_path = str(src_dir)
        if src_path not in python_path:
            os.environ['PYTHONPATH'] = f"{python_path}:{src_path}"
        
        # Set bot service mode
        os.environ['BOT_SERVICE_MODE'] = 'true'
        
        logger.info("Environment setup completed")
    
    def start_bot(self):
        """Start the bot process"""
        try:
            self.setup_environment()
            
            # Import and start the bot
            from src.bot import app
            
            logger.info("Starting BotCompressor 2.0 Enhanced Bot...")
            logger.info(f"Python version: {sys.version}")
            logger.info(f"Working directory: {os.getcwd()}")
            logger.info(f"Bot Service URL: {os.environ.get('BOT_SERVICE_URL', 'http://localhost:3002')}")
            
            # Start the bot
            self.running = True
            app.run()
            
        except ImportError as e:
            logger.error(f"Failed to import bot module: {e}")
            logger.error("Make sure all dependencies are installed")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Failed to start bot: {e}")
            sys.exit(1)
    
    def stop_bot(self):
        """Stop the bot gracefully"""
        logger.info("Stopping bot...")
        self.running = False
        
        if self.bot_process:
            try:
                self.bot_process.terminate()
                self.bot_process.wait(timeout=10)
                logger.info("Bot stopped gracefully")
            except subprocess.TimeoutExpired:
                logger.warning("Bot did not stop gracefully, forcing...")
                self.bot_process.kill()
                self.bot_process.wait()
            except Exception as e:
                logger.error(f"Error stopping bot: {e}")
    
    def restart_bot(self):
        """Restart the bot with error handling"""
        if self.restart_count >= self.max_restarts:
            logger.error(f"Max restart attempts ({self.max_restarts}) reached")
            sys.exit(1)
        
        logger.info(f"Restarting bot (attempt {self.restart_count + 1}/{self.max_restarts})")
        self.restart_count += 1
        
        # Stop current instance
        self.stop_bot()
        
        # Wait before restart
        time.sleep(self.restart_delay)
        
        # Start new instance
        self.start_bot()
    
    def signal_handler(self, signum, frame):
        """Handle system signals"""
        logger.info(f"Received signal {signum}")
        self.stop_bot()
        sys.exit(0)
    
    def run(self):
        """Main entry point"""
        # Setup signal handlers
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
        
        try:
            self.start_bot()
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
            self.stop_bot()
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            self.restart_bot()

def main():
    """Main function"""
    wrapper = BotWrapper()
    wrapper.run()

if __name__ == "__main__":
    main()