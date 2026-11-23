# Defects and Fixes

1. **Invalid quantities accepted** (`cart.py`, `add_item` / `remove_item`)
   Zero, negative or non-integer quantities were allowed. Removing a negative quantity actually added items.
   **Fix:** Quantities must be whole numbers of 1 or more; otherwise an error is raised.

2. **Adding the same product twice could exceed stock** (`cart.py`, `add_item`)
   The stock check only looked at the new quantity, not the amount already in the cart.
   **Fix:** The check now uses the existing quantity plus the new quantity.

3. **Floating-point money errors** (`cart.py`, `models.py`)
   Prices were floats, so 3 × 9.99 gave 29.970000000000002.
   **Fix:** All money uses `Decimal`, rounded to cents.

4. **Discount not updated after editing the cart** (`cart.py`, `apply_discount` / `total`)
   The discounted total was saved once, so adding or removing items afterwards still charged the old amount. Applying a code twice also stacked the discount.
   **Fix:** Only the code is stored, and the discount is recalculated from the current subtotal. A new code replaces the old one.

5. **SAVE15 could make the total negative** (`cart.py`, `apply_discount`)
   A $9.99 cart became −$5.01.
   **Fix:** The discount can't be more than the subtotal, so the lowest total is $0.00.

6. **Loading a saved cart twice doubled the items** (`cart.py`, `load`)
   **Fix:** The cart is cleared before the saved items are loaded.

7. **Stock lost when payment fails** (`checkout.py`)
   Stock was reduced before payment and never restored if the payment was declined or errored, and the cart was cleared anyway. Stock could also go negative.
   **Fix:** Stock is reserved in one transaction only if enough is available. It's given back if payment fails, and the cart is only cleared after a successful payment.

8. **Repeated checkout charged twice** (`checkout.py`)
   Sending the same request again (e.g. a double-click) created a second order and a second charge.
   **Fix:** `request_id` is required and unique. A repeat returns the original order without charging again.

## Assumptions

- A repeated `request_id` always returns the first result, even if that payment was declined. A retry needs a new id.
- Only one discount code can be used at a time.