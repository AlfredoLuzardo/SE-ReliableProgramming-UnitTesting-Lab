"""Shopping cart business logic."""
from decimal import Decimal

from models import ZERO, CartLine, to_money

MIN_QUANTITY = 1
WELCOME_RATE = Decimal('0.10')
STUDENT_RATE = Decimal('0.20')
SAVE15_AMOUNT = Decimal('15.00')
VALID_CODES = ('WELCOME10', 'STUDENT20', 'SAVE15', 'FREESHIP')


def is_valid_quantity(quantity):
    # Defect 1: only whole numbers >= 1 (bool is rejected because True counts as an int)
    return isinstance(quantity, int) and not isinstance(quantity, bool) and quantity >= MIN_QUANTITY


class ShoppingCart:
    def __init__(self, user_id, repository):
        self.user_id = user_id
        self.repository = repository
        self.lines = []
        self.discount_code = None  # Defect 4: store the code, not a saved total

    def add_item(self, sku, quantity):
        if not is_valid_quantity(quantity):
            print('Invalid quantity')
            return False
        product = self.repository.get_product(sku)
        if not product:
            print('Unknown product')
            return False
        existing = next((x for x in self.lines if x.sku == sku), None)
        already_in_cart = existing.quantity if existing else 0
        # Defect 2: check the combined quantity against stock
        if product.stock < already_in_cart + quantity:
            print('Not enough stock')
            return False
        if existing:
            existing.quantity += quantity
        else:
            self.lines.append(CartLine(sku, product.name, to_money(product.price), quantity))
        return True

    def remove_item(self, sku, quantity=None):
        if quantity is not None and not is_valid_quantity(quantity):
            print('Invalid quantity')
            return False
        for line in self.lines:
            if line.sku == sku:
                if quantity is None or quantity >= line.quantity:
                    self.lines.remove(line)
                else:
                    line.quantity -= quantity
                return True
        print('Item not found')
        return False

    def subtotal(self):
        return to_money(sum((line.unit_price * line.quantity for line in self.lines), ZERO))

    def discount_amount(self):
        # Defect 4: recalculated from the current subtotal every time
        subtotal = self.subtotal()
        if self.discount_code == 'WELCOME10':
            amount = subtotal * WELCOME_RATE
        elif self.discount_code == 'STUDENT20':
            amount = subtotal * STUDENT_RATE
        elif self.discount_code == 'SAVE15':
            amount = SAVE15_AMOUNT
        else:
            amount = ZERO
        # Defect 5: a discount can never be more than the subtotal
        return min(to_money(amount), subtotal)

    def total(self):
        return to_money(self.subtotal() - self.discount_amount())

    def apply_discount(self, code):
        if code not in VALID_CODES:
            print('Invalid coupon')
            return False
        if code == 'FREESHIP':
            print('Shipping is free')
        self.discount_code = code  # replaces any earlier code, so discounts don't stack
        return True

    def load(self):
        self.lines = []  # Defect 6: don't add on top of what is already in the cart
        for sku, quantity in self.repository.get_saved_cart(self.user_id):
            self.add_item(sku, quantity)

    def save(self):
        self.repository.save_cart(self.user_id, self.lines)
