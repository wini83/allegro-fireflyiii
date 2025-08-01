"""main module"""

import logging
import os

import requests  # type: ignore[import]
from dotenv import load_dotenv  # type: ignore[import]
from fireflyiii_enricher_core.firefly_client import FireflyClient

from api import AllegroApiClient
from get_order_result import SimplifiedPayment
from processor import TransactionProcessor

load_dotenv()
FIREFLY_URL = os.getenv("FIREFLY_URL")
TOKEN = os.getenv("FIREFLY_TOKEN")
QXLSESSID = os.getenv("QXLSESSID")

DESCRIPTION_FILTER = "allegro"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("blik_sync.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Run simple CLI example."""
    print("=== Allegro CLI ===")
    firefly = FireflyClient(FIREFLY_URL, TOKEN)
    qx_session_id = QXLSESSID
    with requests.Session() as session:
        client = AllegroApiClient(session=session, cookie=qx_session_id)
        order_result = client.get_orders()
        payments_simplified = SimplifiedPayment.from_payments(order_result.payments)
        processor = TransactionProcessor(firefly, payments_simplified, "allegro_done")
        processor.process(DESCRIPTION_FILTER, exact_match=False)


if __name__ == "__main__":
    main()
