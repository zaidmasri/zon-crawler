import os
import asyncio
import sys
import asyncpg
from botasaurus_driver import Driver
from botasaurus.user_agent import UserAgent
from botasaurus.window_size import WindowSize
from dotenv import load_dotenv
from server import Server

load_dotenv()


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
        print(f"Error connecting to database: {e}")
        return None


def create_driver():
    return Driver(
        user_agent=UserAgent.HASHED,
        window_size=WindowSize.HASHED,
        headless=False,
        beep=True,
    )


async def execute_command(command, srv):
    """Execute the command by directly awaiting it if it's a coroutine."""
    if command == "gen-reviews":
        await srv.gen_reviews()
    elif command == "gen-products":
        await srv.gen_products()
    else:
        print("Unknown command:", command)


async def main():
    try:
        if len(sys.argv) < 2:
            print("Usage: main.py <command> [options]")
            return

        # Run connect_to_db concurrently with the driver creation
        conn, driver = await asyncio.gather(
            connect_to_db(), asyncio.to_thread(create_driver)
        )

        if conn is None:
            return

        srv = Server(db=conn, driver=driver)
        command = sys.argv[1]

        # Execute the command
        await execute_command(command, srv)

    except Exception as e:
        print(f"Unexpected error in main: {e}")
    finally:
        # Close connections safely if they exist
        if conn:
            try:
                await conn.close()
            except Exception as e:
                print(f"Error closing database connection: {e}")
        if driver:
            driver.close()


asyncio.run(main())
