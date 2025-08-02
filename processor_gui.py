"""Helper utilities for matching transactions within the Streamlit GUI."""

from dataclasses import dataclass
from typing import Any, List, cast

from fireflyiii_enricher_core.firefly_client import (
    FireflyClient,
    SimplifiedItem,
    SimplifiedTx,
    filter_by_description,
    filter_single_part,
    filter_without_category,
    simplify_transactions,
)
from fireflyiii_enricher_core.matcher import TransactionMatcher

from allegro_api.get_order_result import SimplifiedPayment


@dataclass
class TxMatchResult:
    """A Firefly transaction and its potential Allegro matches."""

    tx: SimplifiedTx
    matches: List[SimplifiedPayment]


def match_transactions(
    firefly_tx: List[TxMatchResult],
    allegro_orders: List[SimplifiedPayment],
) -> List[TxMatchResult]:
    """Match Firefly transactions with Allegro payments using ``TransactionMatcher``."""

    for tx in firefly_tx:
        # Cast list of payments to list of items for matching
        records: List[SimplifiedItem] = cast(List[SimplifiedItem], allegro_orders)
        raw_matches: List[SimplifiedItem] = TransactionMatcher.match(tx.tx, records)
        # Cast matches back to payments
        matches: List[SimplifiedPayment] = cast(List[SimplifiedPayment], raw_matches)
        tx.matches = matches
    return firefly_tx



class TransactionProcessorGUI:
    """High level logic for fetching and updating Firefly transactions."""

    def __init__(self, firefly_client: FireflyClient, tag: str):
        """Store a client and tag used when updating transactions."""
        self.firefly_client = firefly_client
        self.tag = tag

    def fetch_unmatched_transactions(
        self, description_filter: str, exact_match: bool = True
    ) -> List[TxMatchResult]:
        """Retrieve transactions not yet tagged in Firefly III."""

        raw = self.firefly_client.fetch_transactions()
        non_categorized = filter_without_category(filter_single_part(raw))
        allegro_txs = filter_by_description(
            non_categorized, description_filter, exact_match
        )

        allegro_simplified = simplify_transactions(allegro_txs)
        allegro_not_processed: list[SimplifiedTx] = []
        for tx in allegro_simplified:
            if self.tag not in tx.tags:
                allegro_not_processed.append(tx)
        results: List[TxMatchResult] = []
        for tx in allegro_not_processed:
            results.append(TxMatchResult(tx=tx, matches=[]))
        return results

    def apply_match(self, tx_id: int, details: str) -> Any:
        """Update a Firefly transaction with matching details and tag."""
        self.firefly_client.update_transaction_notes(tx_id, details)
        self.firefly_client.add_tag_to_transaction(tx_id, self.tag)
