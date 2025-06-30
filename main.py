import asyncio
import getpass
import aiohttp
from api import AllegroApiClient

def tri_words(text: str) -> str:
    words = text.strip().split()
    return " ".join(words[:3])


async def main():
    print("=== Allegro CLI ===")
#    qx_session_id = getpass.getpass("Wprowadź QXLSESSID (nie będzie widoczny): ")

    async with aiohttp.ClientSession() as session:
        client = AllegroApiClient(session=session, cookie=qx_session_id)

        try:
            orders = await client.get_orders()
            orders_list = orders.get_orders  # <-- to jest property, nie metoda

            for order in orders_list:
                item_text = ""
                for offer in order.get_offers:
                    item_text += f"({tri_words(offer.get_title)} - {offer.get_unit_price} {offer.get_price_currency}) "
                item_text += f"\nData zamówienia: {order.get_orde_date}"
                item_text += f"\nŁączny koszt: {order.get_total_cost}"
                item_text += "\n" + "-" * 40
                print(item_text)

        except Exception as e:
            print(f"\n❌ Błąd: {e}")

if __name__ == "__main__":
    asyncio.run(main())
