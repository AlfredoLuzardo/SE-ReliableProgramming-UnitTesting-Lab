"""Checkout coordinator."""
from models import ZERO, OrderResult


class CheckoutService:
    def __init__(self, repository, payment_gateway):
        self.repository = repository
        self.payment_gateway = payment_gateway

    def checkout(self, cart, payment_token, request_id):
        # Defect 8: every checkout needs a request id
        if not request_id:
            raise ValueError('request_id is required')

        # Defect 8: a repeated request returns the original order instead of charging again.
        # Checked before the empty-cart check, because a successful checkout empties the cart.
        existing = self.repository.get_order_by_request_id(request_id)
        if existing:
            order_id, _user_id, amount, status = existing
            return OrderResult(order_id, status, amount)

        if len(cart.lines) == 0:
            return OrderResult(None, 'empty', ZERO)
        amount = cart.total()
        print(f'Charging payment token: {payment_token}')

        # Defect 7: only take stock if all of it is available (never goes negative)
        if not self.repository.reserve_stock(cart.lines):
            order_id = self.repository.save_order(cart.user_id, amount, 'out_of_stock', request_id)
            return OrderResult(order_id, 'out_of_stock', amount)

        try:
            response = self.payment_gateway.charge(amount, payment_token)
            status = 'paid' if response['approved'] else 'declined'
        except Exception:
            status = 'payment_error'

        order_id = self.repository.save_order(cart.user_id, amount, status, request_id)
        if status != 'paid':
            # Defect 7: give the stock back and keep the cart so the user can try again
            self.repository.release_stock(cart.lines)
            return OrderResult(order_id, status, amount)

        cart.lines.clear()
        cart.discount_code = None
        cart.save()
        return OrderResult(order_id, status, amount)
