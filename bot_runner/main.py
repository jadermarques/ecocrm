import asyncio
import os
import logging
import sys
from bot_runner.consumer import start_consumer

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("BotRunner")

async def start_router():
    """
    Router mode: Could be used for dispatching tasks or load balancing.
    Placeholder for now.
    """
    logger.info("Starting in ROUTER mode...")
    while True:
        logger.info("Router heartbeat...")
        await asyncio.sleep(60)

async def main():
    mode = os.getenv("WORKER_MODE", "runner").lower()
    
    if mode == "router":
        await start_router()
    elif mode == "runner":
        await start_consumer()
    else:
        logger.error(f"Unknown WORKER_MODE: {mode}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot Runner stopped by user.")
        sys.exit(0)
