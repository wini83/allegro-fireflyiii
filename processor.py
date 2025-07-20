from typing import List, cast

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


class TransactionProcessor:
    """Logika przetwarzania i aktualizacji transakcji"""

    def __init__(
        self, firefly_client: FireflyClient, orders: List[SimplifiedPayment], tag: str
    ):
        self.firefly_client = firefly_client
        self.orders = orders
        self.tag = tag

    def process(self, filter_text: str, exact_match: bool = True):
        raw = self.firefly_client.fetch_transactions()
        single = filter_single_part(raw)
        uncategorized = filter_without_category(single)
        filtered = filter_by_description(uncategorized, filter_text, exact_match)
        firefly_transactions: List[SimplifiedTx] = simplify_transactions(filtered)

        for tx in firefly_transactions:
            print(
                "\n📌 Firefly: ID %s | %s | %s PLN | %s"
                % (tx.id, tx.date, tx.amount, tx.description)
            )

            if self.tag in tx.tags:
                print(f"   Oznaczone tagiem '{self.tag}' -omijam ")
                continue

            print("   🔍 Możliwe dopasowania z CSV:")

            matches = TransactionMatcher.match(tx, self.orders)

            if not matches:
                print("   ⚠️ Brak dopasowań.")
                continue
            for i, order_raw in enumerate(matches, start=1):
                order: SimplifiedPayment = cast(SimplifiedPayment, order_raw)
                details = order.details
                print("\n   💬 Dopasowanie #%d" % i)
                print(f"      📅 Data: {order.date}")
                print(f"      💰 Kwota: {order.amount} PLN")
                print(f"      📝 Szczegóły: {details}")
                choice = (
                    input(
                        "      ❓ Czy chcesz zaktualizować opis w Firefly na podstawie tego wpisu? (t/n/q): "
                    )
                    .strip()
                    .lower()
                )
                if choice == "t":
                    self.firefly_client.update_transaction_notes(
                        int(tx.id), order.details
                    )
                    self.firefly_client.add_tag_to_transaction(int(tx.id), self.tag)
                    break
                if choice == "q":
                    print("🔚 Zakończono przetwarzanie.")
                    return
                print("      ⏩ Pominięto.")
