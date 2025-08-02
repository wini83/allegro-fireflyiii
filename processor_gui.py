from dataclasses import dataclass
from typing import Any, List, cast
from typing import Sequence

from fireflyiii_enricher_core.firefly_client import (
    FireflyClient,
    SimplifiedTx,
    filter_by_description,
    filter_single_part,
    filter_without_category,
    simplify_transactions, SimplifiedItem,
)
from fireflyiii_enricher_core.matcher import TransactionMatcher

from allegro_api.get_order_result import SimplifiedPayment


@dataclass
class TxMatchResult:
    tx: SimplifiedTx
    matches: List[SimplifiedPayment]


def match_transactions(
    firefly_tx: List[TxMatchResult],
    allegro_orders: List[SimplifiedPayment],
) -> List[TxMatchResult]:
    for tx in firefly_tx:
        # Cast list of payments to list of items for matching
        records: List[SimplifiedItem] = cast(List[SimplifiedItem], allegro_orders)
        raw_matches: List[SimplifiedItem] = TransactionMatcher.match(tx.tx, records)
        # Cast matches back to payments
        matches: List[SimplifiedPayment] = cast(List[SimplifiedPayment], raw_matches)
        tx.matches = matches
    return firefly_tx



class TransactionProcessorGUI:
    def __init__(self, firefly_client: FireflyClient, tag: str):
        self.firefly_client = firefly_client
        self.tag = tag

    def fetch_unmatched_transactions(
        self, description_filter: str, exact_match: bool = True
    ) -> List[TxMatchResult]:
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
        self.firefly_client.update_transaction_notes(tx_id, details)
        self.firefly_client.add_tag_to_transaction(tx_id, self.tag)
