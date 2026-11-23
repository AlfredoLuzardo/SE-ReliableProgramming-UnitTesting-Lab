"""Models for the order-management application."""
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

CENT = Decimal('0.01')
ZERO = Decimal('0.00')


def to_money(value):
    """Convert a number to a Decimal rounded to cents (defect 3)."""
    return Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP)


@dataclass
class Product:
    sku: str
    name: str
    price: float  # converted to Decimal when added to a cart
    stock: int


@dataclass
class CartLine:
    sku: str
    name: str
    unit_price: Decimal
    quantity: int


@dataclass
class OrderResult:
    order_id: int | None
    status: str
    total: Decimal
