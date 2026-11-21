"""Loan EMI, payment, and risk calculation helpers."""

from typing import Dict, Union


Number = Union[int, float]


def calculate_loan_plan(
    principal: Number,
    annual_rate: Number,
    tenure_months: int,
    avg_monthly_profit: Number,
) -> Dict[str, object]:
    """Calculate a loan repayment plan and a practical Hinglish recommendation."""
    principal = float(principal)
    annual_rate = float(annual_rate)
    tenure_months = int(tenure_months)
    avg_monthly_profit = float(avg_monthly_profit)

    if principal < 0:
        raise ValueError("principal cannot be negative")
    if annual_rate < 0:
        raise ValueError("annual_rate cannot be negative")
    if tenure_months <= 0:
        raise ValueError("tenure_months must be greater than zero")

    monthly_rate = annual_rate / 1200.0
    if monthly_rate == 0:
        monthly_emi = principal / tenure_months
    else:
        factor = (1 + monthly_rate) ** tenure_months
        monthly_emi = principal * monthly_rate * factor / (factor - 1)

    total_payment = monthly_emi * tenure_months
    total_interest = total_payment - principal

    if avg_monthly_profit > 0:
        emi_to_profit_ratio = monthly_emi / avg_monthly_profit * 100.0
    else:
        emi_to_profit_ratio = 0.0

    if avg_monthly_profit <= 0 or emi_to_profit_ratio > 50:
        risk_status = "High Risk"
    elif emi_to_profit_ratio <= 30:
        risk_status = "Safe"
    else:
        risk_status = "Moderate"

    if risk_status == "Safe":
        recommendation = (
            "EMI manageable hai aur monthly profit ka 30% ya less use ho raha hai. "
            "Payment plan follow kar sakte hain."
        )
    elif risk_status == "Moderate":
        recommendation = (
            "EMI moderate burden hai; monthly cash flow aur emergency reserve "
            "carefully manage karein before taking the loan."
        )
    else:
        recommendation = (
            "High risk hai. Profit low hai ya EMI profit ka 50% se zyada hai; "
            "loan reduce karein, tenure badhayein, ya extra income plan karein."
        )

    return {
        "monthly_emi": round(monthly_emi, 2),
        "total_payment": round(total_payment, 2),
        "total_interest": round(total_interest, 2),
        "emi_to_profit_ratio": round(emi_to_profit_ratio, 2),
        "risk_status": risk_status,
        "recommendation": recommendation,
    }