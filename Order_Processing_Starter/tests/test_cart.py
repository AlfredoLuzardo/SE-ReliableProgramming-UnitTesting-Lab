"""Tests for the cart defects (1-6)."""
from decimal import Decimal

import pytest

from cart import ShoppingCart

MOUSE = 'MOU-01'   # 29.95, stock 20
USB = 'USB-01'     # 9.99, stock 50
MOUSE_STOCK = 20


# Defect 1: invalid quantities
@pytest.mark.parametrize('bad_quantity', [0, -1, 1.5, '2', True])
def test_add_item_rejects_invalid_quantity(cart, bad_quantity):
    assert cart.add_item(MOUSE, bad_quantity) is False
    assert cart.lines == []


def test_remove_negative_quantity_does_not_add_items(cart):
    cart.add_item(USB, 2)
    assert cart.remove_item(USB, -3) is False
    assert cart.lines[0].quantity == 2


def test_remove_partial_then_all(cart):
    cart.add_item(USB, 5)
    cart.remove_item(USB, 2)
    assert cart.lines[0].quantity == 3
    cart.remove_item(USB)
    assert cart.lines == []


# Defect 2: adding the same product twice
def test_duplicate_product_merges_into_one_line(cart):
    cart.add_item(USB, 2)
    cart.add_item(USB, 3)
    assert len(cart.lines) == 1
    assert cart.lines[0].quantity == 5


def test_duplicate_product_cannot_exceed_stock(cart):
    assert cart.add_item(MOUSE, 15)
    assert cart.add_item(MOUSE, 6) is False  # 15 + 6 = 21 > 20
    assert cart.lines[0].quantity == 15


def test_can_add_exactly_all_stock(cart):
    assert cart.add_item(MOUSE, MOUSE_STOCK)


# Defect 3: floating-point money
def test_subtotal_is_exact(cart):
    cart.add_item(USB, 3)
    assert cart.subtotal() == Decimal('29.97')


# Defect 4: discount after editing the cart / stacking
def test_discount_updates_after_cart_edit(cart):
    cart.add_item(MOUSE, 2)
    cart.apply_discount('WELCOME10')
    cart.add_item(MOUSE, 2)
    assert cart.total() == Decimal('107.82')  # 119.80 * 0.9


def test_discount_does_not_stack(cart):
    cart.add_item(MOUSE, 2)  # 59.90
    cart.apply_discount('WELCOME10')
    cart.apply_discount('WELCOME10')
    assert cart.total() == Decimal('53.91')


@pytest.mark.parametrize('code, expected', [
    ('WELCOME10', Decimal('53.91')),
    ('STUDENT20', Decimal('47.92')),
    ('SAVE15', Decimal('44.90')),
    ('FREESHIP', Decimal('59.90')),
])
def test_discount_codes(cart, code, expected):
    cart.add_item(MOUSE, 2)
    assert cart.apply_discount(code)
    assert cart.total() == expected


def test_invalid_code_rejected(cart):
    cart.add_item(MOUSE, 1)
    assert cart.apply_discount('BOGUS') is False
    assert cart.total() == Decimal('29.95')


# Defect 5: SAVE15 below $15
def test_save15_never_goes_negative(cart):
    cart.add_item(USB, 1)  # 9.99
    cart.apply_discount('SAVE15')
    assert cart.total() == Decimal('0.00')


# Defect 6: loading twice
def test_loading_saved_cart_twice_does_not_duplicate(repo):
    cart = ShoppingCart('alice', repo)
    cart.add_item(USB, 2)
    cart.save()

    restored = ShoppingCart('alice', repo)
    restored.load()
    restored.load()
    assert len(restored.lines) == 1
    assert restored.lines[0].quantity == 2
