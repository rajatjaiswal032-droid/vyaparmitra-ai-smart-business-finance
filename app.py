import json
import uuid
from datetime import date, timedelta
from io import BytesIO
from urllib.parse import quote

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import qrcode
from gtts import gTTS

import ai_assistant
import auth
import database
import forecasting
import gst_invoice
import loan_calculator


st.set_page_config(
    page_title="VyaparMitra AI - Smart Business Finance",
    page_icon="📊",
    layout="wide",
)


st.markdown(
    """
    <style>
    :html, body, [class*="css"] { font-family: "Inter", "Segoe UI", sans-serif; }
    .block-container { padding-top: 2rem; padding-bottom: 3rem; max-width: 1500px; }
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #f7f9fc 0%, #eef4f8 100%);
    }
    [data-testid="stHeader"] { background: rgba(255,255,255,0.78); }
    [data-testid="stSidebar"] {
        background: #102a43;
    }
    [data-testid="stSidebar"] * { color: #f7fafc; }
    [data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #e8edf3;
        border-radius: 18px;
        padding: 18px 20px;
        box-shadow: 0 8px 24px rgba(16,42,67,0.07);
    }
    [data-testid="stMetricLabel"] { color: #60758a; font-weight: 600; }
    [data-testid="stMetricValue"] { color: #173f5f; font-size: 28px; }
    .stTabs [data-baseweb="tab"] {
        border-radius: 12px 12px 0 0;
        padding: 10px 16px;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background: #e7f1ff;
        color: #1677a8;
    }
    .brand-card {
        background: linear-gradient(135deg, #0b6e99 0%, #1f9d8a 100%);
        color: white;
        border-radius: 24px;
        padding: 34px;
        text-align: center;
        box-shadow: 0 18px 40px rgba(11,110,153,0.18);
    }
    .brand-card h1 { margin: 0; color: white; }
    .brand-card p { margin: 8px 0 0; opacity: 0.92; }
    .alert-red {
        background: #fff1f0; border: 1px solid #ffccc7; color: #cf1322;
        border-radius: 14px; padding: 14px 18px; font-weight: 700;
    }
    .status-safe {
        background: #eaffea; color: #15803d; border: 1px solid #bbf7d0;
        border-radius: 999px; padding: 8px 14px; text-align: center; font-weight: 700;
    }
    .status-moderate {
        background: #fff7d6; color: #a16207; border: 1px solid #fde68a;
        border-radius: 999px; padding: 8px 14px; text-align: center; font-weight: 700;
    }
    .status-high {
        background: #ffecec; color: #c81e1e; border: 1px solid #fecaca;
        border-radius: 999px; padding: 8px 14px; text-align: center; font-weight: 700;
    }
    .summary-card {
        background: white; border: 1px solid #e8edf3; border-radius: 16px;
        padding: 18px; box-shadow: 0 8px 22px rgba(16,42,67,0.06);
    }
    div.stButton > button {
        border-radius: 12px; min-height: 44px; font-weight: 700;
        border: 1px solid #d9e2ec;
    }
    div.stButton > button[kind="primary"] {
        background: #0b7fab; border: none; color: white;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def format_inr(amount: float) -> str:
    absolute = abs(float(amount))
    value = f"{absolute:.2f}"
    whole, decimal = value.split(".", 1)
    sign = "-" if float(amount) < 0 else ""

    if len(whole) <= 3:
        return f"₹{sign}{whole}.{decimal}"

    last_three = whole[-3:]
    prefix = whole[:-3]
    grouped_prefix = ""
    while len(prefix) > 2:
        grouped_prefix = "," + prefix[-2:] + grouped_prefix
        prefix = prefix[:-2]
    if prefix:
        grouped_prefix = prefix + grouped_prefix
    return f"₹{sign}{grouped_prefix},{last_three}.{decimal}"




def init_state() -> None:
    defaults = {
        "authenticated": False,
        "user": None,
        "chat_history": [],
        "store_gstin": "27ABCDE1234F1Z5",
        "store_state": "Madhya Pradesh",
        "store_upi_id": "8461919697@ybl",
        "upi_payee_name": "",
        "invoice_items": [
            {"name": "Rice 5kg", "qty": 1.0, "price": 450.0, "gst_rate": 5.0}
        ],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_state()
database.init_db()


def auth_screen() -> None:
    st.markdown(
        """
        <div class="brand-card">
            <h1>📊 VyaparMitra AI — Smart Business Finance</h1>
            <p>Smart Business Finance for India’s growing Kirana stores</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("")

    col_left, col_center, col_right = st.columns([1, 2, 1])
    with col_center:
        if st.button(
            "🚀 1-Click Demo Store Login (Kirana Store)",
            type="primary",
            use_container_width=True,
        ):
            user = auth.get_or_create_demo_user()
            st.session_state.authenticated = True
            st.session_state.user = user
            st.session_state.store_gstin = "27ABCDE1234F1Z5"
            st.session_state.store_state = "Maharashtra"
            st.session_state.chat_history = []
            st.rerun()

        login_tab, register_tab = st.tabs(["🔐 Login", "📝 Register New Business"])

        with login_tab:
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Login", type="primary")
            if submitted:
                user = auth.login_user(username, password)
                if user:
                    st.session_state.authenticated = True
                    st.session_state.user = user
                    st.rerun()
                else:
                    st.error("Galat username ya password.")

        with register_tab:
            indian_states = [
                "Madhya Pradesh", "Maharashtra", "Delhi", "Rajasthan", "Gujarat",
                "Uttar Pradesh", "Karnataka", "Tamil Nadu", "Telangana", "West Bengal",
            ]
            with st.form("register_form"):
                business_name = st.text_input("Store Name", "My Kirana Store")
                gstin = st.text_input("GSTIN", "23ABCDE1234F1Z5")
                state = st.selectbox(
                    "State",
                    indian_states,
                    index=indian_states.index("Madhya Pradesh"),
                )
                username = st.text_input("Create Username")
                password = st.text_input("Create Password", type="password")
                submitted = st.form_submit_button("Create Account", type="primary")
            if submitted:
                user = auth.signup_user(username, password, business_name)
                if user:
                    st.session_state.authenticated = True
                    st.session_state.user = user
                    st.session_state.store_gstin = gstin or "NOT PROVIDED"
                    st.session_state.store_state = state
                    st.success("Business account created.")
                    st.rerun()
                else:
                    st.error("Username already exists or required details are missing.")


def transactions_dataframe(user_id: int) -> pd.DataFrame:
    transactions = database.get_transactions(user_id)
    if not transactions:
        return pd.DataFrame(columns=["date", "type", "amount", "category", "description"])

    frame = pd.DataFrame(transactions)
    frame["type"] = frame["type"].str.title()
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    return frame


def generate_sample_kirana_receipt() -> bytes:
    """Create a realistic, OCR-friendly Kirana store bill image."""
    image = Image.new("RGB", (760, 900), "white")
    draw = ImageDraw.Draw(image)
    try:
        regular = ImageFont.truetype("arial.ttf", 34)
        small = ImageFont.truetype("arial.ttf", 24)
        bold = ImageFont.truetype("arialbd.ttf", 38)
    except OSError:
        regular = ImageFont.load_default()
        small = ImageFont.load_default()
        bold = ImageFont.load_default()

    y = 35
    draw.text((230, y), "SHARMA KIRANA STORE", fill="black", font=bold)
    y += 55
    draw.text((255, y), "GSTIN: 27ABCDE1234F1Z5", fill="black", font=small)
    y += 42
    draw.text((270, y), "MUMBAI - 400001", fill="black", font=small)
    y += 45
    draw.line((40, y, 720, y), fill="black", width=3)
    y += 30
    draw.text((50, y), "ITEM", fill="black", font=regular)
    draw.text((520, y), "QTY", fill="black", font=regular)
    draw.text((635, y), "AMOUNT", fill="black", font=regular)
    y += 45
    draw.line((40, y, 720, y), fill="black", width=2)

    rows = [
        ("Aashirvaad Atta 5kg", "1", "Rs. 245"),
        ("Tata Salt 1kg", "2", "Rs. 48"),
        ("Fortune Sunflower Oil", "1", "Rs. 185"),
        ("Amul Milk 1L", "3", "Rs. 99"),
        ("Parle-G Biscuits", "4", "Rs. 80"),
    ]
    for name, qty, amount in rows:
        y += 55
        draw.text((50, y), name, fill="black", font=small)
        draw.text((530, y), qty, fill="black", font=small)
        draw.text((635, y), amount, fill="black", font=small)

    y += 65
    draw.line((40, y, 720, y), fill="black", width=2)
    y += 35
    draw.text((430, y), "SUBTOTAL", fill="black", font=regular)
    draw.text((635, y), "Rs. 657", fill="black", font=regular)
    y += 55
    draw.text((430, y), "GST 5%", fill="black", font=regular)
    draw.text((635, y), "Rs. 33", fill="black", font=regular)
    y += 55
    draw.line((430, y, 720, y), fill="black", width=2)
    y += 25
    draw.text((430, y), "TOTAL", fill="black", font=bold)
    draw.text((635, y), "Rs. 690", fill="black", font=bold)
    y += 75
    draw.text((220, y), "Date: 20-11-2026  |  Cash/UPI", fill="black", font=small)
    y += 45
    draw.text((250, y), "Thank you for shopping!", fill="black", font=small)

    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def financial_overview(user_id: int) -> None:
    summary = database.get_financial_summary(user_id)
    transactions = database.get_transactions(user_id)
    forecast_df = pd.DataFrame(
        [
            {
                "date": item["date"],
                "type": item["type"].title(),
                "amount": item["amount"],
            }
            for item in transactions
        ]
    )
    if forecast_df.empty:
        forecast_df = pd.DataFrame(columns=["date", "type", "amount"])
    forecast = forecasting.analyze_and_forecast(forecast_df)

    revenue = float(summary["total_income"])
    expenses = float(summary["total_expense"])
    net_profit = float(summary["net_balance"])
    projected = float(forecast["predicted_balance"])

    st.subheader("📊 Financial Overview & Forecast")
    low_stock_items = [
        item for item in database.get_inventory(user_id)
        if float(item["stock_qty"]) < float(item["min_stock"])
    ]
    if low_stock_items:
        names = ", ".join(str(item["item_name"]) for item in low_stock_items[:4])
        st.warning(f"⚠️ Low Stock Alert: {names}. Inventory tab mein restock karein.")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("💰 Total Revenue", format_inr(revenue))
    k2.metric("💸 Total Expenses", format_inr(expenses))
    k3.metric("📈 Net Profit / Loss", format_inr(net_profit))
    k4.metric("🔮 Next Month Projected Balance", format_inr(projected))

    near_expiry_items = []
    for item in database.get_inventory(user_id):
        expiry_text = str(item.get("expiry_date", "") or "").strip()
        if expiry_text:
            try:
                expiry_date = date.fromisoformat(expiry_text)
                if date.today() <= expiry_date <= date.today() + timedelta(days=30):
                    near_expiry_items.append((item["item_name"], expiry_date))
            except ValueError:
                pass
    if near_expiry_items:
        expiry_names = ", ".join(
            f"{name} ({expiry_date.strftime('%d-%m-%Y')})"
            for name, expiry_date in near_expiry_items
        )
        st.warning(
            f"⏳ Expiring Within 30 Days: {expiry_names}. "
            "Pehle FEFO clearance karein."
        )

    with st.expander("🌙 Daily Galla Closing (Raat Ka Hisaab)", expanded=False):
        closing_date = date.today()
        today_transactions = [
            item for item in transactions
            if str(item["date"])[:10] == closing_date.strftime("%Y-%m-%d")
        ]
        system_cash_sales = 0.0
        system_upi_sales = 0.0
        for item in today_transactions:
            if str(item["type"]).lower() == "income":
                text = f"{item['description']} {item['category']}".lower()
                if "upi" in text:
                    system_upi_sales += float(item["amount"])
                else:
                    system_cash_sales += float(item["amount"])
        cash_expenses = sum(
            float(item["amount"])
            for item in today_transactions
            if str(item["type"]).lower() == "expense"
            and "upi" not in f"{item['description']} {item['category']}".lower()
        )

        saved_closing = database.get_daily_closing(
            user_id,
            closing_date.strftime("%Y-%m-%d"),
        )
        saved_opening = float(saved_closing["opening_cash"]) if saved_closing else 0.0
        saved_actual_cash = (
            float(saved_closing["actual_galla_cash"]) if saved_closing else 0.0
        )
        saved_actual_upi = (
            float(saved_closing["actual_upi_received"]) if saved_closing else 0.0
        )

        gc1, gc2, gc3 = st.columns(3)
        opening_cash = gc1.number_input(
            "Opening Cash (₹)",
            min_value=0.0,
            value=saved_opening,
            step=100.0,
        )
        actual_galla_cash = gc2.number_input(
            "Actual Cash in Galla (₹)",
            min_value=0.0,
            value=saved_actual_cash,
            step=100.0,
        )
        actual_upi_received = gc3.number_input(
            "Actual UPI Received (₹)",
            min_value=0.0,
            value=saved_actual_upi,
            step=100.0,
        )

        expected_closing_cash = (
            opening_cash + system_cash_sales - cash_expenses
        )
        galla_difference = actual_galla_cash - expected_closing_cash
        st.caption(
            f"System Cash Sales: {format_inr(system_cash_sales)}  |  "
            f"Cash Expenses: {format_inr(cash_expenses)}  |  "
            f"Expected Galla Cash: {format_inr(expected_closing_cash)}"
        )
        if abs(galla_difference) < 0.01:
            st.markdown(
                '<div class="status-safe">✅ Galla Matched</div>',
                unsafe_allow_html=True,
            )
        elif galla_difference < 0:
            st.markdown(
                f'<div class="status-high">⚠️ Cash Short by {format_inr(abs(galla_difference))}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="status-moderate">⚠️ Cash Excess by {format_inr(galla_difference)}</div>',
                unsafe_allow_html=True,
            )

        closing_notes = st.text_area(
            "Notes",
            value=saved_closing["notes"] if saved_closing else "",
        )
        if st.button("💾 Save Daily Closing", type="primary"):
            database.add_or_update_daily_closing(
                user_id,
                closing_date.strftime("%Y-%m-%d"),
                opening_cash,
                system_cash_sales,
                system_upi_sales,
                cash_expenses,
                actual_galla_cash,
                actual_upi_received,
                galla_difference,
                closing_notes,
            )
            st.success("Daily galla closing save ho gaya.")

    preview_alert = st.toggle(
        "Preview Cash Shortage Alert",
        value=bool(forecast["shortage_alert"]),
        help="Turn on to preview the alert banner for presentations.",
    )
    if forecast["shortage_alert"] or preview_alert:
        st.markdown(
            '<div class="alert-red">🚨 Cash Shortage Alert: Projected closing balance is below ₹10,000. '
            "Inventory aur discretionary expenses control mein rakhein.</div>",
            unsafe_allow_html=True,
        )

    monthly = forecast["monthly_df"]
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=monthly["Month"],
            y=monthly["Monthly Income"],
            name="Income",
            marker_color="#24a148",
        )
    )
    fig.add_trace(
        go.Bar(
            x=monthly["Month"],
            y=monthly["Monthly Expense"],
            name="Expense",
            marker_color="#f97316",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=monthly["Month"],
            y=monthly["Net Profit/Loss"],
            name="Net Profit/Loss",
            mode="lines+markers",
            yaxis="y",
            line={"color": "#1677a8", "width": 3},
        )
    )
    fig.update_layout(
        barmode="group",
        height=390,
        margin={"l": 20, "r": 20, "t": 20, "b": 20},
        legend={"orientation": "h", "y": 1.08},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0)",
        xaxis_title="Month",
        yaxis_title="INR",
    )
    chart_col, donut_col = st.columns([1.35, 0.65])
    chart_col.plotly_chart(fig, use_container_width=True)

    expense_categories = (
        pd.DataFrame(
            [
                {"category": item["category"], "amount": float(item["amount"])}
                for item in transactions
                if item["type"].lower() == "expense"
            ]
        )
        if transactions
        else pd.DataFrame(columns=["category", "amount"])
    )
    if not expense_categories.empty:
        top_expenses = [
            (str(row.category), float(row.amount))
            for row in expense_categories.groupby("category", as_index=False)["amount"]
            .sum()
            .sort_values("amount", ascending=False)
            .head(5)
            .itertuples(index=False)
        ]
    else:
        top_expenses = []

    if not expense_categories.empty:
        category_totals = (
            expense_categories.groupby("category", as_index=False)["amount"]
            .sum()
            .sort_values("amount", ascending=False)
        )
        donut = go.Figure(
            go.Pie(
                labels=category_totals["category"],
                values=category_totals["amount"],
                hole=0.58,
                textinfo="percent",
                hovertemplate="%{label}: ₹%{value:,.0f}<extra></extra>",
            )
        )
        donut.update_layout(
            title="Expenses by Category",
            height=390,
            margin={"l": 20, "r": 20, "t": 55, "b": 20},
            showlegend=True,
        )
        donut_col.plotly_chart(donut, use_container_width=True)
    else:
        donut_col.info("Expense category data available nahi hai.")

    goal = st.number_input(
        "🎯 Monthly Profit Goal (₹)",
        min_value=0.0,
        value=100000.0,
        step=5000.0,
    )
    current_month_profit = float(monthly.iloc[-1]["Net Profit/Loss"]) if not monthly.empty else net_profit
    goal_progress = 0.0 if goal <= 0 else min(current_month_profit / goal, 1.0)
    st.progress(
        float(max(0.0, goal_progress)),
        text=f"Current: {format_inr(current_month_profit)} / Goal: {format_inr(goal)}",
    )

    if st.button(
        "📄 Download Monthly P&L Report (PDF)",
        type="primary",
        use_container_width=False,
    ):
        report_data = {
            "store_name": st.session_state.user.get("business_name", "Kirana Store"),
            "report_month": date.today().strftime("%B %Y"),
            "total_revenue": revenue,
            "total_expenses": expenses,
            "net_profit": net_profit,
            "projected_balance": projected,
            "top_expense_categories": top_expenses,
            "shortage_alert": forecast["shortage_alert"],
        }
        report_pdf = gst_invoice.generate_pnl_pdf(report_data)
        st.download_button(
            "Download P&L PDF",
            data=report_pdf,
            file_name=f"PnL-{date.today().strftime('%Y-%m')}.pdf",
            mime="application/pdf",
        )

    with st.expander("📂 Import / Export Data (CSV & Excel)", expanded=False):
        export_columns = ["date", "type", "category", "description", "amount"]
        export_df = (
            pd.DataFrame(transactions)[export_columns]
            if transactions
            else pd.DataFrame(columns=export_columns)
        )
        export_df["type"] = export_df["type"].str.title()

        export_left, export_right = st.columns(2)
        export_left.download_button(
            "⬇️ Download Transactions CSV",
            data=export_df.to_csv(index=False).encode("utf-8"),
            file_name=f"transactions-{date.today().strftime('%Y-%m-%d')}.csv",
            mime="text/csv",
            use_container_width=True,
        )

        excel_buffer = BytesIO()
        with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
            export_df.to_excel(writer, index=False, sheet_name="Transactions")
        export_right.download_button(
            "⬇️ Download Transactions Excel",
            data=excel_buffer.getvalue(),
            file_name=f"transactions-{date.today().strftime('%Y-%m-%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

        uploaded_statement = st.file_uploader(
            "⬆️ Upload bank/store statement",
            type=["csv", "xlsx", "xls"],
            key="statement_import",
        )
        if uploaded_statement:
            try:
                if uploaded_statement.name.lower().endswith(".csv"):
                    import_df = pd.read_csv(uploaded_statement)
                else:
                    import_df = pd.read_excel(uploaded_statement)
                import_df.columns = [str(column).strip().lower() for column in import_df.columns]

                meal_columns = {"meal_name", "quantity_prepared", "quantity_consumed"}
                is_meal_import = meal_columns.issubset(set(import_df.columns))
                if is_meal_import:
                    st.info(
                        "Meal plan format detected: Income = consumed × ₹60; "
                        "Expense = prepared × ₹35."
                    )
                    if st.button("Bulk Import Transactions", type="primary"):
                        imported = 0
                        for row in import_df.to_dict("records"):
                            meal_name = str(row["meal_name"]).strip()
                            quantity_prepared = pd.to_numeric(
                                row["quantity_prepared"], errors="coerce"
                            )
                            quantity_consumed = pd.to_numeric(
                                row["quantity_consumed"], errors="coerce"
                            )
                            if (
                                not meal_name
                                or meal_name.lower() == "nan"
                                or pd.isna(quantity_prepared)
                                or pd.isna(quantity_consumed)
                            ):
                                continue

                            prepared_qty = max(0.0, float(quantity_prepared))
                            consumed_qty = max(0.0, float(quantity_consumed))
                            if "date" in import_df.columns:
                                parsed_date = pd.to_datetime(row["date"], errors="coerce")
                                transaction_date = (
                                    parsed_date.strftime("%Y-%m-%d")
                                    if not pd.isna(parsed_date)
                                    else date.today().strftime("%Y-%m-%d")
                                )
                            else:
                                transaction_date = date.today().strftime("%Y-%m-%d")

                            income_amount = round(consumed_qty * 60.0, 2)
                            expense_amount = round(prepared_qty * 35.0, 2)
                            if income_amount > 0:
                                database.add_transaction(
                                    user_id,
                                    transaction_date,
                                    "income",
                                    "Food & Meal Sales",
                                    income_amount,
                                    f"Meal sale: {meal_name}",
                                )
                                imported += 1
                            if expense_amount > 0:
                                database.add_transaction(
                                    user_id,
                                    transaction_date,
                                    "expense",
                                    "Raw Material & Prep",
                                    expense_amount,
                                    f"Meal preparation: {meal_name}",
                                )
                                imported += 1
                        st.success(f"{imported} meal transactions successfully imported.")
                        st.rerun()
                else:
                    required = {"date", "type", "category", "description", "amount"}
                    missing = required.difference(import_df.columns)
                    if missing:
                        st.error("Missing columns: " + ", ".join(sorted(missing)))
                    elif st.button("Bulk Import Transactions", type="primary"):
                        imported = 0
                        for row in import_df.to_dict("records"):
                            normalized_type = str(row["type"]).strip().lower()
                            if normalized_type not in {"income", "expense"}:
                                continue
                            parsed_date = pd.to_datetime(row["date"], errors="coerce")
                            parsed_amount = pd.to_numeric(row["amount"], errors="coerce")
                            if pd.isna(parsed_date) or pd.isna(parsed_amount) or float(parsed_amount) <= 0:
                                continue
                            database.add_transaction(
                                user_id,
                                parsed_date.strftime("%Y-%m-%d"),
                                normalized_type,
                                str(row["category"]).strip() or "Other",
                                float(parsed_amount),
                                str(row["description"]).strip(),
                            )
                            imported += 1
                        st.success(f"{imported} transactions successfully imported.")
                        st.rerun()
            except Exception as exc:
                st.error(f"Import could not be completed: {exc}")

    st.markdown("### 📋 Recent Transactions")
    if transactions:
        recent = pd.DataFrame(transactions)
        recent["date"] = pd.to_datetime(recent["date"], errors="coerce").dt.strftime("%Y-%m-%d")
        recent["amount"] = recent["amount"].map(format_inr)
        recent = recent[
            ["date", "type", "category", "description", "amount"]
        ].rename(
            columns={
                "date": "Date",
                "type": "Type",
                "category": "Category",
                "description": "Description",
                "amount": "Amount",
            }
        )
        search_text = st.text_input("🔎 Search transactions", "")
        if search_text.strip():
            mask = recent.astype(str).apply(
                lambda column: column.str.contains(search_text.strip(), case=False, na=False)
            ).any(axis=1)
            recent = recent[mask]
        st.dataframe(recent.head(50), use_container_width=True, hide_index=True)
    else:
        st.info("Abhi koi transaction nahi hai.")

    with st.expander("➕ Add Manual Transaction", expanded=False):
        with st.form("manual_transaction"):
            c1, c2, c3 = st.columns(3)
            with c1:
                transaction_type = st.selectbox("Type", ["Income", "Expense"])
                category = st.text_input("Category", "Retail Sales")
            with c2:
                transaction_date = st.date_input("Date", date.today())
                amount = st.number_input("Amount (₹)", min_value=0.0, step=100.0)
            with c3:
                description = st.text_area("Description", "Kirana store transaction")
            submitted = st.form_submit_button("💾 Save Transaction", type="primary")
        if submitted:
            if amount <= 0:
                st.error("Amount ₹0 se zyada hona chahiye.")
            else:
                database.add_transaction(
                    user_id,
                    transaction_date.strftime("%Y-%m-%d"),
                    transaction_type.lower(),
                    category,
                    amount,
                    description,
                )
                st.success("Transaction saved.")
                st.rerun()


def receipt_scanner(user_id: int) -> None:
    st.subheader("📸 AI Receipt Scanner")
    left, right = st.columns(2)

    with left:
        uploaded = st.file_uploader(
            "Upload receipt image (JPG, PNG)",
            type=["jpg", "jpeg", "png"],
            key="receipt_upload",
        )
        if uploaded:
            image_bytes = uploaded.getvalue()
            st.image(image_bytes, caption="Receipt Preview", use_container_width=True)

        camera_image = st.camera_input("📷 Take Photo of Paper Bill")
        if camera_image:
            st.image(camera_image, caption="Camera Bill Preview", use_container_width=True)

        if st.button("🧪 Generate Sample Kirana Bill Image", type="primary"):
            sample_bytes = generate_sample_kirana_receipt()
            st.session_state.receipt_generated = sample_bytes
            st.session_state.receipt_extracted = ai_assistant.extract_receipt_data(
                sample_bytes
            )

        if st.session_state.get("receipt_generated"):
            st.image(
                st.session_state["receipt_generated"],
                caption="Generated Sample Kirana Receipt",
                use_container_width=True,
            )

        if st.button("🔍 Scan Bill with AI", type="primary", use_container_width=True):
            scan_source = st.session_state.get("receipt_generated")
            if uploaded:
                scan_source = uploaded.getvalue()
            if camera_image:
                scan_source = camera_image.getvalue()
            if scan_source:
                with st.spinner("Gemini Vision receipt ko read kar raha hai..."):
                    extracted = ai_assistant.extract_receipt_data(scan_source)
                st.session_state.receipt_extracted = extracted
                if extracted.get("offline"):
                    st.info(
                        extracted.get(
                            "summary",
                            "Offline Mode: Please verify details manually",
                        )
                    )
            else:
                st.warning("Pehle bill image upload karein ya sample bill generate karein.")

    extracted = st.session_state.get("receipt_extracted", {})
    with right:
        vendor = st.text_input("Vendor Name", extracted.get("vendor", ""))
        receipt_date = st.text_input("Date", extracted.get("date", ""))
        invoice_no = st.text_input("Invoice No.", extracted.get("invoice_no", ""))
        amount = st.number_input(
            "Amount (₹)",
            min_value=0.0,
            value=float(
                extracted.get("total_amount", extracted.get("amount", 0)) or 0
            ),
            step=50.0,
        )
        gst_amount = st.number_input(
            "GST Amount (₹)",
            min_value=0.0,
            value=float(extracted.get("gst_amount", 0) or 0),
            step=10.0,
        )
        category = st.selectbox(
            "Category",
            ["Inventory", "Rent", "Utilities", "Transport", "Other"],
            index=(
                ["Inventory", "Rent", "Utilities", "Transport", "Other"].index(
                    extracted.get("category", "Inventory")
                )
                if extracted.get("category", "Inventory")
                in ["Inventory", "Rent", "Utilities", "Transport", "Other"]
                else 0
            ),
        )
        if extracted.get("offline"):
            st.caption("Offline mode: API missing or image extraction unavailable.")

        if extracted:
            st.markdown('<div class="summary-card">', unsafe_allow_html=True)
            st.markdown("### 🧾 AI Bill Summary")
            st.write(
                extracted.get(
                    "hinglish_summary",
                    "Bill scan complete. Item details aur GST verify karein.",
                )
            )
            items = extracted.get("items", [])
            if items:
                item_df = pd.DataFrame(items)
                st.dataframe(
                    item_df.rename(
                        columns={"name": "Item", "qty": "Qty", "price": "Price (₹)"}
                    ),
                    use_container_width=True,
                    hide_index=True,
                )
            duplicate = False
            for existing in database.get_transactions(user_id):
                if (
                    existing["type"].lower() == "expense"
                    and float(existing["amount"]) == float(amount)
                    and str(existing["date"]) == receipt_date
                    and vendor.lower() in str(existing["description"]).lower()
                ):
                    duplicate = True
                    break
            if duplicate:
                st.warning("⚠️ Duplicate-bill possible hai: same vendor, amount aur date ka record mila.")
            st.markdown("</div>", unsafe_allow_html=True)

        action_save, action_restock = st.columns(2)
        if action_save.button("💾 Save to Expenses", type="primary", use_container_width=True):
            if amount <= 0:
                st.error("Valid receipt amount required.")
            else:
                try:
                    parsed_date = date.fromisoformat(receipt_date) if receipt_date else date.today()
                except ValueError:
                    parsed_date = date.today()
                database.add_transaction(
                    user_id,
                    parsed_date.strftime("%Y-%m-%d"),
                    "expense",
                    category,
                    amount,
                    f"AI receipt {invoice_no or ''} - {vendor or 'Unknown vendor'}",
                )
                st.success("Receipt expense saved.")
                st.rerun()

        if action_restock.button("📦 Save & Restock Inventory", use_container_width=True):
            if amount <= 0:
                st.error("Valid receipt amount required.")
            else:
                try:
                    parsed_date = date.fromisoformat(receipt_date) if receipt_date else date.today()
                except ValueError:
                    parsed_date = date.today()
                database.add_transaction(
                    user_id,
                    parsed_date.strftime("%Y-%m-%d"),
                    "expense",
                    "Inventory",
                    amount,
                    f"AI restock receipt {invoice_no or ''} - {vendor or 'Unknown vendor'}",
                )
                for item in extracted.get("items", []):
                    database.add_or_restock_inventory(
                        user_id,
                        str(item.get("name", "")).strip(),
                        float(item.get("qty", 0) or 0),
                        selling_price=float(item.get("price", 0) or 0),
                        gst_rate=float(gst_amount),
                    )
                st.success("Expense saved aur inventory restock ho gayi.")
                st.rerun()


def gst_invoice_module(user_id: int) -> None:
    st.subheader("🧾 GST Invoice Generator")
    left, right = st.columns([1.15, 0.85])

    with left:
        indian_states = [
            "Madhya Pradesh", "Maharashtra", "Delhi", "Rajasthan", "Gujarat",
            "Uttar Pradesh", "Karnataka", "Tamil Nadu", "Telangana", "West Bengal",
        ]
        c1, c2 = st.columns(2)
        with c1:
            customer_name = st.text_input("Customer Name", "Sahu Traders")
            customer_state = st.selectbox(
                "Customer State",
                indian_states,
                index=indian_states.index("Madhya Pradesh"),
            )
        with c2:
            seller_state_index = (
                indian_states.index(st.session_state.store_state)
                if st.session_state.store_state in indian_states
                else indian_states.index("Madhya Pradesh")
            )
            seller_state = st.selectbox(
                "Seller State",
                indian_states,
                index=seller_state_index,
            )
            invoice_date = st.date_input("Invoice Date", date.today())
        upi_id = st.session_state.store_upi_id
        payee_name = st.session_state.upi_payee_name

        item_control_left, item_control_right = st.columns(2)
        if item_control_left.button("➕ Add Item"):
            st.session_state.invoice_items.append(
                {"name": "", "qty": 1.0, "price": 0.0, "gst_rate": 0.0}
            )
            st.rerun()
        if item_control_right.button("🗑️ Clear Items"):
            st.session_state.invoice_items = []
            st.rerun()

        item_frame = pd.DataFrame(st.session_state.invoice_items)
        edited_items = st.data_editor(
            item_frame,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "name": st.column_config.TextColumn("Item"),
                "qty": st.column_config.NumberColumn("Qty", min_value=0.0),
                "price": st.column_config.NumberColumn("Price (₹)", min_value=0.0),
                "gst_rate": st.column_config.SelectboxColumn(
                    "GST Rate",
                    options=[0.0, 5.0, 12.0, 18.0, 28.0],
                    required=True,
                ),
            },
            key="invoice_item_editor",
        )

    clean_items = []
    for row in edited_items.to_dict("records"):
        if str(row.get("name", "")).strip():
            clean_items.append(
                {
                    "name": str(row["name"]),
                    "qty": float(row["qty"]),
                    "price": float(row["price"]),
                    "gst_rate": float(row["gst_rate"]),
                }
            )

    gst_result = gst_invoice.calculate_gst(
        clean_items,
        seller_state,
        customer_state,
    )

    with right:
        st.markdown('<div class="summary-card">', unsafe_allow_html=True)
        st.markdown("#### 💳 Live Tax Breakdown")
        st.metric("Subtotal", format_inr(gst_result["subtotal"]))
        if gst_result["igst"] > 0:
            st.metric("IGST", format_inr(gst_result["igst"]))
            st.caption("Inter-state supply")
        else:
            tax1, tax2 = st.columns(2)
            tax1.metric("CGST", format_inr(gst_result["cgst"]))
            tax2.metric("SGST", format_inr(gst_result["sgst"]))
            st.caption("Intra-state supply")
        st.metric("Grand Total", format_inr(gst_result["total"]))
        st.markdown("</div>", unsafe_allow_html=True)

        store_name = payee_name or st.session_state.user.get(
            "business_name",
            "Kirana Store",
        )
        invoice_note = f"GST Invoice payment - {customer_name or 'Customer'}"
        qr_bytes = gst_invoice.generate_upi_qr_bytes(
            upi_id,
            store_name,
            gst_result["total"],
            invoice_note,
        )
        st.image(
            qr_bytes,
            caption=(
                f"Scan with GPay / PhonePe / Paytm to Pay "
                f"Rs. {gst_result['total']:,.2f}"
            ),
            width=200,
        )
        st.download_button(
            "📥 Download Payment QR (PNG)",
            data=qr_bytes,
            file_name="GST-Payment-QR.png",
            mime="image/png",
            use_container_width=True,
        )

        if st.button("📥 Generate & Download GST PDF", type="primary", use_container_width=True):
            invoice_number = f"INV-{date.today().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"
            invoice_data = {
                "invoice_number": invoice_number,
                "date": invoice_date.strftime("%Y-%m-%d"),
                "seller_name": st.session_state.user.get("business_name", "Kirana Store"),
                "seller_state": seller_state,
                "customer_name": customer_name,
                "customer_state": customer_state,
                "items": clean_items,
                "upi_id": upi_id,
                "payee_name": store_name,
                "upi_note": invoice_note,
            }
            pdf_bytes = gst_invoice.generate_invoice_pdf(invoice_data)

            database.add_invoice(
                user_id,
                invoice_number,
                invoice_date.strftime("%Y-%m-%d"),
                customer_name,
                customer_state,
                seller_state,
                json.dumps(clean_items),
                gst_result["subtotal"],
                gst_result["cgst"],
                gst_result["sgst"],
                gst_result["igst"],
                gst_result["total"],
            )
            database.deduct_inventory(user_id, clean_items)
            st.download_button(
                "Download PDF",
                data=pdf_bytes,
                file_name=f"{invoice_number}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

        whatsapp_message = (
            f"{st.session_state.user.get('business_name', 'VyaparMitra Store')} "
            f"GST Invoice {invoice_number if 'invoice_number' in locals() else 'Draft'} "
            f"for {customer_name or 'Customer'}. "
            f"Total due: ₹{gst_result['total']:,.2f}. "
            f"Thank you for your purchase."
        )
        whatsapp_url = "https://wa.me/?text=" + quote(whatsapp_message)
        st.link_button(
            "📲 Share Summary on WhatsApp",
            whatsapp_url,
            use_container_width=True,
        )

    st.markdown("---")
    st.markdown("### 🏛️ Monthly GST Tax Liability Summary")
    invoices = database.get_invoices(user_id)
    current_month = date.today().strftime("%Y-%m")
    monthly_invoices = [
        invoice for invoice in invoices
        if str(invoice["date"]).startswith(current_month)
    ]
    taxable_sales = sum(float(invoice["subtotal"]) for invoice in monthly_invoices)
    cgst_total = sum(float(invoice["cgst"]) for invoice in monthly_invoices)
    sgst_total = sum(float(invoice["sgst"]) for invoice in monthly_invoices)
    igst_total = sum(float(invoice["igst"]) for invoice in monthly_invoices)
    net_output_gst = cgst_total + sgst_total + igst_total

    gst_s1, gst_s2, gst_s3 = st.columns(3)
    gst_s1.metric("Total Taxable Sales", format_inr(taxable_sales))
    gst_s2.metric("CGST", format_inr(cgst_total))
    gst_s3.metric("SGST", format_inr(sgst_total))
    gst_s4, gst_s5 = st.columns(2)
    gst_s4.metric("IGST", format_inr(igst_total))
    gst_s5.metric("Net Output GST Payable", format_inr(net_output_gst))

    gst_summary_df = pd.DataFrame([
        {
            "Period": current_month,
            "Total Taxable Sales": taxable_sales,
            "CGST": cgst_total,
            "SGST": sgst_total,
            "IGST": igst_total,
            "Net Output GST Payable": net_output_gst,
        }
    ])
    st.download_button(
        "📥 Download GST Summary CSV",
        data=gst_summary_df.to_csv(index=False).encode("utf-8"),
        file_name=f"GST-Summary-{current_month}.csv",
        mime="text/csv",
        use_container_width=True,
    )


def loan_planner(user_id: int) -> None:
    st.subheader("🏦 Loan & Safe EMI Planner")
    transactions = database.get_transactions(user_id)
    income_values = [
        float(item["amount"])
        for item in transactions
        if item["type"].lower() == "income"
    ]
    avg_monthly_profit = (
        float(database.get_financial_summary(user_id)["net_balance"]) / 6
        if income_values
        else 0.0
    )

    left, right = st.columns([1, 1])
    with left:
        loan_amount = st.number_input(
            "Loan Amount (₹)",
            min_value=50000,
            max_value=2000000,
            value=200000,
            step=5000,
        )
        interest_rate = st.number_input(
            "Annual Interest Rate (%)",
            min_value=0.0,
            max_value=30.0,
            value=12.0,
            step=0.25,
        )
        tenure_months = st.number_input(
            "Tenure (Months)",
            min_value=6,
            max_value=84,
            value=36,
            step=6,
        )
        st.caption(
            f"Estimated average monthly profit: {format_inr(avg_monthly_profit)}"
        )
        calculate_emi = st.button(
            "🧮 Calculate EMI & Risk",
            type="primary",
            use_container_width=True,
        )

    if calculate_emi:
        st.session_state.loan_plan = loan_calculator.calculate_loan_plan(
            loan_amount,
            interest_rate,
            tenure_months,
            avg_monthly_profit,
        )

    plan = st.session_state.get("loan_plan")
    if plan is None:
        plan = loan_calculator.calculate_loan_plan(
            loan_amount,
            interest_rate,
            tenure_months,
            avg_monthly_profit,
        )

    with right:
        m1, m2, m3 = st.columns(3)
        m1.metric("Monthly EMI", format_inr(plan["monthly_emi"]))
        m2.metric("Total Interest", format_inr(plan["total_interest"]))
        m3.metric("Total Repayment", format_inr(plan["total_payment"]))

        status = plan["risk_status"]
        css_class = {
            "Safe": "status-safe",
            "Moderate": "status-moderate",
            "High Risk": "status-high",
        }[status]
        badge_text = {
            "Safe": "🟢 Safe",
            "Moderate": "🟡 Moderate",
            "High Risk": "🔴 High Risk",
        }[status]
        st.markdown(
            f'<div class="{css_class}">{badge_text} EMI Affordability</div>',
            unsafe_allow_html=True,
        )
        st.info(plan["recommendation"])


def inventory_module(user_id: int) -> None:
    st.subheader("📦 Inventory & Stock")
    inventory = database.get_inventory(user_id)
    today = date.today()
    near_expiry = []
    expired = []
    for item in inventory:
        expiry_text = str(item.get("expiry_date", "") or "").strip()
        if not expiry_text:
            continue
        try:
            expiry_date = date.fromisoformat(expiry_text)
            if expiry_date < today:
                expired.append(item)
            elif expiry_date <= today + timedelta(days=30):
                near_expiry.append(item)
        except ValueError:
            pass
    if expired:
        st.markdown(
            '<div class="alert-red">⏳ Expired Stock: '
            + ", ".join(str(item["item_name"]) for item in expired)
            + "</div>",
            unsafe_allow_html=True,
        )
    if near_expiry:
        st.warning(
            "⏳ Expiring Within 30 Days: "
            + ", ".join(
                f"{item['item_name']} ({item['expiry_date']})"
                for item in near_expiry
            )
        )
    low_stock = [
        item for item in inventory
        if float(item["stock_qty"]) < float(item["min_stock"])
    ]
    if low_stock:
        names = ", ".join(str(item["item_name"]) for item in low_stock)
        st.markdown(
            f'<div class="alert-red">⚠️ Low Stock Alert: {names}</div>',
            unsafe_allow_html=True,
        )

    with st.expander("➕ Add / Restock Inventory", expanded=False):
        with st.form("inventory_entry"):
            c1, c2, c3 = st.columns(3)
            with c1:
                item_name = st.text_input("Item Name")
                unit = st.text_input("Unit", "pcs")
            with c2:
                stock_qty = st.number_input("Stock Qty", min_value=0.0, step=1.0)
                min_stock = st.number_input("Minimum Stock", min_value=0.0, step=1.0)
            with c3:
                selling_price = st.number_input("Selling Price (₹)", min_value=0.0, step=10.0)
                gst_rate = st.selectbox("GST Rate", [0.0, 5.0, 12.0, 18.0, 28.0])
                expiry_date = st.date_input(
                    "Expiry Date",
                    value=date.today() + timedelta(days=180),
                )
            submitted = st.form_submit_button("💾 Add / Restock Item", type="primary")
        if submitted:
            if not item_name.strip():
                st.error("Item name required hai.")
            else:
                database.add_or_restock_inventory(
                    user_id,
                    item_name,
                    stock_qty,
                    unit,
                    min_stock,
                    selling_price,
                    gst_rate,
                    expiry_date.strftime("%Y-%m-%d"),
                )
                st.success("Inventory updated.")
                st.rerun()

    if not inventory:
        st.info("Abhi inventory empty hai.")
        return

    for item in inventory:
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([2, 1, 1, 1.5])
            c1.markdown(
                f"**{item['item_name']}**\n\n"
                f"{format_inr(item['selling_price'])} / {item['unit']} • GST {item['gst_rate']}%\n"
                f"Expiry: {item.get('expiry_date') or 'Not set'}"
            )
            c2.metric("Stock", f"{item['stock_qty']:.1f} {item['unit']}")
            c3.metric("Min Stock", f"{item['min_stock']:.1f}")
            restock_key = f"restock_{item['id']}"
            restock_qty = c4.number_input(
                "Restock Qty",
                min_value=0.0,
                step=1.0,
                key=restock_key,
            )
            if c4.button("📦 Restock", key=f"button_{item['id']}", use_container_width=True):
                if restock_qty <= 0:
                    st.warning("Restock quantity 0 se zyada dalein.")
                elif database.restock_inventory(user_id, int(item["id"]), restock_qty):
                    st.success(f"{item['item_name']} restocked.")
                    st.rerun()


def udhaar_module(user_id: int) -> None:
    st.subheader("📒 Udhaar / Credit Khata")

    with st.expander("➕ Record New Customer Credit", expanded=False):
        with st.form("udhaar_entry"):
            c1, c2, c3 = st.columns(3)
            with c1:
                customer_name = st.text_input("Customer Name")
                phone = st.text_input("Phone")
                amount = st.number_input("Amount (₹)", min_value=0.0, step=100.0)
            with c2:
                due_date = st.date_input("Due Date", date.today())
                status = st.selectbox("Status", ["Pending", "Paid"])
            with c3:
                entry_type = st.selectbox(
                    "Khata Entry Type",
                    ["Customer - Lena Hai", "Supplier - Dena Hai"],
                )
                payment_mode = st.selectbox("Payment Mode", ["Cash", "UPI"])
            submitted = st.form_submit_button("💾 Save Udhaar", type="primary")
        if submitted:
            if not customer_name.strip():
                st.error("Customer name required hai.")
            elif amount <= 0:
                st.error("Amount ₹0 se zyada hona chahiye.")
            else:
                database.add_udhaar(
                    user_id,
                    customer_name,
                    phone,
                    amount,
                    due_date.strftime("%Y-%m-%d"),
                    status,
                    entry_type,
                    payment_mode,
                )
                st.success("Udhaar entry saved.")
                st.rerun()

    entries = database.get_udhaar(user_id)
    if not entries:
        st.info("Abhi koi udhaar entry nahi hai.")
        return

    pending_total = sum(
        float(entry.get("remaining_amount", entry["amount"]))
        for entry in entries
        if entry["status"] == "Pending"
    )
    m1, m2 = st.columns(2)
    m1.metric("Pending Udhaar", format_inr(pending_total))
    m2.metric("Total Entries", str(len(entries)))

    for entry in entries:
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([1.4, 1.2, 1, 1.5])
            c1.markdown(
                f"**{entry['customer_name']}**\n\n"
                f"📞 {entry['phone'] or 'N/A'}\n\n"
                f"{entry.get('entry_type', 'Customer - Lena Hai')} • "
                f"{entry.get('payment_mode', 'Cash')}"
            )
            c2.markdown(
                f"**Pending/Original**\n\n"
                f"{format_inr(entry.get('remaining_amount', entry['amount']))}"
                f" / {format_inr(entry['amount'])}"
            )
            c3.markdown(f"**Due**\n\n{entry['due_date']}")

            status = entry["status"]
            if status == "Paid":
                c4.markdown('<div class="status-safe">✅ Paid</div>', unsafe_allow_html=True)
            else:
                c4.markdown('<div class="status-moderate">🟡 Pending</div>', unsafe_allow_html=True)

            action_left, action_right = st.columns(2)
            if entry["status"] == "Pending":
                partial_amount = action_left.number_input(
                    "Partial Payment (₹)",
                    min_value=0.0,
                    max_value=float(entry.get("remaining_amount", entry["amount"])),
                    step=100.0,
                    key=f"partial_udhaar_{entry['id']}",
                )
                if action_right.button(
                    "💸 Apply Partial Payment",
                    key=f"apply_partial_udhaar_{entry['id']}",
                    use_container_width=True,
                ):
                    if partial_amount <= 0:
                        st.warning("Partial payment amount 0 se zyada dalein.")
                    else:
                        updated = database.record_udhaar_partial_payment(
                            user_id,
                            int(entry["id"]),
                            partial_amount,
                        )
                        if updated:
                            st.success(
                                f"{format_inr(updated['applied_amount'])} update hua; "
                                f"remaining balance {format_inr(updated['remaining_amount'])}"
                            )
                            st.rerun()

                action_left, action_right = st.columns(2)
                if action_left.button(
                    "✅ Mark as Paid",
                    key=f"pay_udhaar_{entry['id']}",
                    use_container_width=True,
                ):
                    paid_entry = database.mark_udhaar_paid(user_id, int(entry["id"]))
                    if paid_entry:
                        st.success(
                            f"{paid_entry['customer_name']} se "
                            f"{format_inr(paid_entry['amount'])} Income mein recover hua."
                        )
                        st.rerun()

            if entry["status"] == "Pending":
                store_name = st.session_state.upi_payee_name or st.session_state.user.get(
                    "business_name",
                    "Kirana Store",
                )
                amount_value = float(entry.get("remaining_amount", entry["amount"]))
                udhaar_note = (
                    f"Udhaar payment - {entry['customer_name']} "
                    f"due {entry['due_date']}"
                )
                udhaar_qr_bytes = gst_invoice.generate_upi_qr_bytes(
                    st.session_state.store_upi_id,
                    store_name,
                    amount_value,
                    udhaar_note,
                )

                reminder_message = (
                    "Namaste!\n\n"
                    "Yeh aapke liye ek payment reminder hai.\n\n"
                    f"Hamari dukaan ke hisaab ke anusaar aapka ₹{amount_value:.2f} ka balance abhi pending hai.\n\n"
                    "Aapki suvidha ke liye pending bill aur online payment ka QR Code saath mein share kiya gaya hai.\n\n"
                    "Payment update hone par aapke account mein balance automatically update kar diya jayega.\n\n"
                    "Dhanyavaad!\n"
                    f"*{store_name}*"
                )
                phone_digits = "".join(ch for ch in str(entry["phone"]) if ch.isdigit())
                if len(phone_digits) == 10:
                    whatsapp_url = (
                        "https://wa.me/91"
                        + phone_digits
                        + "?text="
                        + quote(reminder_message)
                    )
                elif phone_digits:
                    whatsapp_url = (
                        "https://wa.me/"
                        + phone_digits
                        + "?text="
                        + quote(reminder_message)
                    )
                else:
                    whatsapp_url = "https://wa.me/?text=" + quote(reminder_message)

                with st.expander(
                    "📲 Send Reminder, QR & Bill",
                    expanded=False,
                ):
                    st.link_button(
                        "📲 Send WhatsApp Payment Reminder",
                        whatsapp_url,
                        use_container_width=True,
                    )
                    qr_col, pdf_col = st.columns([1, 1])
                    with qr_col:
                        st.image(
                            udhaar_qr_bytes,
                            caption=(
                                f"Scan to Pay ₹{amount_value:.2f} via UPI "
                                "(8461919697@ybl)"
                            ),
                            width=220,
                        )
                    with pdf_col:
                        pending_pdf = gst_invoice.generate_pending_udhaar_pdf(
                            {
                                "shop_name": store_name,
                                "customer_name": entry["customer_name"],
                                "phone": entry["phone"],
                                "due_date": entry["due_date"],
                                "amount": amount_value,
                                "upi_id": st.session_state.store_upi_id,
                            }
                        )
                        st.download_button(
                            "📥 Download Pending Bill + QR (PDF)",
                            data=pending_pdf,
                            file_name=(
                                f"Pending-Udhaar-{entry['customer_name']}"
                                f"-{entry['id']}.pdf"
                            ),
                            mime="application/pdf",
                            key=f"udhaar_pending_pdf_{entry['id']}",
                            use_container_width=True,
                        )


def copilot_module(user_id: int) -> None:
    st.subheader("🤖 Hinglish AI Business Copilot")
    summary = database.get_financial_summary(user_id)
    transactions = database.get_transactions(user_id)
    forecast_df = pd.DataFrame(
        [
            {"date": item["date"], "type": item["type"].title(), "amount": item["amount"]}
            for item in transactions
        ]
    )
    if forecast_df.empty:
        forecast_df = pd.DataFrame(columns=["date", "type", "amount"])
    forecast = forecasting.analyze_and_forecast(forecast_df)
    expense_categories = {}
    for item in transactions:
        if str(item["type"]).lower() == "expense":
            category = str(item["category"] or "Other")
            expense_categories[category] = (
                expense_categories.get(category, 0.0) + float(item["amount"])
            )
    top_category = (
        max(expense_categories, key=expense_categories.get)
        if expense_categories
        else "N/A"
    )
    pending_udhaar = sum(
        float(entry.get("remaining_amount", entry["amount"]))
        for entry in database.get_udhaar(user_id)
        if entry["status"] == "Pending"
    )
    khata_entries = database.get_udhaar(user_id)
    customer_entries = [
        entry for entry in khata_entries
        if entry["status"] == "Pending"
        and "supplier" not in str(entry.get("entry_type", "")).lower()
        and "customer" in str(entry.get("entry_type", "")).lower()
    ]
    supplier_entries = [
        entry for entry in khata_entries
        if entry["status"] == "Pending"
        and "supplier" in str(entry.get("entry_type", "")).lower()
    ]
    customer_receivable_total = sum(
        float(entry.get("remaining_amount", entry["amount"]))
        for entry in customer_entries
    )
    wholesaler_payable_total = sum(
        float(entry.get("remaining_amount", entry["amount"]))
        for entry in supplier_entries
    )
    expiring_items = []
    today = date.today()
    for item in database.get_inventory(user_id):
        expiry_text = str(item.get("expiry_date", "") or "").strip()
        if not expiry_text:
            continue
        try:
            expiry_date = date.fromisoformat(expiry_text)
            if today <= expiry_date <= today + timedelta(days=30):
                expiring_items.append(str(item["item_name"]))
        except ValueError:
            pass
    low_stock_items = [
        str(item["item_name"])
        for item in database.get_inventory(user_id)
        if float(item["stock_qty"]) < float(item["min_stock"])
    ]
    copilot_summary = {
        "total_income": float(summary["total_income"]),
        "total_expense": float(summary["total_expense"]),
        "total_revenue": float(summary["total_income"]),
        "total_expenses": float(summary["total_expense"]),
        "net_profit": float(summary["net_balance"]),
        "projected_balance": float(forecast["predicted_balance"]),
        "top_category": top_category,
        "pending_udhaar": float(pending_udhaar),
        "low_stock_items": low_stock_items,
        "customer_receivable_total": float(customer_receivable_total),
        "customer_pending_count": len(customer_entries),
        "wholesaler_payable_total": float(wholesaler_payable_total),
        "wholesaler_pending_count": len(supplier_entries),
        "expiring_items": expiring_items,
        "shortage_alert": forecast["shortage_alert"],
    }

    st.markdown("#### 🎙️ Bol Kar Sawal Puchein")
    voice_audio = st.audio_input("🎙️ Bol Kar Sawal Puchein (Voice Input)")
    if voice_audio:
        if st.button("🔍 Transcribe & Ask", type="primary"):
            transcription, answer = ai_assistant.transcribe_voice_and_answer(
                voice_audio.getvalue(),
                copilot_summary,
            )
            st.session_state.chat_history.append(
                {"role": "user", "content": f"[Voice] {transcription}"}
            )
            st.session_state.chat_history.append(
                {"role": "assistant", "content": answer}
            )
            st.session_state.last_voice_answer = answer
            st.rerun()

    chips = [
        "📒 \"Kitne logon se udhaar lena hai aur kitna payment pending hai?\"",
        "🏭 \"Wholesalers ko kitna payment dena baaki hai?\"",
        "🏦 \"Kya ₹2,50,000 ka loan lena safe rahega?\"",
    ]
    chip_cols = st.columns(3)
    for index, question in enumerate(chips):
        if chip_cols[index].button(question, use_container_width=True):
            clean_question = question.split('"', 1)[1].rsplit('"', 1)[0] if '"' in question else question
            st.session_state.chat_history.append(
                {"role": "user", "content": clean_question}
            )
            chip_answer = ai_assistant.ask_business_copilot(
                clean_question,
                copilot_summary,
            )
            st.session_state.chat_history.append(
                {"role": "assistant", "content": chip_answer}
            )
            st.rerun()

    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if st.session_state.chat_history:
        last_assistant = next(
            (
                message["content"]
                for message in reversed(st.session_state.chat_history)
                if message["role"] == "assistant"
            ),
            "",
        )
        if st.button("🔊 Listen to Reply (Hindi Audio)"):
            try:
                speech = gTTS(text=last_assistant[:500], lang="hi")
                audio_buffer = BytesIO()
                speech.write_to_fpfile(audio_buffer)
                st.audio(audio_buffer.getvalue(), format="audio/mpg")
            except Exception as exc:
                st.info(f"Audio generate nahi hua: {exc}")

    prompt = st.chat_input("Apna business sawal Hinglish mein puchein...")
    if "pending_question" in st.session_state:
        prompt = st.session_state.pop("pending_question")

    if prompt:
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Samajh raha hoon..."):
                answer = ai_assistant.ask_business_copilot(prompt, copilot_summary)
            st.markdown(answer)
        st.session_state.chat_history.append({"role": "assistant", "content": answer})


def dashboard() -> None:
    user = st.session_state.user
    user_id = int(user["id"])

    if not st.session_state.get("upi_payee_name"):
        st.session_state.upi_payee_name = user.get(
            "business_name",
            "Sharma Kirana Store",
        )

    with st.sidebar:
        st.markdown("## VyaparMitra")
        st.markdown("### Store Profile")
        st.markdown(f"**Store Name:** {user.get('business_name', 'Kirana Store')}")
        st.caption(f"GSTIN: {st.session_state.get('store_gstin', 'NOT PROVIDED')}")
        st.caption(f"State: {st.session_state.get('store_state', 'Madhya Pradesh')}")
        st.markdown("---")
        with st.expander("💳 UPI Payment QR Settings", expanded=False):
            st.session_state.store_upi_id = st.text_input(
                "Store UPI ID",
                value=st.session_state.store_upi_id,
                key="sidebar_store_upi_id",
            )
            st.session_state.upi_payee_name = st.text_input(
                "Payee / Store Display Name",
                value=st.session_state.upi_payee_name,
                key="sidebar_upi_payee_name",
            )
        st.markdown("---")
        selected = st.radio(
            "Navigation",
            [
                "📊 Financial Overview & Forecast",
                "📸 AI Receipt Scanner",
                "🧾 GST Invoice Generator",
                "🏦 Loan & Safe EMI Planner",
                "📒 Udhaar / Credit Khata",
                "📦 Inventory & Stock",
                "🤖 Hinglish AI Copilot",
            ],
            label_visibility="collapsed",
        )
        st.markdown("---")
        if st.button("🔄 Reset Demo Data", use_container_width=True):
            demo_user = auth.reset_demo_user()
            st.session_state.user = demo_user
            st.session_state.store_gstin = "27ABCDE1234F1Z5"
            st.session_state.store_state = "Maharashtra"
            st.session_state.chat_history = []
            st.session_state.receipt_extracted = {}
            st.session_state.receipt_generated = None
            st.session_state.invoice_items = [
                {"name": "Rice 5kg", "qty": 1.0, "price": 450.0, "gst_rate": 5.0}
            ]
            st.success("Demo data reset ho gaya.")
            st.rerun()
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.user = None
            st.session_state.chat_history = []
            st.rerun()

    if selected == "📊 Financial Overview & Forecast":
        financial_overview(user_id)
    elif selected == "📸 AI Receipt Scanner":
        receipt_scanner(user_id)
    elif selected == "🧾 GST Invoice Generator":
        gst_invoice_module(user_id)
    elif selected == "🏦 Loan & Safe EMI Planner":
        loan_planner(user_id)
    elif selected == "📒 Udhaar / Credit Khata":
        udhaar_module(user_id)
    elif selected == "📦 Inventory & Stock":
        inventory_module(user_id)
    else:
        copilot_module(user_id)


if not st.session_state.authenticated:
    auth_screen()
else:
    dashboard()