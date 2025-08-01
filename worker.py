import os

import requests  # type: ignore[import-untyped]
from dotenv import load_dotenv
from fireflyiii_enricher_core.firefly_client import FireflyClient
from loguru import logger

import log_db
from api import AllegroApiClient
from get_order_result import SimplifiedPayment
from processor_gui import TransactionProcessorGUI, TxMatchResult, match_transactions

# ---------------------------------------------------
# Configure logging with Loguru
# ---------------------------------------------------
logger.remove()
logger.add(
    sink="worker.log",
    level="DEBUG",
    rotation="10 MB",
    retention="10 days",
    compression="zip",
    format=(
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{module}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    ),
)
logger.add(
    sink=lambda msg: print(msg, end=""),
    level="INFO",
    format="{time:HH:mm:ss} | {level} | {message}",
)
# ---------------------------------------------------
# Environment and constants
# ---------------------------------------------------
load_dotenv()
TAG = "allegro_done"
DESCRIPTION_FILTER = "allegro"


# ---------------------------------------------------
# Main workflow
# ---------------------------------------------------
def main() -> None:
    logger.info("===== Worker started =====")

    logger.info("Initializing Log_db")
    log_db.init_db()

    # Initialize Firefly III client
    logger.info("Initializing FireflyClient")
    ff = FireflyClient(os.getenv("FIREFLY_URL"), os.getenv("FIREFLY_TOKEN"))

    # Fetch Firefly III transactions
    logger.info("Fetching transactions from Firefly III")
    processor = TransactionProcessorGUI(ff, TAG)
    transactions = processor.fetch_unmatched_transactions(
        DESCRIPTION_FILTER, exact_match=False
    )
    logger.debug(f"Fetched {len(transactions)} transactions from Firefly III")

    # Fetch Allegro payments
    logger.info("Fetching payments from Allegro")
    with requests.Session() as session:
        cookie = os.getenv("QXLSESSID")
        assert cookie is not None
        allegro = AllegroApiClient(cookie, session)
        orders_data = allegro.get_orders()
    payments = SimplifiedPayment.from_payments(orders_data.payments)
    logger.info(f"Fetched {len(payments)} orders/payments from Allegro")

    # Match transactions
    logger.info("Matching transactions with payments")
    matched: list[TxMatchResult] = match_transactions(transactions, payments)

    # Apply matches and log results
    auto_applied = 0
    for txr in matched:
        applied = False
        logger.info(
            f"Processing transaction ID {txr.tx.id} - matches: {len(txr.matches)} "
        )
        if len(txr.matches) == 1:
            try:
                logger.info(f"Applying match for transaction ID {txr.tx.id}")
                processor.apply_match(int(txr.tx.id), txr.matches[0].details)
                applied = True
                auto_applied += 1
                logger.success(f"Transaction {txr.tx.id} processed successfully")
            except RuntimeError as e:
                logger.error(f"Failed to processed transaction {txr.tx.id}: {e}")
                applied = False
        else:
            logger.info("Conditions not met skipping")

        details_list = [m.details for m in txr.matches]
        log_db.log_matched_transaction(txr, len(txr.matches), applied, details_list)

        # Summary
    logger.info(f"Automatically applied to {auto_applied} transactions")
    logger.info("===== Worker finished =====")


if __name__ == "__main__":
    main()
