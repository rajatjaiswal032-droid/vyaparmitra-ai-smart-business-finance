# Smart Biz Finance

Smart Biz Finance is a Python and Streamlit project for small Indian businesses, especially Kirana stores. It is designed to manage transactions, invoices, loans, business forecasts, authentication, and Hinglish conversations with an AI business copilot.

> Note: `database.py` contains the SQLite implementation and initializes `finance.db` automatically. Several Streamlit and feature modules are currently scaffolds, so the demo should be extended in `app.py` and the feature modules before calling it feature-complete.

## Features

- User accounts with bcrypt password hashing support
- Income and expense transaction management
- Per-user financial summaries and balances
- GST invoice records
- Loan and EMI records
- Sales forecasting support
- Gemini-powered AI business assistance
- INR formatting and Indian business terminology
- SQLite storage with no external database server

## Technology Stack

- Python
- Streamlit
- SQLite
- Pandas
- Plotly
- FPDF2
- scikit-learn
- bcrypt
- python-dotenv
- Google Gen AI SDK
- Pillow

## Project Structure

| File | Purpose |
|---|---|
| `app.py` | Main Streamlit application entry point |
| `database.py` | SQLite schema and CRUD operations |
| `auth.py` | Authentication helpers |
| `ai_assistant.py` | AI Business Copilot integration |
| `forecasting.py` | Sales and expense forecasting |
| `gst_invoice.py` | GST invoice calculations and PDF generation |
| `loan_calculator.py` | Loan EMI and risk calculations |
| `demo_test_notes.md` | Demo notes and test scenarios |
| `requirements.txt` | Python dependencies |
| `.env` | Local environment variables; excluded by `.gitignore` |
| `finance.db` | Generated SQLite database; excluded by `.gitignore` |

## Prerequisites

- Windows 10/11
- Python 3.10 or later
- A Google Gemini API key for AI Copilot features
- Optional: Git

## Setup on Windows

1. Open PowerShell in the project directory:

```powershell
cd "C:\Users\RAJAT JAISWAL\smart-biz-finance"
```

2. Create a virtual environment:

```powershell
python -m venv venv
```

3. Activate the environment:

```powershell
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks script execution:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

4. Install dependencies:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

5. Create or update `.env` in the project root:

```dotenv
GEMINI_API_KEY=your_api_key_here
```

Do not commit `.env` or real API credentials. Revoke and replace any key that is accidentally shared.

6. Initialize the database:

```powershell
python -c "import database"
```

This creates `finance.db` and the required tables. `database.py` also initializes the database automatically when imported.

7. Start the Streamlit app:

```powershell
streamlit run app.py
```

Open the local URL printed by Streamlit, normally `http://localhost:8501`.

## Database Schema

The SQLite database contains four main tables:

- `users`: account details and bcrypt password hashes
- `transactions`: income and expenses linked to a user
- `invoices`: invoice and GST details
- `loans`: principal, tenure, EMI, interest, and risk data

Transaction types are validated as either `income` or `expense`. Dates are stored as ISO strings using `YYYY-MM-DD`, while monetary values are stored as floating-point amounts in INR.

## Running Database Operations

Example Python usage:

```python
import database

database.init_db()

user_id = database.create_user(
    username="demo-owner",
    password_hash="replace-with-bcrypt-hash",
    business_name="Sharma Kirana Store",
)

if user_id:
    database.add_transaction(
        user_id=user_id,
        date="2026-11-20",
        trans_type="income",
        category="Retail Sale",
        amount=2850.00,
        description="Cash par daily groceries ki sale",
    )

    print(database.get_financial_summary(user_id))
```

## Demo Transaction Data

Use these 10 realistic INR records during a demo:

| Date | Type | Category | Description | Amount |
|---|---|---|---|---:|
| 2026-11-20 | income | UTP Sale | 2 kg rice, 1 litre oil aur 500g atta sale | ₹1,240 |
| 2026-11-19 | income | Retail Sale | Cash par daily groceries ki sale | ₹2,850 |
| 2026-11-19 | expense | Inventory | Big Basket se sugar aur packaged snacks purchase | ₹3,600 |
| 2026-11-18 | expense | Transport | Delivery auto aur goods pickup transport | ₹450 |
| 2026-11-18 | income | UTP Sale | Biscuits, tea aur soap ki customer sale | ₹980 |
| 2026-11-17 | expense | Rent | Shop rent payment | ₹8,000 |
| 2026-11-17 | income | UPI Sale | UPI ke through grocery sale | ₹4,125 |
| 2026-11-16 | expense | Utilities | Bijli aur water bill payment | ₹1,750 |
| 2026-11-16 | income | Retail Sale | Cooking oil aur masale ki cash sale | ₹1,675 |
| 2026-11-15 | expense | Inventory | Wholesale market se atta, dal aur namkeen purchase | ₹6,200 |

## Demo Test Queries

Ask the AI Business Copilot:

1. `Aaj ki total income aur expenses kitni hain?`
2. `October mein sabse zyada kharcha kis category par hua?`
3. `UPI sales aur cash sales mein kya difference hai?`
4. `Kis date par sabse zyada revenue hua aur woh kyun ho sakta hai?`
5. `Agli 7 din ke liye inventory purchase ka budget kya recommend karoge?`

Additional verification queries:

```text
Mera current net balance kitna hai?
Sabse bada expense kya tha?
Is week ki income aur expense compare karo.
Rent aur utilities milakar kitna hai?
Inventory spending ko kam karne ke 3 practical suggestions do.
```

## Suggested Demo Flow

1. Start Streamlit and show the dashboard.
2. Create or log in to a demo Kirana Store account.
3. Add a few income and expense transactions from the sample table.
4. Demonstrate the summary cards for income, expense, net balance, and count.
5. Generate a GST invoice with a domestic customer.
6. Calculate a loan EMI and explain the risk level.
7. Ask three Hinglish questions to the AI Business Copilot.
8. Export or download a PDF report if that feature is enabled.

## Verification Checklist

- `python -c "import streamlit, pandas, plotly, fpdf, sklearn, bcrypt, dotenv, google.genai"`
- `python -c "import database; print(database.get_financial_summary(1))"`
- `streamlit run app.py`
- Database tables appear in `finance.db`
- Creating a transaction updates the summary
- Invalid transaction types are rejected
- Transactions are isolated by `user_id`
- API keys are not displayed in logs or UI

Useful SQLite checks:

```sql
SELECT name FROM sqlite_master
WHERE type = 'table'
ORDER BY name;

SELECT type, category, amount, description
FROM transactions
ORDER BY date DESC;

SELECT
    SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) AS income,
    SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) AS expense
FROM transactions;
```

## Troubleshooting

### Streamlit does not start

- Activate `venv`
- Run `python -m pip install -r requirements.txt`
- Confirm `app.py` exists in the current directory
- Run `streamlit run app.py --server.headless true`

### Gemini API error

- Confirm `GEMINI_API_KEY` is set in `.env`
- Restart Streamlit after changing `.env`
- Verify that the key is valid and has available quota
- Never use a customer-facing deployment secret directly in browser code

### Database problems

- Run `python -c "import database"`
- Delete only a local test `finance.db` after confirming it is safe
- Database recreation occurs when `database.init_db()` runs

### Invoice PDF issues

- Confirm `fpdf2` is installed
- Verify that the generated font and output path support your system
- Add invoice exports outside source-controlled directories

## Security Notes

- Store secrets in `.env`, not in source code
- Keep `.env` and `*.db` out of version control
- Hash passwords with bcrypt before using `create_user`
- Validate API and database inputs in the Streamlit UI
- Scope every transaction, invoice, and loan query to the logged-in `user_id`
- Rotate API keys that have been committed or shared publicly

## Development Status

The database layer is implemented. Application pages and integrations in `app.py`, `auth.py`, `ai_assistant.py`, `forecasting.py`, `gst_invoice.py`, and `loan_calculator.py` can be completed by wiring the existing database helpers into Streamlit UI components.
