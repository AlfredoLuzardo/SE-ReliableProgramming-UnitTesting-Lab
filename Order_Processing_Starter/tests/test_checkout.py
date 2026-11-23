"""Tests for the checkout defects (7-8), using the supplied fake payment gateway."""
from decimal import Decimal

import pytest

from cart import ShoppingCart
from checkout import CheckoutService
from payments import FakePaymentGateway

TOKEN = 'TEST_TOKEN'
LAPTOP_STOCK = 5
MOUSE_STOCK = 20


class BrokenGateway:
    """Simulates the payment gateway crashing."""

    def charge(self, amount, payment_token):
        raise ConnectionError('gateway down')


def test_successful_checkout(repo, cart):
    gateway = FakePaymentGateway()
    cart.add_item('MOU-01', 2)
    result = CheckoutService(repo, gateway).checkout(cart, TOKEN, 'req-1')
    assert result.status == 'paid'
    assert result.total == Decimal('59.90')
    assert repo.get_product('MOU-01').stock == MOUSE_STOCK - 2
    assert cart.lines == []


def test_empty_cart_is_not_charged(repo, cart):
    gateway = FakePaymentGateway()
    result = CheckoutService(repo, gateway).checkout(cart, TOKEN, 'req-empty')
    assert result.status == 'empty'
    assert gateway.calls == []


# Defect 7: stock and cart on a failed payment
def test_declined_payment_restores_stock_and_keeps_cart(repo, cart):
    cart.add_item('LAP-01', 2)
    result = CheckoutService(repo, FakePaymentGateway(should_approve=False)).checkout(cart, TOKEN, 'req-2')
    assert result.status == 'declined'
    assert repo.get_product('LAP-01').stock == LAPTOP_STOCK
    assert len(cart.lines) == 1


def test_payment_error_restores_stock_and_keeps_cart(repo, cart):
    cart.add_item('LAP-01', 1)
    result = CheckoutService(repo, BrokenGateway()).checkout(cart, TOKEN, 'req-3')
    assert result.status == 'payment_error'
    assert repo.get_product('LAP-01').stock == LAPTOP_STOCK
    assert len(cart.lines) == 1


def test_stock_never_goes_negative(repo):
    gateway = FakePaymentGateway()
    service = CheckoutService(repo, gateway)
    alice = ShoppingCart('alice', repo)
    bob = ShoppingCart('bob', repo)
    alice.add_item('LAP-01', 3)
    bob.add_item('LAP-01', 3)  # fits on its own, but not after alice buys

    assert service.checkout(alice, TOKEN, 'req-a').status == 'paid'
    assert service.checkout(bob, TOKEN, 'req-b').status == 'out_of_stock'
    assert repo.get_product('LAP-01').stock == LAPTOP_STOCK - 3
    assert len(gateway.calls) == 1  # bob was not charged


# Defect 8: repeated checkout
def test_repeated_checkout_charges_once(repo, cart):
    gateway = FakePaymentGateway()
    service = CheckoutService(repo, gateway)
    cart.add_item('MOU-01', 1)
    first = service.checkout(cart, TOKEN, 'req-dup')
    second = service.checkout(cart, TOKEN, 'req-dup')
    assert second.order_id == first.order_id
    assert second.status == 'paid'
    assert len(gateway.calls) == 1
    assert repo.get_product('MOU-01').stock == MOUSE_STOCK - 1


def test_missing_request_id_is_rejected(repo, cart):
    gateway = FakePaymentGateway()
    cart.add_item('USB-01', 1)
    with pytest.raises(ValueError):
        CheckoutService(repo, gateway).checkout(cart, TOKEN, None)
    assert gateway.calls == []
