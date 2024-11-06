import os
import asyncio
import sys
import asyncpg
from botasaurus_driver import Driver, Wait
from botasaurus.user_agent import UserAgent
from botasaurus.window_size import WindowSize
from dotenv import load_dotenv
from server import Server

load_dotenv()


async def main():
    try:
        if len(sys.argv) < 2:
            print("Usage: main.py <command> [options]")
            return

        try:
            conn = await asyncpg.connect(
                user=os.getenv("PG_USER"),
                password=os.getenv("PG_PASSWORD"),
                database=os.getenv("PG_DATABASE"),
                host=os.getenv("PG_HOST"),
                port=os.getenv("PG_PORT"),
            )
        except Exception as e:
            print(f"Error connecting to database: {e}")
            return

        driver = Driver(
            user_agent=UserAgent.HASHED,
            window_size=WindowSize.HASHED,
            headless=False,
            beep=True,
        )
        srv = Server(db=conn, driver=driver)
        command = sys.argv[1]
        if command == "gen-reviews":
            try:
                await srv.gen_reviews()
            except Exception as e:
                print(f"Error running scraper: {e}")

        elif command == "gen-products":
            await srv.gen_products()
        else:
            print("Unknown command:", command)

    except Exception as e:
        print(f"Unexpected error in main: {e}")
    finally:
        # Close connections safely if they exist
        try:
            await conn.close()
        except Exception as e:
            print(f"Error closing database connection: {e}")
        driver.close()


asyncio.run(main())
