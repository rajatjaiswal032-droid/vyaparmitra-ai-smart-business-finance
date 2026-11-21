"""Database module for Smart Business Finance System (finance.db)."""
import sqlite3
from typing import Any, Dict, List, Optional

DB_PATH = "finance.db"

def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path: str = DB_PATH) -> None:
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            business_name TEXT DEFAULT 'Kirana Store',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('income', 'expense')),
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            description TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            invoice_number TEXT NOT NULL,
            date TEXT NOT NULL,
            customer_name TEXT NOT NULL,
            customer_state TEXT NOT NULL,
            seller_state TEXT NOT NULL,
            items_json TEXT DEFAULT '[]',
            subtotal REAL NOT NULL,
            cgst REAL DEFAULT 0.0,
            sgst REAL DEFAULT 0.0,
            igst REAL DEFAULT 0.0,
            total_amount REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS loans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            loan_name TEXT NOT NULL,
            principal REAL NOT NULL,
            interest_rate REAL NOT NULL,
            tenure_months INTEGER NOT NULL,
            monthly_emi REAL NOT NULL,
            total_interest REAL NOT NULL,
            risk_level TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS udhaar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            customer_name TEXT NOT NULL,
            phone TEXT DEFAULT '',
            amount REAL NOT NULL,
            due_date TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('Pending', 'Paid')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            item_name TEXT NOT NULL,
            unit TEXT DEFAULT 'pcs',
            stock_qty REAL NOT NULL DEFAULT 0,
            min_stock REAL NOT NULL DEFAULT 0,
            selling_price REAL NOT NULL DEFAULT 0,
            gst_rate REAL NOT NULL DEFAULT 0,
            expiry_date TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS daily_closings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            opening_cash REAL NOT NULL DEFAULT 0,
            system_cash_sales REAL NOT NULL DEFAULT 0,
            system_upi_sales REAL NOT NULL DEFAULT 0,
            cash_expenses REAL NOT NULL DEFAULT 0,
            actual_galla_cash REAL NOT NULL DEFAULT 0,
            actual_upi_received REAL NOT NULL DEFAULT 0,
            difference REAL NOT NULL DEFAULT 0,
            notes TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        );
    """)
    for table_name in ("inventory", "udhaar"):
        cur.execute(f"PRAGMA table_info({table_name})")
        columns = {str(row[1]) for row in cur.fetchall()}
        if table_name == "inventory":
            if "expiry_date" not in columns:
                cur.execute("ALTER TABLE inventory ADD COLUMN expiry_date TEXT DEFAULT ''")
        else:
            if "entry_type" not in columns:
                cur.execute(
                    "ALTER TABLE udhaar ADD COLUMN entry_type TEXT "
                    "DEFAULT 'Customer - Lena Hai'"
                )
            if "payment_mode" not in columns:
                cur.execute(
                    "ALTER TABLE udhaar ADD COLUMN payment_mode TEXT DEFAULT 'Cash'"
                )
            if "paid_amount" not in columns:
                cur.execute(
                    "ALTER TABLE udhaar ADD COLUMN paid_amount REAL NOT NULL DEFAULT 0"
                )
    cur.execute("CREATE INDEX IF NOT EXISTS idx_trans_user ON transactions(user_id);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_inv_user ON invoices(user_id);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_loans_user ON loans(user_id);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_udhaar_user ON udhaar(user_id);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_inventory_user ON inventory(user_id);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_closing_user ON daily_closings(user_id);")
    conn.commit()
    conn.close()

# Users CRUD
def create_user(username: str, password_hash: str, business_name: str = "Kirana Store") -> Optional[int]:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (username, password_hash, business_name) VALUES (?, ?, ?)",
            (username.strip(), password_hash, business_name.strip()),
        )
        conn.commit()
        return cur.lastrowid
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username = ?", (username.strip(),))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None

def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


# Transactions CRUD
def add_transaction(user_id: int, date: str, trans_type: str, category: str, amount: float, description: str = "") -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO transactions (user_id, date, type, category, amount, description) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, date, trans_type.lower(), category.strip(), float(amount), description.strip()),
    )
    conn.commit()
    tid = cur.lastrowid
    conn.close()
    return tid

def get_transactions(user_id: int, trans_type: Optional[str] = None, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()
    q = "SELECT * FROM transactions WHERE user_id = ?"
    params: List[Any] = [user_id]
    if trans_type:
        q += " AND type = ?"
        params.append(trans_type.lower())
    if start_date:
        q += " AND date >= ?"
        params.append(start_date)
    if end_date:
        q += " AND date <= ?"
        params.append(end_date)
    q += " ORDER BY date DESC, id DESC"
    cur.execute(q, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def delete_transaction(user_id: int, transaction_id: int) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM transactions WHERE id = ? AND user_id = ?", (transaction_id, user_id))
    conn.commit()
    deleted = cur.rowcount > 0
    conn.close()
    return deleted

def get_financial_summary(user_id: int) -> Dict[str, float]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT 
            COALESCE(SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END), 0.0) as total_income,
            COALESCE(SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END), 0.0) as total_expense,
            COUNT(id) as total_count
        FROM transactions WHERE user_id = ?
        """,
        (user_id,),
    )
    r = cur.fetchone()
    conn.close()
    inc = float(r["total_income"]) if r else 0.0
    exp = float(r["total_expense"]) if r else 0.0
    return {"total_income": inc, "total_expense": exp, "net_balance": inc - exp, "total_count": int(r["total_count"]) if r else 0}

def add_or_update_daily_closing(
    user_id: int,
    closing_date: str,
    opening_cash: float,
    system_cash_sales: float,
    system_upi_sales: float,
    cash_expenses: float,
    actual_galla_cash: float,
    actual_upi_received: float,
    difference: float,
    notes: str = "",
) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id FROM daily_closings WHERE user_id = ? AND date = ?",
        (user_id, closing_date),
    )
    existing = cur.fetchone()
    if existing:
        cur.execute(
            """
            UPDATE daily_closings
            SET opening_cash = ?, system_cash_sales = ?, system_upi_sales = ?,
                cash_expenses = ?, actual_galla_cash = ?, actual_upi_received = ?,
                difference = ?, notes = ?
            WHERE id = ? AND user_id = ?
            """,
            (
                float(opening_cash),
                float(system_cash_sales),
                float(system_upi_sales),
                float(cash_expenses),
                float(actual_galla_cash),
                float(actual_upi_received),
                float(difference),
                notes.strip(),
                int(existing["id"]),
                user_id,
            ),
        )
        closing_id = int(existing["id"])
    else:
        cur.execute(
            """
            INSERT INTO daily_closings (
                user_id, date, opening_cash, system_cash_sales,
                system_upi_sales, cash_expenses, actual_galla_cash,
                actual_upi_received, difference, notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                closing_date,
                float(opening_cash),
                float(system_cash_sales),
                float(system_upi_sales),
                float(cash_expenses),
                float(actual_galla_cash),
                float(actual_upi_received),
                float(difference),
                notes.strip(),
            ),
        )
        closing_id = int(cur.lastrowid)
    conn.commit()
    conn.close()
    return closing_id

def get_daily_closing(user_id: int, closing_date: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM daily_closings WHERE user_id = ? AND date = ?",
        (user_id, closing_date),
    )
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None

# Invoices CRUD
def add_invoice(user_id: int, invoice_number: str, date: str, customer_name: str, customer_state: str,
                seller_state: str, items_json: str, subtotal: float, cgst: float, sgst: float, igst: float, total_amount: float) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO invoices (user_id, invoice_number, date, customer_name, customer_state, seller_state, items_json, subtotal, cgst, sgst, igst, total_amount)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (user_id, invoice_number.strip(), date, customer_name.strip(), customer_state.strip(), seller_state.strip(), items_json, float(subtotal), float(cgst), float(sgst), float(igst), float(total_amount)),
    )
    conn.commit()
    inv_id = cur.lastrowid
    conn.close()
    return inv_id

def get_invoices(user_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM invoices WHERE user_id = ? ORDER BY date DESC, id DESC", (user_id,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def delete_invoice(user_id: int, invoice_id: int) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM invoices WHERE id = ? AND user_id = ?", (invoice_id, user_id))
    conn.commit()
    deleted = cur.rowcount > 0
    conn.close()
    return deleted

# Loans CRUD
def add_loan(user_id: int, loan_name: str, principal: float, interest_rate: float, tenure_months: int, monthly_emi: float, total_interest: float, risk_level: str) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO loans (user_id, loan_name, principal, interest_rate, tenure_months, monthly_emi, total_interest, risk_level)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (user_id, loan_name.strip(), float(principal), float(interest_rate), int(tenure_months), float(monthly_emi), float(total_interest), risk_level.strip()),
    )
    conn.commit()
    lid = cur.lastrowid
    conn.close()
    return lid

def get_loans(user_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM loans WHERE user_id = ? ORDER BY id DESC", (user_id,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def delete_loan(user_id: int, loan_id: int) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM loans WHERE id = ? AND user_id = ?", (loan_id, user_id))
    conn.commit()
    deleted = cur.rowcount > 0
    conn.close()
    return deleted

# Udhaar / Credit Khata CRUD
def add_udhaar(
    user_id: int,
    customer_name: str,
    phone: str,
    amount: float,
    due_date: str,
    status: str = "Pending",
    entry_type: str = "Customer - Lena Hai",
    payment_mode: str = "Cash",
    paid_amount: float = 0.0,
) -> int:
    conn = get_connection()
    cur = conn.cursor()
    normalized_status = "Paid" if status.strip().lower() == "paid" else "Pending"
    normalized_entry_type = (
        "Supplier - Dena Hai"
        if "supplier" in entry_type.lower()
        else "Customer - Lena Hai"
    )
    normalized_payment_mode = (
        "UPI" if "upi" in payment_mode.lower() else "Cash"
    )
    paid_value = max(0.0, min(float(amount), float(paid_amount)))
    if paid_value >= float(amount):
        normalized_status = "Paid"
    cur.execute(
        """
        INSERT INTO udhaar (
            user_id, customer_name, phone, amount, due_date, status,
            entry_type, payment_mode, paid_amount
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            customer_name.strip(),
            phone.strip(),
            float(amount),
            due_date,
            normalized_status,
            normalized_entry_type,
            normalized_payment_mode,
            paid_value,
        ),
    )
    conn.commit()
    udhaar_id = cur.lastrowid
    conn.close()
    return udhaar_id

def get_udhaar(user_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM udhaar WHERE user_id = ? ORDER BY due_date ASC, id DESC",
        (user_id,),
    )
    rows = []
    for row in cur.fetchall():
        entry = dict(row)
        entry.setdefault(
            "entry_type",
            "Customer - Lena Hai",
        )
        entry.setdefault("payment_mode", "Cash")
        paid_amount = float(entry.get("paid_amount", 0) or 0)
        entry["paid_amount"] = paid_amount
        entry["remaining_amount"] = max(
            0.0,
            float(entry["amount"]) - paid_amount,
        )
        rows.append(entry)
    conn.close()
    return rows

def mark_udhaar_paid(user_id: int, udhaar_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM udhaar WHERE id = ? AND user_id = ?",
        (udhaar_id, user_id),
    )
    row = cur.fetchone()
    if not row:
        conn.close()
        return None

    entry = dict(row)
    if entry["status"] != "Paid":
        entry_type = str(entry.get("entry_type", "Customer - Lena Hai"))
        payment_mode = str(entry.get("payment_mode", "Cash"))
        original_amount = float(entry["amount"])
        already_paid = float(entry.get("paid_amount", 0) or 0)
        remaining = max(0.0, original_amount - already_paid)
        if remaining <= 0:
            remaining = original_amount
        cur.execute(
            "UPDATE udhaar SET status = 'Paid', paid_amount = amount "
            "WHERE id = ? AND user_id = ?",
            (udhaar_id, user_id),
        )
        transaction_type = (
            "expense"
            if "supplier" in entry_type.lower()
            else "income"
        )
        cur.execute(
            """
            INSERT INTO transactions (user_id, date, type, category, amount, description)
            VALUES (?, date('now'), ?, ?, ?, ?)
            """,
            (
                user_id,
                transaction_type,
                "Udhaar Recovery" if transaction_type == "income" else "Supplier Payment",
                remaining,
                f"{payment_mode} {'payment received from' if transaction_type == 'income' else 'payment paid to'} {entry['customer_name']}",
            ),
        )
        conn.commit()
        entry["status"] = "Paid"
        entry["paid_amount"] = original_amount
        entry["remaining_amount"] = 0.0
    conn.close()
    return entry

def record_udhaar_partial_payment(
    user_id: int,
    udhaar_id: int,
    payment_amount: float,
) -> Optional[Dict[str, Any]]:
    payment_amount = float(payment_amount)
    if payment_amount <= 0:
        return None

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM udhaar WHERE id = ? AND user_id = ?",
        (udhaar_id, user_id),
    )
    row = cur.fetchone()
    if not row:
        conn.close()
        return None

    entry = dict(row)
    original_amount = float(entry["amount"])
    already_paid = float(entry.get("paid_amount", 0) or 0)
    remaining = max(0.0, original_amount - already_paid)
    applied_amount = min(payment_amount, remaining)
    if applied_amount <= 0:
        conn.close()
        return entry

    new_paid = already_paid + applied_amount
    new_remaining = max(0.0, original_amount - new_paid)
    new_status = "Paid" if new_remaining <= 0 else "Pending"
    cur.execute(
        "UPDATE udhaar SET paid_amount = ?, status = ? "
        "WHERE id = ? AND user_id = ?",
        (new_paid, new_status, udhaar_id, user_id),
    )

    entry_type = str(entry.get("entry_type", "Customer - Lena Hai"))
    payment_mode = str(entry.get("payment_mode", "Cash"))
    transaction_type = "expense" if "supplier" in entry_type.lower() else "income"
    category = "Supplier Payment" if transaction_type == "expense" else "Udhaar Recovery"
    cur.execute(
        """
        INSERT INTO transactions (user_id, date, type, category, amount, description)
        VALUES (?, date('now'), ?, ?, ?, ?)
        """,
        (
            user_id,
            transaction_type,
            category,
            applied_amount,
            f"{payment_mode} {'payment paid to' if transaction_type == 'expense' else 'partial payment received from'} {entry['customer_name']}",
        ),
    )
    conn.commit()
    entry["paid_amount"] = new_paid
    entry["remaining_amount"] = new_remaining
    entry["status"] = new_status
    entry["applied_amount"] = applied_amount
    conn.close()
    return entry

# Inventory CRUD
def add_inventory_item(
    user_id: int,
    item_name: str,
    unit: str,
    stock_qty: float,
    min_stock: float,
    selling_price: float,
    gst_rate: float,
    expiry_date: str = "",
) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO inventory (
        user_id, item_name, unit, stock_qty, min_stock,
        selling_price, gst_rate, expiry_date
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            item_name.strip(),
            unit.strip() or "pcs",
            float(stock_qty),
            float(min_stock),
            float(selling_price),
            float(gst_rate),
            expiry_date,
        ),
    )
    conn.commit()
    item_id = cur.lastrowid
    conn.close()
    return item_id

def get_inventory(user_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM inventory WHERE user_id = ? ORDER BY item_name ASC",
        (user_id,),
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def restock_inventory(user_id: int, item_id: int, quantity: float) -> bool:
    if quantity < 0:
        return False
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE inventory
        SET stock_qty = stock_qty + ?
        WHERE id = ? AND user_id = ?
        """,
        (float(quantity), item_id, user_id),
    )
    conn.commit()
    updated = cur.rowcount > 0
    conn.close()
    return updated

def add_or_restock_inventory(
    user_id: int,
    item_name: str,
    quantity: float,
    unit: str = "pcs",
    min_stock: float = 5.0,
    selling_price: float = 0.0,
    gst_rate: float = 0.0,
    expiry_date: str = "",
) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM inventory WHERE user_id = ? AND lower(item_name) = lower(?)",
        (user_id, item_name.strip()),
    )
    row = cur.fetchone()
    if row:
        if expiry_date:
            cur.execute(
                "UPDATE inventory SET stock_qty = stock_qty + ?, expiry_date = ? "
                "WHERE id = ?",
                (float(quantity), expiry_date, int(row["id"])),
            )
        else:
            cur.execute(
                "UPDATE inventory SET stock_qty = stock_qty + ? WHERE id = ?",
                (float(quantity), int(row["id"])),
            )
    else:
        cur.execute(
            """
            INSERT INTO inventory (
                user_id, item_name, unit, stock_qty, min_stock,
                selling_price, gst_rate, expiry_date
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                item_name.strip(),
                unit,
                float(quantity),
                float(min_stock),
                float(selling_price),
                float(gst_rate),
                expiry_date,
            ),
        )
    conn.commit()
    conn.close()
    return True

def deduct_inventory(user_id: int, items: List[Dict[str, Any]]) -> None:
    conn = get_connection()
    cur = conn.cursor()
    for item in items:
        item_name = str(item.get("name", "")).strip()
        if not item_name:
            continue
        quantity = float(item.get("qty", 0) or 0)
        cur.execute(
            "SELECT id, stock_qty FROM inventory WHERE user_id = ? AND lower(item_name) = lower(?)",
            (user_id, item_name),
        )
        row = cur.fetchone()
        if not row:
            cur.execute(
                "SELECT id, stock_qty, item_name FROM inventory WHERE user_id = ?",
                (user_id,),
            )
            normalized_name = item_name.lower()
            for candidate in cur.fetchall():
                candidate_name = str(candidate["item_name"]).lower()
                if normalized_name in candidate_name or candidate_name in normalized_name:
                    row = candidate
                    break
        if row:
            remaining = max(0.0, float(row["stock_qty"]) - quantity)
            cur.execute(
                "UPDATE inventory SET stock_qty = ? WHERE id = ?",
                (remaining, int(row["id"])),
            )
    conn.commit()
    conn.close()

init_db()
