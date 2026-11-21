import sqlite3
import pandas as pd
import random
from datetime import datetime, timedelta
import auth, database

# 1. Fetch real open-source retail sales dataset from GitHub
PUBLIC_CSV_URL = "https://githubusercontent.com"
print("Downloading real retail dataset from web...")

try:
    df = pd.read_csv(PUBLIC_CSV_URL, encoding="latin1")
    print(f"Downloaded {len(df)} real retail rows from web!")
except Exception as e:
    raise SystemExit(f"Web download failed (check internet): {e}")

# 2. Initialize DB & get Demo Store user
database.init_db()
demo_user = auth.get_or_create_demo_user()
uid = demo_user["id"]

conn = sqlite3.connect("finance.db")
cur = conn.cursor()

# Clear previous demo transactions
cur.execute("DELETE FROM transactions WHERE user_id = ?", (uid,))

# 3. Map real dataset rows to recent 8 months & Indian Rupee (INR) retail equivalents
sample_df = df.dropna(subset=["Sales", "Profit", "Category", "Sub-Category"]).sample(n=250, random_state=42).reset_index(drop=True)

category_map = {
    "Office Supplies": ("Retail Grocery & Staples", "Wholesale Kirana Stock"),
    "Technology": ("Electronics & Home Utility", "Distributor Stock Purchase"),
    "Furniture": ("Store Fixtures & Packaging", "Shop Maintenance & Racks"),
}

base_end = datetime(2026, 11, 20)
inserted = 0

for idx, row in sample_df.iterrows():
    # Spread across the last 240 days (Apr 2026 - Nov 2026)
    txn_date = (base_end - timedelta(days=int((idx / len(sample_df)) * 240))).strftime("%Y-%m-%d")
    
    # Scale real sales value to realistic Indian retail INR (approx 25x-40x scale)
    raw_sales = float(row["Sales"])
    inr_sales = round(max(650.0, min(raw_sales * 32.0, 28500.0)), 2)
    
    # Derive realistic wholesale/operating expense from real dataset's Sales-Profit margin
    raw_profit = float(row["Profit"])
    margin_ratio = max(0.12, min(0.35, raw_profit / raw_sales)) if raw_sales > 0 else 0.20
    inr_expense = round(inr_sales * (1.0 - margin_ratio), 2)

    inc_cat, exp_cat = category_map.get(row["Category"], ("General Retail Sales", "Wholesale Procurement"))
    sub_cat = str(row["Sub-Category"])
    city = str(row.get("City", "Local Market"))

    # Insert Real-Data Derived Income
    cur.execute(
        "INSERT INTO transactions (user_id, date, type, category, description, amount) VALUES (?, ?, ?, ?, ?, ?)",
        (uid, txn_date, "Income", inc_cat, f"Retail Order - {sub_cat} ({city} Bulk)", inr_sales),
    )
    inserted += 1

    # Insert Corresponding Wholesale/Operating Expense every 2nd transaction
    if idx % 2 == 0:
        cur.execute(
            "INSERT INTO transactions (user_id, date, type, category, description, amount) VALUES (?, ?, ?, ?, ?, ?)",
            (uid, txn_date, "Expense", exp_cat, f"Supplier Invoice - {sub_cat} Restock", inr_expense),
        )
        inserted += 1

conn.commit()
conn.close()
print(f"SUCCESS: Imported {inserted} real-world web-sourced retail transactions into finance.db!")
