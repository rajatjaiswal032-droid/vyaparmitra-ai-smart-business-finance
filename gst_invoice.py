"""GST invoice calculation and PDF generation helpers."""

from io import BytesIO
from typing import Any, Dict, List
from urllib.parse import quote

from fpdf import FPDF
import qrcode


def calculate_gst(
    items: List[Dict[str, Any]],
    seller_state: str,
    customer_state: str,
) -> Dict[str, Any]:
    """Calculate item totals and applicable GST for an Indian invoice."""
    subtotal = 0.0
    gst_total = 0.0
    calculated_items: List[Dict[str, Any]] = []

    for item in items:
        name = str(item.get("name", ""))
        qty = float(item.get("qty", 0))
        price = float(item.get("price", 0))
        gst_rate = float(item.get("gst_rate", 0))

        line_subtotal = qty * price
        line_gst = line_subtotal * gst_rate / 100.0

        subtotal += line_subtotal
        gst_total += line_gst
        calculated_items.append(
            {
                "name": name,
                "qty": qty,
                "price": price,
                "gst_rate": gst_rate,
                "subtotal": line_subtotal,
                "gst": line_gst,
            }
        )

    same_state = seller_state.strip().lower() == customer_state.strip().lower()
    if same_state:
        cgst = gst_total / 2.0
        sgst = gst_total - cgst
        igst = 0.0
    else:
        cgst = 0.0
        sgst = 0.0
        igst = gst_total

    total = subtotal + gst_total
    return {
        "items": calculated_items,
        "subtotal": round(subtotal, 2),
        "cgst": round(cgst, 2),
        "sgst": round(sgst, 2),
        "igst": round(igst, 2),
        "total": round(total, 2),
    }


def _format_indian_decimal(amount: float) -> str:
    absolute = abs(float(amount))
    whole = f"{absolute:.2f}".split(".", 1)[0]
    decimal = f"{absolute:.2f}".split(".", 1)[1]
    sign = "-" if float(amount) < 0 else ""

    if len(whole) <= 3:
        return f"{sign}{whole}.{decimal}"

    last_three = whole[-3:]
    prefix = whole[:-3]
    grouped_prefix = ""
    while len(prefix) > 2:
        grouped_prefix = "," + prefix[-2:] + grouped_prefix
        prefix = prefix[:-2]
    if prefix:
        grouped_prefix = prefix + grouped_prefix
    return f"{sign}{grouped_prefix},{last_three}.{decimal}"


def _as_money(amount: float) -> str:
    return f"Rs. {_format_indian_decimal(amount)}"


def generate_upi_qr_bytes(
    upi_id: str,
    payee_name: str,
    amount: float,
    note: str,
) -> bytes:
    """Build an NPCI UPI URI and return a high-contrast PNG QR."""
    upi_uri = (
        f"upi://pay?"
        f"pa={upi_id}&"
        f"pn={quote(str(payee_name))}&"
        f"am={float(amount):.2f}&"
        "cu=INR&"
        f"tn={quote(str(note))}"
    )
    qr_image = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=2,
    )
    qr_image.add_data(upi_uri)
    qr_image.make(fit=True)
    image = qr_image.make_image(
        fill_color="black",
        back_color="white",
    )
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def generate_invoice_pdf(invoice_data: Dict[str, Any]) -> bytes:
    """Build a clean Indian GST Tax Invoice PDF and return it as bytes."""
    items = invoice_data.get("items", [])
    seller_state = str(invoice_data.get("seller_state", invoice_data.get("sellerState", "")))
    customer_state = str(
        invoice_data.get("customer_state", invoice_data.get("customerState", ""))
    )

    gst = calculate_gst(items, seller_state, customer_state)

    seller_name = str(invoice_data.get("seller_name", "Seller"))
    customer_name = str(invoice_data.get("customer_name", "Customer"))
    invoice_number = str(invoice_data.get("invoice_number", invoice_data.get("id", "N/A")))
    invoice_date = str(invoice_data.get("date", ""))

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "GST TAX INVOICE", align="C", ln=True)

    pdf.set_font("Helvetica", "", 10)
    pdf.cell(95, 7, f"Invoice No: {invoice_number}", ln=False)
    pdf.cell(95, 7, f"Date: {invoice_date}", align="R", ln=True)
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(95, 7, "Bill From:", ln=False)
    pdf.cell(95, 7, "Bill To:", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(95, 7, seller_name, ln=False)
    pdf.cell(95, 7, customer_name, ln=True)
    pdf.cell(95, 7, f"State: {seller_state or 'N/A'}", ln=False)
    pdf.cell(95, 7, f"State: {customer_state or 'N/A'}", ln=True)
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(72, 8, "Item", border=1)
    pdf.cell(18, 8, "Qty", border=1, align="C")
    pdf.cell(32, 8, "Rate", border=1, align="R")
    pdf.cell(24, 8, "GST %", border=1, align="C")
    pdf.cell(44, 8, "Amount", border=1, align="R", ln=True)

    pdf.set_font("Helvetica", "", 9)
    for item in gst["items"]:
        pdf.cell(72, 8, str(item["name"])[:38], border=1)
        pdf.cell(18, 8, str(item["qty"]), border=1, align="C")
        pdf.cell(32, 8, _as_money(item["price"]), border=1, align="R")
        pdf.cell(24, 8, f"{item['gst_rate']:.2f}", border=1, align="C")
        pdf.cell(
            44,
            8,
            _as_money(item["subtotal"]),
            border=1,
            align="R",
            ln=True,
        )

    pdf.ln(4)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(145, 7, "Subtotal", border=0, align="R")
    pdf.cell(45, 7, _as_money(gst["subtotal"]), border=0, align="R", ln=True)

    if gst["cgst"] > 0:
        pdf.cell(145, 7, "CGST", align="R")
        pdf.cell(45, 7, _as_money(gst["cgst"]), align="R", ln=True)
        pdf.cell(145, 7, "SGST", align="R")
        pdf.cell(45, 7, _as_money(gst["sgst"]), align="R", ln=True)
    elif gst["igst"] > 0:
        pdf.cell(145, 7, "IGST", align="R")
        pdf.cell(45, 7, _as_money(gst["igst"]), align="R", ln=True)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(145, 9, "Grand Total", border="T", align="R")
    pdf.cell(45, 9, _as_money(gst["total"]), border="T", align="R", ln=True)

    upi_id = str(invoice_data.get("upi_id", "8461919697@ybl")).strip()
    if upi_id:
        store_name = str(
            invoice_data.get(
                "payee_name",
                invoice_data.get("seller_name", "VyaparMitra Store"),
            )
        )
        upi_note = str(
            invoice_data.get(
                "upi_note",
                f"GST Invoice {invoice_number}",
            )
        )
        upi_url = (
            "upi://pay?"
            f"pa={quote(upi_id, safe='@')}&"
            f"pn={quote(store_name)}&"
            f"am={gst['total']:.2f}&cu=INR&"
            f"tn={quote(upi_note)}"
        )
        qr_bytes = generate_upi_qr_bytes(
            upi_id,
            store_name,
            gst["total"],
            upi_note,
        )
        qr_buffer = BytesIO(qr_bytes)
        qr_y = min(max(pdf.get_y() + 2, 235), 250)
        pdf.image(qr_buffer, x=146, y=qr_y, w=42, h=42)
        pdf.set_xy(102, qr_y + 43)
        pdf.set_font("Helvetica", "B", 8)
        pdf.multi_cell(
            86,
            4,
            "Scan via any UPI App (GPay / PhonePe / Paytm) - "
            "UPI: 8461919697@ybl",
            align="R",
        )

    pdf.set_font("Helvetica", "I", 8)
    pdf.ln(8)
    pdf.cell(0, 6, "Thank you for your business.", align="C")

    return bytes(pdf.output())


def generate_pending_udhaar_pdf(bill_data: Dict[str, Any]) -> bytes:
    """Generate a pending Udhaar payment slip with an embedded UPI QR."""
    shop_name = str(bill_data.get("shop_name", "VyaparMitra Store"))
    customer_name = str(bill_data.get("customer_name", "Customer"))
    phone = str(bill_data.get("phone", ""))
    due_date = str(bill_data.get("due_date", ""))
    amount = float(bill_data.get("amount", 0) or 0)
    upi_id = str(bill_data.get("upi_id", "8461919697@ybl"))

    note = f"Udhaar payment - {customer_name}"
    upi_url = (
        "upi://pay?"
        f"pa={quote(upi_id, safe='@')}&"
        f"pn={quote(shop_name)}&"
        f"am={amount:.2f}&cu=INR&"
        f"tn={quote(note)}"
    )
    qr_bytes = generate_upi_qr_bytes(
        upi_id,
        shop_name,
        amount,
        note,
    )
    qr_buffer = BytesIO(qr_bytes)

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 17)
    pdf.cell(0, 12, "PENDING UDHAAR PAYMENT SLIP", align="C", ln=True)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, shop_name, align="C", ln=True)
    pdf.ln(5)

    pdf.set_font("Helvetica", "", 10)
    pdf.cell(95, 8, f"Customer: {customer_name}", border=1)
    pdf.cell(95, 8, f"Phone: {phone or 'N/A'}", border=1, ln=True)
    pdf.cell(95, 8, f"Due Date: {due_date}", border=1)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(95, 8, f"Pending Amount: {_as_money(amount)}", border=1, ln=True)

    pdf.ln(7)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "Payment QR", align="C", ln=True)
    pdf.image(qr_buffer, x=82, y=pdf.get_y(), w=46, h=46)
    pdf.set_y(185)
    pdf.set_font("Helvetica", "B", 9)
    pdf.multi_cell(
        0,
        5,
        "Scan via any UPI App (GPay / PhonePe / Paytm)\n"
        f"UPI: {upi_id}",
        align="C",
    )
    pdf.ln(5)
    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(
        0,
        5,
        "Kripya pending payment scan karke pay karein. "
        "Payment update hone par account mein balance automatically adjust kiya jayega.",
        align="C",
    )

    return bytes(pdf.output())


def generate_pnl_pdf(report_data: Dict[str, Any]) -> bytes:
    """Generate a clean monthly P&L PDF from presentation report data."""
    def indian_money(amount: float) -> str:
        return f"Rs. {_format_indian_decimal(amount)}"

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 12, "MONTHLY P&L REPORT", align="C", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 7, str(report_data.get("store_name", "Kirana Store")), align="C", ln=True)
    pdf.cell(
        0,
        7,
        f"Report Month: {report_data.get('report_month', '')}",
        align="C",
        ln=True,
    )
    pdf.ln(5)

    pdf.set_font("Helvetica", "B", 11)
    metrics = [
        ("Total Revenue", float(report_data.get("total_revenue", 0))),
        ("Total Expenses", float(report_data.get("total_expenses", 0))),
        ("Net Profit", float(report_data.get("net_profit", 0))),
        (
            "Next-Month Projected Balance",
            float(report_data.get("projected_balance", 0)),
        ),
    ]
    for label, amount in metrics:
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(130, 9, label, border=1)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(60, 9, indian_money(amount), border=1, align="R", ln=True)

    pdf.ln(8)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Top Expense Categories", ln=True)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(130, 8, "Category", border=1)
    pdf.cell(60, 8, "Amount", border=1, align="R", ln=True)

    pdf.set_font("Helvetica", "", 9)
    top_expenses = report_data.get("top_expense_categories", [])
    if not top_expenses:
        pdf.cell(130, 8, "No expense data", border=1)
        pdf.cell(60, 8, indian_money(0), border=1, align="R", ln=True)
    else:
        for category, amount in top_expenses:
            pdf.cell(130, 8, str(category)[:42], border=1)
            pdf.cell(60, 8, indian_money(amount), border=1, align="R", ln=True)

    pdf.ln(8)
    pdf.set_font("Helvetica", "I", 9)
    shortage = bool(report_data.get("shortage_alert", False))
    alert = (
        "Cash flow alert: projected balance is below Rs. 10,000."
        if shortage
        else "Cash flow status: projected balance is at or above Rs. 10,000."
    )
    pdf.multi_cell(0, 7, alert)

    return bytes(pdf.output())