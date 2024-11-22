from logging.handlers import RotatingFileHandler
import os
import asyncio
import string
import sys
import asyncpg
import logging
from botasaurus_driver import Driver
from botasaurus.user_agent import UserAgent
from botasaurus.window_size import WindowSize
from dotenv import load_dotenv
from server import Server
from pythonjsonlogger import jsonlogger


load_dotenv()


# Create a logger
logger = logging.getLogger("my_logger")
logger.setLevel(logging.INFO)

# Define the log formatter with custom timestamp format
formatter = jsonlogger.JsonFormatter(
    "%(asctime)s %(message)s",  # Log format with timestamp and message
    datefmt="%Y-%m-%d %H:%M:%S",  # Custom timestamp format
)

# Create log handlers with rotation
console_handler = logging.StreamHandler()  # Log to console
file_handler = RotatingFileHandler(
    "app_logs.json", maxBytes=5 * 1024 * 1024, backupCount=3
)  # Log to file with rotation

# Set formatter for all handlers
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Add the handlers to the logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)


async def connect_to_db():
    try:
        return await asyncpg.connect(
            user=os.getenv("PG_USER"),
            password=os.getenv("PG_PASSWORD"),
            database=os.getenv("PG_DATABASE"),
            host=os.getenv("PG_HOST"),
            port=os.getenv("PG_PORT"),
        )
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        return None


def create_driver():
    return Driver(
        user_agent=UserAgent.HASHED,
        window_size=WindowSize.HASHED,
        headless=True,
        beep=True,
    )


async def execute_command(command: string, srv: Server):
    """Execute the command by directly awaiting it if it's a coroutine."""
    if command == "gen-reviews":
        await srv.gen_reviews()
    else:
        logger.error("Unknown command:", command)


async def main():
    try:
        if len(sys.argv) < 2:
            logger.error("Usage: main.py <command> [options]")
            return

        # Run connect_to_db concurrently with the driver creation
        conn, driver = await asyncio.gather(
            connect_to_db(), asyncio.to_thread(create_driver)
        )

        if conn is None:
            return

        srv = Server(db=conn, driver=driver, logger=logger)
        command = sys.argv[1]

        # Execute the command
        await execute_command(command, srv)

    except Exception as e:
        logger.error(f"Unexpected error in main: {e}")
    finally:
        # Close connections safely if they exist
        if conn:
            try:
                await conn.close()
            except Exception as e:
                logger.error(f"Error closing database connection: {e}")
        if driver:
            driver.close()


asyncio.run(main())
