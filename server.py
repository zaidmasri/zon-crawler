from typing import Coroutine
from botasaurus_driver import Driver


class Server:
    driver: Driver
    conn: Coroutine

    def __init__(self, driver: Driver, db: Coroutine):
        self.driver = driver
        self.conn = db

    async def get_products(self):
        values = await self.conn.fetch("SELECT * FROM products")
        await self.conn.close()
        return values
