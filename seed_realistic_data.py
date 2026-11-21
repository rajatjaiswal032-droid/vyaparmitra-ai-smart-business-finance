import sqlite3
import random
from datetime import datetime, timedelta
import auth, database

database.init_db()
demo_user = auth.get_or_create_demo_user()
uid = demo_user["id"]

conn = sqlite3.connect("finance.db")
cur = conn.cursor()

for tbl in ("transactions", "invoices", "loans", "udhaar"):
    try:
        cur.execute(f"DELETE FROM {tbl} WHERE user_id = ?", (uid,))
    except Exception:
        pass

random.seed(42)
end_date = datetime(2026, 11, 20)
start_date = end_date - timedelta(days=240)

income_sources = [
    ("Daily Counter Cash & UPI Sales", "Retail Grocery", (4200, 9800)),
    ("Local Home Delivery & WhatsApp Orders", "Online & Delivery", (1800, 4900)),
    ("Monthly Family Ration Pack Orders", "Bulk Ration", (3500, 12500)),
    ("Amul Dairy, Bread & Cold Drinks Counter", "Dairy & Beverages", (1400, 3600)),
    ("Navratri & Diwali Bulk Samagri Orders", "Seasonal Sales", (4500, 16000)),
]

expense_sources = [
    ("ITC & HUL Distributor (Atta, Soap, Tea)", "Wholesale Stock", (8500, 22000)),
    ("Adani Wilmar & Fortune Edible Oil Agency", "Wholesale Stock", (6500, 18500)),
    ("Dal, Rice & Sugar Wholesale Mandi Bill", "Wholesale Stock", (7200, 19000)),
    ("Amul & Sanchi Milk Distributor Settlement", "Dairy Procurement", (2200, 4800)),
    ("MPPKVVCL Commercial Electricity Bill", "Utilities & Rent", (3800, 5600)),
    ("Shop Commercial Rent - Main Market", "Utilities & Rent", (12000, 12000)),
    ("Store Helper & Delivery Boy Monthly Salary", "Staff Wages", (14500, 14500)),
    ("Packaging, Carry Bags & Local Transport", "Logistics & Packaging", (900, 2600)),
]

curr = start_date
txn_count = 0

while curr <= end_date:
    date_str = curr.strftime("%Y-%m-%d")
    is_weekend = curr.weekday() in (5, 6)
    is_festival = curr.month in (10, 11)
    multiplier = (1.35 if is_festival else 1.0) * (1.15 if is_weekend else 1.0)

    desc, cat, (lo, hi) = random.choice(income_sources[:4])
    amt = round(random.uniform(lo, hi) * multiplier, 2)
    cur.execute(
        "INSERT INTO transactions (user_id, date, type, category, description, amount) VALUES (?, ?, ?, ?, ?, ?)",
        (uid, date_str, "Income", cat, desc, amt),
    )
    txn_count += 1

    if is_weekend or is_festival:
        desc2, cat2, (lo2, hi2) = income_sources[4] if is_festival else income_sources[2]
        amt2 = round(random.uniform(lo2, hi2) * multiplier, 2)
        cur.execute(
            "INSERT INTO transactions (user_id, date, type, category, description, amount) VALUES (?, ?, ?, ?, ?, ?)",
            (uid, date_str, "Income", cat2, desc2, amt2),
        )
        txn_count += 1

    if curr.weekday() in (1, 4):
        edesc, ecat, (elo, ehi) = random.choice(expense_sources[:4])
        eamt = round(random.uniform(elo, ehi) * (1.25 if is_festival else 1.0), 2)
        cur.execute(
            "INSERT INTO transactions (user_id, date, type, category, description, amount) VALUES (?, ?, ?, ?, ?, ?)",
            (uid, date_str, "Expense", ecat, edesc, eamt),
        )
        txn_count += 1

    if curr.day == 5:
        cur.execute(
            "INSERT INTO transactions (user_id, date, type, category, description, amount) VALUES (?, ?, ?, ?, ?, ?)",
            (uid, date_str, "Expense", "Utilities & Rent", "Shop Commercial Rent - Main Market", 12000.0),
        )
        txn_count += 1
    elif curr.day == 7:
        cur.execute(
            "INSERT INTO transactions (user_id, date, type, category, description, amount) VALUES (?, ?, ?, ?, ?, ?)",
            (uid, date_str, "Expense", "Staff Wages", "Store Helper & Delivery Boy Monthly Salary", 14500.0),
        )
        txn_count += 1
    elif curr.day == 15:
        cur.execute(
            "INSERT INTO transactions (user_id, date, type, category, description, amount) VALUES (?, ?, ?, ?, ?, ?)",
            (uid, date_str, "Expense", "Utilities & Rent", "MPPKVVCL Commercial Electricity Bill", round(random.uniform(4100, 5400), 2)),
        )
        txn_count += 1

    curr += timedelta(days=1)

sample_customers = [
    ("Shree Balaji Caterers, Ujjain", "Madhya Pradesh", 18450.0, 922.50),
    ("Hotel Rajhans Palace, Indore", "Madhya Pradesh", 32400.0, 3888.00),
    ("Narmada Tiffin Services, Bhopal", "Madhya Pradesh", 11200.0, 560.00),
    ("Khandelwal Sweets & Namkeen, Kota", "Rajasthan", 26800.0, 3216.00),
    ("Sai Kirana & General Stores, Akodia", "Madhya Pradesh", 15600.0, 780.00),
    ("Mahakal Hostel Mess, Ujjain", "Madhya Pradesh", 41500.0, 2075.00),
    ("Patel Agro Traders, Nagpur", "Maharashtra", 29300.0, 3516.00),
    ("Annapurna Bhojnalaya, Dewas", "Madhya Pradesh", 14900.0, 745.00),
]

for idx, (cname, cstate, sub, gst) in enumerate(sample_customers, start=1):
    inv_date = (end_date - timedelta(days=idx * 6)).strftime("%Y-%m-%d")
    inv_no = f"INV-2026-{1040 + idx}"
    cur.execute(
        "INSERT INTO invoices (user_id, invoice_no, customer_name, customer_state, subtotal, gst_amount, total_amount, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (uid, inv_no, cname, cstate, sub, gst, sub + gst, inv_date),
    )

try:
    udhaar_rows = [
        ("Rameshwar Sharma (Colony Ration)", "9826011234", 4850.0, "2026-11-25", "Pending"),
        ("Verma Ji Tea Stall & Snacks", "9425099812", 3200.0, "2026-11-23", "Pending"),
        ("Gupta Marriage Garden Catering", "9893144520", 14500.0, "2026-11-28", "Pending"),
        ("Sunita Devi (Monthly Home Ration)", "9755233410", 2650.0, "2026-11-18", "Paid"),
        ("Chouhan Dairy & Bakery", "9179088432", 6100.0, "2026-11-26", "Pending"),
    ]
    for cname, phone, amt, due, status in udhaar_rows:
        cur.execute(
            "INSERT INTO udhaar (user_id, customer_name, phone, amount, due_date, status) VALUES (?, ?, ?, ?, ?, ?)",
            (uid, cname, phone, amt, due, status),
        )
except Exception:
    pass

conn.commit()
conn.close()
print(f"SUCCESS: Inserted {txn_count} realistic transactions, {len(sample_customers)} GST invoices, and Udhaar records!")
