"""Monthly business forecasting helpers."""

from typing import Dict

import pandas as pd
from sklearn.linear_model import LinearRegression


def analyze_and_forecast(transactions_df: pd.DataFrame) -> Dict[str, object]:
    """Aggregate transactions by month and forecast the next month's balances."""
    required_columns = {"date", "type", "amount"}
    if not required_columns.issubset(transactions_df.columns):
        raise ValueError(
            "transactions_df must contain 'date', 'type', and 'amount' columns"
        )

    data = transactions_df.copy()
    data["date"] = pd.to_datetime(data["date"], errors="coerce")
    data["amount"] = pd.to_numeric(data["amount"], errors="coerce").fillna(0.0)
    data = data.dropna(subset=["date"])

    data["Month"] = data["date"].dt.strftime("%Y-%m")
    data["type_normalized"] = data["type"].astype(str).str.strip().str.lower()

    monthly_income = (
        data.loc[data["type_normalized"] == "income"]
        .groupby("Month")["amount"]
        .sum()
    )
    monthly_expense = (
        data.loc[data["type_normalized"] == "expense"]
        .groupby("Month")["amount"]
        .sum()
    )

    all_months = sorted(set(monthly_income.index).union(monthly_expense.index))
    rows = []
    closing_balance = 0.0

    for month in all_months:
        income = float(monthly_income.get(month, 0.0))
        expense = float(monthly_expense.get(month, 0.0))
        net = income - expense
        closing_balance += net
        rows.append(
            {
                "Month": month,
                "Monthly Income": income,
                "Monthly Expense": expense,
                "Net Profit/Loss": net,
                "Closing Balance": closing_balance,
            }
        )

    monthly_df = pd.DataFrame(
        rows,
        columns=[
            "Month",
            "Monthly Income",
            "Monthly Expense",
            "Net Profit/Loss",
            "Closing Balance",
        ],
    )

    month_count = len(monthly_df)
    if month_count == 0:
        predicted_income = 0.0
        predicted_expense = 0.0
    elif month_count < 2:
        predicted_income = float(monthly_df["Monthly Income"].iloc[-1])
        predicted_expense = float(monthly_df["Monthly Expense"].iloc[-1])
    else:
        x = pd.Series(range(month_count), dtype=float).to_numpy().reshape(-1, 1)
        next_month = [[float(month_count)]]

        income_model = LinearRegression()
        income_model.fit(x, monthly_df["Monthly Income"])
        predicted_income = max(0.0, float(income_model.predict(next_month)[0]))

        expense_model = LinearRegression()
        expense_model.fit(x, monthly_df["Monthly Expense"])
        predicted_expense = max(0.0, float(expense_model.predict(next_month)[0]))

    predicted_income = round(predicted_income, 2)
    predicted_expense = round(predicted_expense, 2)
    predicted_next_profit = predicted_income - predicted_expense
    predicted_balance = round(closing_balance + predicted_next_profit, 2)

    return {
        "monthly_df": monthly_df,
        "predicted_income": predicted_income,
        "predicted_expense": predicted_expense,
        "predicted_balance": predicted_balance,
        "shortage_alert": predicted_balance < 10000,
    }