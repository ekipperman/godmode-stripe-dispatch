from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import psutil
import asyncio
import redis.asyncio as redis
import json
from pathlib import Path
import logging

# Import your own modules
from modules import PluginManager
from telegram_bot import TelegramBot
from sentry_config import init_sentry, capture_exception, set_tag

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load configuration
def load_config():
    try:
        config_path = Path(__file__).parent / "config.json"
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load configuration: {str(e)}")
        raise

config = load_config()

# Initialize services
init_sentry(config)
redis_client = redis.Redis.from_url(config["database"]["redis_url"])
plugin_manager = PluginManager(config)
telegram_bot = TelegramBot(config, plugin_manager)

# Initialize FastAPI app
app = FastAPI(
    title="AI-Powered Telegram Assistant",
    description="Backend API for Telegram bot with plugin system",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config["security"]["allowed_origins"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define routes (Health check etc.)
@app.get("/health")
async def health_check():
    await redis_client.ping()
    cpu_percent = psutil.cpu_percent()
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    active_plugins = plugin_manager.get_active_plugins()

    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "services": {
            "redis": "healthy",
            "plugins": {name: "active" for name in active_plugins}
        },
        "system": {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "disk_percent": disk.percent
        }
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    if config["webhook"]["enabled"]:
        telegram_bot.start_webhook(config["webhook"]["url"], config["webhook"]["port"])
    else:
        telegram_bot.start_polling()

    await redis_client.ping()
    logger.info("Startup complete")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    telegram_bot.stop()
    await redis_client.close()

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    capture_exception(exc, {"path": request.url.path})
    return JSONResponse(status_code=500, content={"error": str(exc)})

# Entry point for local/dev
if __name__ == "__main__":
    import os
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port)
