"""main module"""

import asyncio
import os

import aiohttp  # type: ignore[import]
from dotenv import load_dotenv  # type: ignore[import]

from api import AllegroApiClient

load_dotenv()

QXLSESSID = os.getenv("QXLSESSID")


def tri_words(text: str) -> str:
    """Return first three words from ``text``."""
    words = text.strip().split()
    return " ".join(words[:3])


async def main():
    """Run simple CLI example."""
    print("=== Allegro CLI ===")

    qx_session_id = QXLSESSID
    async with aiohttp.ClientSession() as session:
        client = AllegroApiClient(session=session, cookie=qx_session_id)

        orders = await client.get_orders()
        orders_list = orders.orders  # <-- to jest property, nie metoda

        for order in orders_list:
            item_text = ""
            for offer in order.offers:
                item_text += (
                    f"({tri_words(offer.title)} -"
                    f" {offer.unit_price}"
                    f" {offer.price_currency}) "
                )
            item_text += f"\nData zamówienia: {order.order_date}"
            item_text += f"\nŁączny koszt: {order.total_cost}"
            item_text += "\n" + "-" * 40
            print(item_text)

if __name__ == "__main__":
    asyncio.run(main())
