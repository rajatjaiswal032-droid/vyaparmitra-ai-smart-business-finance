"""Authentication and demo-store seeding helpers."""

from datetime import date, timedelta
from typing import Dict, Optional

import bcrypt

import database


DEMO_USERNAME = "demo_store"
DEMO_PASSWORD = "demo123"
DEMO_BUSINESS = "Sharma Kirana Store"


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def signup_user(
    username: str,
    password: str,
    business_name: str = "Kirana Store",
) -> Optional[Dict[str, object]]:
    """Create a business account and return its database row."""
    username = username.strip()
    business_name = business_name.strip() or "Kirana Store"

    if not username or not password:
        return None

    database.init_db()
    user_id = database.create_user(
        username=username,
        password_hash=_hash_password(password),
        business_name=business_name,
    )
    if user_id is None:
        return None

    return database.get_user_by_id(user_id)


def login_user(username: str, password: str) -> Optional[Dict[str, object]]:
    """Authenticate a user using a bcrypt password hash."""
    user = database.get_user_by_username(username)
    if not user:
        return None

    try:
        valid = bcrypt.checkpw(
            password.encode("utf-8"),
            str(user["password_hash"]).encode("utf-8"),
        )
    except (TypeError, ValueError):
        valid = False

    return user if valid else None


def get_or_create_demo_user() -> Dict[str, object]:
    """Get the demo account, seeding realistic six-month Kirana data once."""
    database.init_db()
    demo = database.get_user_by_username(DEMO_USERNAME)

    if demo:
        return demo

    demo = signup_user(DEMO_USERNAME, DEMO_PASSWORD, DEMO_BUSINESS)
    if demo is None:
        demo = database.get_user_by_username(DEMO_USERNAME)
    if demo is None:
        raise RuntimeError("Could not create the demo user")

    user_id = int(demo["id"])
    _seed_demo_transactions(user_id)
    return demo


def _seed_demo_transactions(user_id: int) -> None:
    today = date.today()
    income_profile = [
        (148000, 17800),
        (156500, 19200),
        (162000, 20500),
        (170500, 21600),
        (181000, 22800),
        (188500, 23600),
    ]

    for month_index, (income, expense) in enumerate(income_profile):
        month_number_index = (
            today.year * 12
            + (today.month - 1)
            - (5 - month_index)
        )
        year, month_zero_based = divmod(month_number_index, 12)
        month_number = month_zero_based + 1

        database.add_transaction(
            user_id,
            f"{year}-{month_number:02d}-05",
            "income",
            "Retail Sales",
            income * 0.52,
            "Daily grocery aur household items ki cash/UPI sale",
        )
        database.add_transaction(
            user_id,
            f"{year}-{month_number:02d}-12",
            "income",
            "Wholesale Sales",
            income * 0.48,
            "Wholesaler aur local shopkeepers ko supply",
        )
        database.add_transaction(
            user_id,
            f"{year}-{month_number:02d}-03",
            "expense",
            "Inventory",
            expense * 0.64,
            "Wholesale market se atta, dal, rice, oil aur snacks",
        )
        database.add_transaction(
            user_id,
            f"{year}-{month_number:02d}-08",
            "expense",
            "Rent",
            14500,
            "Monthly Kirana shop rent",
        )
        database.add_transaction(
            user_id,
            f"{year}-{month_number:02d}-16",
            "expense",
            "Utilities",
            1850,
            "Bijli aur municipal water bill",
        )
        database.add_transaction(
            user_id,
            f"{year}-{month_number:02d}-21",
            "expense",
            "Transport",
            2450,
            "Goods pickup aur local delivery transport",
        )

    existing_udhaar = database.get_udhaar(user_id)
    if not existing_udhaar:
        today = date.today()
        samples = [
            ("Ramesh Yadav", "9876543210", 2450.0, today + timedelta(days=3), "Pending"),
            ("Sunita Sharma", "9876501234", 1800.0, today + timedelta(days=7), "Pending"),
            ("Mohit Traders", "9811122233", 5200.0, today - timedelta(days=2), "Pending"),
            ("Amit Kumar", "9898989898", 950.0, today - timedelta(days=10), "Paid"),
        ]
        for customer_name, phone, amount, due_date, status in samples:
            database.add_udhaar(
                user_id,
                customer_name,
                phone,
                amount,
                due_date.strftime("%Y-%m-%d"),
                status,
            )

    inventory_items = [
        ("Aashirvaad Atta 10kg", "pack", 18.0, 5.0, 520.0, 5.0, (date.today() + timedelta(days=95)).strftime("%Y-%m-%d")),
        ("Fortune Oil 1L", "bottle", 4.0, 8.0, 185.0, 5.0, (date.today() + timedelta(days=18)).strftime("%Y-%m-%d")),
        ("Sugar 1kg", "pack", 25.0, 6.0, 48.0, 5.0, (date.today() + timedelta(days=180)).strftime("%Y-%m-%d")),
        ("Basmati Rice 5kg", "pack", 12.0, 4.0, 450.0, 5.0, (date.today() + timedelta(days=120)).strftime("%Y-%m-%d")),
        ("Tata Salt 1kg", "pack", 3.0, 10.0, 28.0, 0.0, (date.today() + timedelta(days=240)).strftime("%Y-%m-%d")),
        ("Toor Dal 1kg", "pack", 14.0, 5.0, 160.0, 5.0, (date.today() + timedelta(days=22)).strftime("%Y-%m-%d")),
        ("Parle-G Biscuits", "pack", 32.0, 8.0, 10.0, 18.0, (date.today() + timedelta(days=75)).strftime("%Y-%m-%d")),
        ("Amul Milk 1L", "pack", 14.0, 12.0, 66.0, 0.0, (date.today() + timedelta(days=3)).strftime("%Y-%m-%d")),
    ]
    existing_inventory = database.get_inventory(user_id)
    if not existing_inventory:
        for item in inventory_items:
            database.add_inventory_item(user_id, *item)


def reset_demo_user() -> Dict[str, object]:
    """Restore the demo store to a clean, freshly seeded presentation state."""
    database.init_db()
    existing = database.get_user_by_username(DEMO_USERNAME)

    if existing:
        conn = database.get_connection()
        cur = conn.cursor()
        user_id = int(existing["id"])
        cur.execute("DELETE FROM transactions WHERE user_id = ?", (user_id,))
        cur.execute("DELETE FROM invoices WHERE user_id = ?", (user_id,))
        cur.execute("DELETE FROM loans WHERE user_id = ?", (user_id,))
        cur.execute("DELETE FROM udhaar WHERE user_id = ?", (user_id,))
        cur.execute("DELETE FROM inventory WHERE user_id = ?", (user_id,))
        cur.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()

    demo = signup_user(DEMO_USERNAME, DEMO_PASSWORD, DEMO_BUSINESS)
    if demo is None:
        raise RuntimeError("Could not reset the demo user")

    _seed_demo_transactions(int(demo["id"]))
    return demo