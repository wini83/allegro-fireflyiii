"""Data structures for the ``get_orders`` API call."""

import hashlib
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, List

from fireflyiii_enricher_core.firefly_client import SimplifiedItem


def short_id(id_str: str, length: int = 8) -> str:
    """Return a short, deterministic hash of ``id_str``."""
    return hashlib.sha1(id_str.encode()).hexdigest()[:length]


@dataclass()
class SimplifiedPayment(SimplifiedItem):
    """Simplified representation of an Allegro payment."""

    details: str

    def compare(self, other: SimplifiedItem) -> bool:
        """Check whether ``other`` matches this payment within tolerance."""
        if not super().compare_amount(other.amount):
            return False
        latest_acceptable_date = self.date + timedelta(days=6)
        return self.date <= other.date <= latest_acceptable_date

    @classmethod
    def from_payments(cls, payments: List["Payment"]) -> List["SimplifiedPayment"]:
        """Convert Allegro payment objects into simplified payments."""
        result: List["SimplifiedPayment"] = []
        for payment in payments:
            date = payment.orders[0].order_date.date()
            amount = payment.amount
            offer_text = "\n".join(
                f"{order.print_offers()}" for order in payment.orders
            )
            result.append(cls(date=date, amount=amount, details=offer_text))
        return result


class GetOrdersResult:  # pylint: disable=too-few-public-methods
    """Result of get_orders method"""

    def __init__(self, items: dict[str, Any]) -> None:
        """Init method"""
        self.orders: List[Order] = []
        for group in items["orderGroups"]:
            self.orders.append(Order(group["groupId"], group["myorders"][0]))
        self.payments: List[Payment] = Payment.from_orders(self.orders)

    def as_list(self) -> list["Order"]:
        """Return orders as list."""
        return self.orders


class Order:
    """Single order item"""

    def __init__(self, order_id: str, items: dict[str, Any]) -> None:
        """Initialize order from API response ``items``."""
        self.order_id = order_id
        self.seller = items["seller"]["login"]
        self.offers = [Offer.from_dict(o) for o in items["offers"]]
        self._order_date = items["orderDate"]
        self.total_cost = items["totalCost"]
        self.payment_amount = items["payment"]["amount"]
        self.payment_id = items["payment"]["id"]

    def print_offers(self) -> str:
        """Return human readable representation of ordered offers."""
        return "\n".join(
            f"{offer.get_simplified_title()} ({offer.unit_price} "
            f"{offer.price_currency})"
            for offer in self.offers
        )

    @property
    def order_date(self) -> datetime:
        """Return order date as ``datetime`` with timezone awareness."""
        if self._order_date.endswith("Z"):
            return datetime.fromisoformat(self._order_date[:-1]).replace(
                tzinfo=timezone.utc
            )
        return datetime.fromisoformat(self._order_date)


@dataclass(slots=True)
class Offer:
    """Single offer item"""

    offer_id: str
    title: str
    unit_price: float
    price_currency: str
    friendly_url: str
    quantity: int
    image_url: str

    @staticmethod
    def from_dict(item: dict[str, Any]) -> "Offer":
        """Create :class:`Offer` from API response ``item``."""
        return Offer(
            item["id"],
            item["title"],
            float(item["unitPrice"]["amount"]),
            item["unitPrice"]["currency"],
            item["friendlyUrl"],
            int(item["quantity"]),
            item["imageUrl"],
        )

    def get_simplified_title(self) -> str:
        """Create shortened title suitable for tagging."""

        def format_word(title_word: str) -> str:
            return "-".join(
                w.capitalize() if len(w) > 2 else w.lower()
                for w in title_word.split("-")
            )

        clean = re.sub(r"[^\w\s\-]", "", self.title or "", flags=re.UNICODE)

        words = clean.split()
        result: List[str] = []
        total_length = 0

        for word in words:
            formatted = format_word(word)
            extra = len(formatted) + (1 if result else 0)

            if len(result) < 3 and total_length + extra <= 32:
                result.append(formatted)
                total_length += extra
            else:
                break

        return " ".join(result)


@dataclass()
class Payment:
    """Group of orders paid together."""

    payment_id: str
    orders: List["Order"]
    tolerance: float = 0.01

    @property
    def sum_total_cost(self) -> float:
        """Return the total cost of all orders in the payment."""
        return sum(float(order.total_cost["amount"]) for order in self.orders)

    @property
    def amount(self) -> float:
        """Return paid amount value."""
        if not self.orders:
            return 0.0
        return float(self.orders[0].payment_amount["amount"])

    @property
    def is_balanced(self) -> bool:
        """Czy suma wartości zamówień zgadza się z kwotą płatności (z tolerancją)."""
        return abs(self.amount - self.sum_total_cost) <= self.tolerance

    def __str__(self) -> str:
        return (
            f"Payment {short_id(self.payment_id)}: "
            f"{len(self.orders)} orders, {self.amount:.2f} "
            f"total, balanced: {self.is_balanced}"
        )

    def __repr__(self) -> str:
        return (
            f"Payment {short_id(self.payment_id)}: {len(self.orders)} "
            f"orders, {self.amount:.2f} total, balanced: {self.is_balanced}"
        )

    @classmethod
    def from_orders(cls, orders: List["Order"]) -> List["Payment"]:
        """Grupuje zamówienia po `payment_id` i tworzy obiekty Payment."""
        grouped = defaultdict(list)

        for order in orders:
            grouped[order.payment_id].append(order)

        payments = [cls(payment_id=pid, orders=group) for pid, group in grouped.items()]
        return payments

