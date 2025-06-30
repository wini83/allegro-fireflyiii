from dataclasses import dataclass
from typing import Any, Optional


class GetOrdersResult:
    """Result of get_orders method"""

    def __init__(self, items: dict) -> None:
        """Init method"""
        self.orders = [
            Order(group["groupId"], group["myorders"][0])
            for group in items["orderGroups"]
        ]

    def get_order(self, item: Any):
        """Returns single order"""
        return Order(item["groupId"], item["myorders"][0])


class Order:
    """Single order item"""

    def __init__(self, order_id: str, items: dict) -> None:
        """Init method"""
        self.order_id = order_id
        self.seller = items["seller"]["login"]
        self.offers = [Offer.from_dict(o) for o in items["offers"]]
        self.order_date = items["orderDate"]
        self.total_cost = items["totalCost"]
        self.status = Status(items["status"]["primary"]["status"])
        delivery = items["delivery"]
        waybills_data = delivery["waybillsData"]

        if "waybills" in waybills_data:
            pickup = waybills_data["waybills"][0].get("pickupCode", {})

            self.delivery = Delivery(
                delivery["name"],
                waybills_data["waybills"][0]["carrier"]["url"],
                pickup.get("code"),
                pickup.get("receiverPhoneNumber"),
                pickup.get("qrCode"),
            )
        else:
            self.delivery = Delivery(delivery["name"], None, None, None, None)

    def get_formatted_address(self, items: dict):
        """Returns formatted delivery address"""
        return f"{items['street']} {items['code']} {items['city']}"

    def get_offer(self, item: Any):
        """Returns single offer"""
        return Offer.from_dict(item)


@dataclass(slots=True)
class Status:
    """Order status"""

    current_status: str


@dataclass(slots=True)
class Delivery:
    """Delivery info"""

    name: str
    url: Optional[str]
    pickup_code: Optional[str]
    receiver_phone_number: Optional[str]
    qr_code: Optional[str]


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
    def from_dict(item: dict) -> "Offer":
        return Offer(
            item["id"],
            item["title"],
            float(item["unitPrice"]["amount"]),
            item["unitPrice"]["currency"],
            item["friendlyUrl"],
            int(item["quantity"]),
            item["imageUrl"],
        )
