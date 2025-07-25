from typing import List
from dataclasses import dataclass

from fireflyiii_enricher_core.firefly_client import FireflyClient, simplify_transactions
from fireflyiii_enricher_core.firefly_client import (
    filter_by_description, filter_single_part, filter_without_category, SimplifiedTx
)
from fireflyiii_enricher_core.matcher import TransactionMatcher

from get_order_result import SimplifiedPayment


@dataclass
class TxMatchResult:
    tx: SimplifiedTx
    matches: List[SimplifiedPayment]


class TransactionProcessorGUI:
    def __init__(self, firefly_client: FireflyClient):
        self.firefly_client = firefly_client

    def fetch_unmatched_transactions(self,
                                     description_filter: str,
                                     tag: str,
                                     exact_match: bool = True) -> List[SimplifiedTx]:
        raw = self.firefly_client.fetch_transactions()
        non_categorized = filter_without_category(filter_single_part(raw))
        allegro_txs = filter_by_description(non_categorized, description_filter, exact_match)
        print(len(allegro_txs))
        allegro_txs = simplify_transactions(allegro_txs)
        #TODO:filter without Tag
        return allegro_txs

    def match_transactions(self, firefly_tx: List[SimplifiedTx], allegro_orders: List[SimplifiedPayment]) -> List[
        TxMatchResult]:
        results = []
        for tx in firefly_tx:
            matches = TransactionMatcher.match(tx, allegro_orders)
            if matches:
                results.append(TxMatchResult(tx=tx, matches=matches))
        return results

    def apply_match(self, tx_id: int, details: str):
        self.firefly_client.update_transaction_notes(tx_id, details)
        self.firefly_client.add_tag_to_transaction(tx_id, self.tag)
