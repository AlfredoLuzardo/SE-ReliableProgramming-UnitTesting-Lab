"""SQLite persistence."""
import sqlite3
from models import Product, to_money

ONE_ROW = 1


class StoreRepository:
    def __init__(self, db_path='shop.db'):
        self.db_path = db_path

    def connect(self):
        return sqlite3.connect(self.db_path, timeout=2)

    def get_product(self, sku):
        conn = self.connect()
        row = conn.execute(f"SELECT sku, name, price, stock FROM products WHERE sku = '{sku}'").fetchone()
        conn.close()
        return Product(*row) if row else None

    def get_saved_cart(self, user_id):
        conn = self.connect()
        rows = conn.execute(f"SELECT sku, quantity FROM saved_cart WHERE user_id = '{user_id}'").fetchall()
        conn.close()
        return rows

    def save_cart(self, user_id, lines):
        conn = self.connect()
        conn.execute('DELETE FROM saved_cart WHERE user_id = ?', (user_id,))
        for line in lines:
            conn.execute('INSERT INTO saved_cart VALUES (?, ?, ?)', (user_id, line.sku, line.quantity))
        conn.commit()
        conn.close()

    def reserve_stock(self, lines):
        """Defect 7: take stock for every line in one transaction, or for none.

        Returns False (and changes nothing) if any product doesn't have enough stock.
        """
        conn = self.connect()
        try:
            for line in lines:
                cur = conn.execute('UPDATE products SET stock = stock - ? WHERE sku = ? AND stock >= ?',
                                   (line.quantity, line.sku, line.quantity))
                if cur.rowcount != ONE_ROW:
                    conn.rollback()
                    return False
            conn.commit()
            return True
        finally:
            conn.close()

    def release_stock(self, lines):
        """Defect 7: give reserved stock back when payment fails."""
        conn = self.connect()
        for line in lines:
            conn.execute('UPDATE products SET stock = stock + ? WHERE sku = ?', (line.quantity, line.sku))
        conn.commit()
        conn.close()

    def save_order(self, user_id, amount, status, request_id):
        conn = self.connect()
        cur = conn.execute('INSERT INTO orders(user_id, amount, status, request_id) VALUES (?, ?, ?, ?)',
                           (user_id, str(amount), status, request_id))
        conn.commit()
        order_id = cur.lastrowid
        conn.close()
        return order_id

    def get_order_by_request_id(self, request_id):
        """Defect 8: look up an earlier order for the same request."""
        conn = self.connect()
        row = conn.execute('SELECT id, user_id, amount, status FROM orders WHERE request_id = ?',
                           (request_id,)).fetchone()
        conn.close()
        if row is None:
            return None
        order_id, user_id, amount, status = row
        return order_id, user_id, to_money(amount), status

    def list_orders(self, user_id):
        conn = self.connect()
        rows = conn.execute('SELECT id, user_id, amount, status FROM orders ORDER BY id DESC').fetchall()
        conn.close()
        return rows
