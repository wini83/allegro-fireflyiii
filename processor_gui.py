from dataclasses import dataclass
from typing import List

from fireflyiii_enricher_core.firefly_client import (
    FireflyClient,
    SimplifiedTx,
    filter_by_description,
    filter_single_part,
    filter_without_category,
    simplify_transactions,
)
from fireflyiii_enricher_core.matcher import TransactionMatcher

from get_order_result import SimplifiedPayment


@dataclass
class TxMatchResult:
    tx: SimplifiedTx
    matches: List[SimplifiedPayment]


class TransactionProcessorGUI:
    def __init__(
        self, firefly_client: FireflyClient, orders: List[SimplifiedPayment], tag: str
    ):
        self.firefly_client = firefly_client
        self.orders = orders
        self.tag = tag

    def find_matches(
        self, filter_text: str, exact_match: bool = True
    ) -> List[TxMatchResult]:
        raw = self.firefly_client.fetch_transactions()
        filtered = filter_by_description(
            filter_without_category(filter_single_part(raw)), filter_text, exact_match
        )
        transactions = simplify_transactions(filtered)
        results = []

        for tx in transactions:
            # if self.tag in tx.tags:
            #    continue
            matches = TransactionMatcher.match(tx, self.orders)
            if matches:
                results.append(TxMatchResult(tx=tx, matches=matches))
        return results

    def apply_match(self, tx_id: int, details: str):
        self.firefly_client.update_transaction_notes(tx_id, details)
        self.firefly_client.add_tag_to_transaction(tx_id, self.tag)
