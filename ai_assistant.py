"""Gemini-powered receipt extraction and Hinglish business copilot."""

import json
import os
import re
from typing import Any, Dict

from dotenv import load_dotenv

load_dotenv()


def _get_api_key() -> str:
    return os.getenv("GEMINI_API_KEY", "").strip()


def extract_receipt_data(image_bytes: bytes) -> Dict[str, Any]:
    """Extract editable receipt fields from an image using Gemini."""
    load_dotenv(override=True)
    api_key = _get_api_key()
    if not api_key:
        return _receipt_failure(
            "Offline Mode: Please verify details manually",
            "GEMINI_API_KEY is missing.",
        )

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        prompt = (
            "Extract this Indian receipt and return structured JSON only. "
            "Use keys: vendor, date (YYYY-MM-DD), amount (number), "
            "gst_amount (number), category, items (name, qty, price), "
            "and summary (2-3 lines in simple Hinglish). "
            "If a field is unclear, use an empty string or 0."
        )
        mime_type = "image/png" if image_bytes.startswith(b"\x89PNG") else "image/jpeg"
        image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
        last_error = "No receipt model response."

        for model_name in ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-flash-latest"]:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=[prompt, image_part],
                    config=types.GenerateContentConfig(
                        temperature=0.2,
                        response_mime_type="application/json",
                    ),
                )
                text = (getattr(response, "text", "") or "").strip()
                if text.startswith("```"):
                    text = text.strip("`")
                    if text.lower().startswith("json"):
                        text = text[4:].strip()
                result = json.loads(text)
                items = result.get("items", [])
                if not isinstance(items, list):
                    items = []
                amount = float(result.get("amount", result.get("total_amount", 0)) or 0)
                return {
                    "vendor": str(result.get("vendor", "") or ""),
                    "date": str(result.get("date", "") or ""),
                    "invoice_no": str(result.get("invoice_no", "") or ""),
                    "amount": amount,
                    "total_amount": amount,
                    "gst_amount": float(result.get("gst_amount", 0) or 0),
                    "category": str(result.get("category", "Inventory") or "Inventory"),
                    "items": [
                        {
                            "name": str(item.get("name", "")),
                            "qty": float(item.get("qty", 0) or 0),
                            "price": float(item.get("price", 0) or 0),
                        }
                        for item in items
                        if isinstance(item, dict)
                    ],
                    "summary": str(
                        result.get("summary", result.get("hinglish_summary", ""))
                        or ""
                    ),
                    "hinglish_summary": str(
                        result.get("hinglish_summary", result.get("summary", ""))
                        or ""
                    ),
                    "offline": False,
                }
            except Exception as exc:
                last_error = str(exc)
        return _receipt_failure(
            "Offline Mode: Please verify details manually",
            last_error,
        )
    except Exception as exc:
        return _receipt_failure(
            "Offline Mode: Please verify details manually",
            str(exc),
        )


def _receipt_failure(summary: str, reason: str) -> Dict[str, Any]:
    return {
        "vendor": "",
        "date": "",
        "invoice_no": "",
        "amount": 0.0,
        "total_amount": 0.0,
        "gst_amount": 0.0,
        "category": "Inventory",
        "items": [],
        "summary": f"{summary}. Reason: {reason}",
        "hinglish_summary": f"{summary}. Reason: {reason}",
        "offline": True,
        "error": reason,
    }


def _offline_receipt() -> Dict[str, Any]:
    return {
        "vendor": "Sharma Kirana Store",
        "date": "2026-11-20",
        "invoice_no": "SKS-2026-1120",
        "total_amount": 690.0,
        "gst_amount": 33.0,
        "category": "Inventory",
        "items": [
            {"name": "Aashirvaad Atta 5kg", "qty": 1.0, "price": 245.0},
            {"name": "Tata Salt 1kg", "qty": 2.0, "price": 24.0},
            {"name": "Fortune Oil 1L", "qty": 1.0, "price": 185.0},
            {"name": "Amul Milk 1L", "qty": 3.0, "price": 33.0},
            {"name": "Parle-G Biscuits", "qty": 4.0, "price": 20.0},
        ],
        "hinglish_summary": (
            "Is bill mein kirana aur grocery items purchase hue hain. "
            "Total GST Rs. 33 hai. "
            "Fortune Oil aur atta ki prices normally market range mein lag rahi hain."
        ),
        "offline": True,
    }


def transcribe_voice_and_answer(audio_bytes: bytes, summary_dict: Dict[str, Any]) -> tuple[str, str]:
    """Transcribe Hinglish voice and answer it, with a text fallback."""
    api_key = _get_api_key()
    fallback_question = "Mera overall business cash flow aur profit kaisa hai?"
    if not api_key:
        return fallback_question, _offline_copilot(fallback_question, summary_dict)

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        audio_part = types.Part.from_bytes(data=audio_bytes, mime_type="audio/wav")
        prompt = (
            "First transcribe the user's Hinglish or Hindi question in text. "
            "Then answer briefly in simple Hinglish using this business summary: "
            f"{json.dumps(summary_dict, ensure_ascii=False)} "
            "Return valid JSON with keys transcription and answer."
        )
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt, audio_part],
        )
        text = response.text.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:].strip()
        result = json.loads(text)
        transcription = str(result.get("transcription", fallback_question) or fallback_question)
        answer = str(result.get("answer", "") or _offline_copilot(transcription, summary_dict))
        return transcription, answer
    except Exception:
        return fallback_question, _offline_copilot(fallback_question, summary_dict)


def ask_business_copilot(question: str, summary_dict: Dict[str, Any]) -> str:
    """Answer in simple Hindi/Hinglish using Gemini or a useful offline response."""
    load_dotenv(override=True)
    api_key = _get_api_key()
    if api_key:
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=api_key)
            system_instruction = (
                "You are VyaparMitra AI, an expert Indian Chartered Accountant "
                "and Kirana business advisor. Answer in clear, friendly Hinglish "
                "using the exact numbers from the supplied store summary. Be practical, "
                "specific, concise, and never invent data."
            )
            prompt = (
                f"Live store summary: {json.dumps(summary_dict, ensure_ascii=False)}\n"
                f"Store owner question: {question}\n"
                "Answer only about this store and its exact live numbers."
            )
            last_error = "No Gemini model response."
            for model_name in [
                "gemini-2.5-flash",
                "gemini-2.0-flash",
                "gemini-flash-latest",
            ]:
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            temperature=0.7,
                            system_instruction=system_instruction,
                        ),
                    )
                    answer = (getattr(response, "text", "") or "").strip()
                    if answer:
                        return answer
                except Exception as exc:
                    last_error = str(exc)
            return _offline_copilot(question, summary_dict) + (
                "\n\nAI note: Live Gemini is temporarily unavailable; "
                "the guidance above is calculated from your current store data."
            )
        except Exception as exc:
            return _offline_copilot(question, summary_dict) + (
                "\n\nAI note: Live Gemini is temporarily unavailable; "
                "the guidance above is calculated from your current store data."
            )
    return _offline_copilot(question, summary_dict)


def _offline_copilot(question: str, summary_dict: Dict[str, Any]) -> str:
    income = float(
        summary_dict.get(
            "total_income",
            summary_dict.get("total_revenue", 0),
        )
        or 0
    )
    expense = float(
        summary_dict.get(
            "total_expense",
            summary_dict.get("total_expenses", 0),
        )
        or 0
    )
    profit = float(summary_dict.get("net_profit", income - expense) or 0)
    projected = float(summary_dict.get("predicted_balance", profit) or 0)
    top_category = str(summary_dict.get("top_category", "N/A") or "N/A")
    pending_udhaar = float(summary_dict.get("pending_udhaar", 0) or 0)
    customer_receivable_total = float(
        summary_dict.get("customer_receivable_total", 0) or 0
    )
    customer_pending_count = int(
        summary_dict.get("customer_pending_count", 0) or 0
    )
    wholesaler_payable_total = float(
        summary_dict.get("wholesaler_payable_total", 0) or 0
    )
    wholesaler_pending_count = int(
        summary_dict.get("wholesaler_pending_count", 0) or 0
    )
    expiring_items = summary_dict.get("expiring_items", []) or []
    low_stock = summary_dict.get("low_stock_items", []) or []
    if isinstance(low_stock, str):
        low_stock_names = [item.strip() for item in low_stock.split(",") if item.strip()]
    elif isinstance(low_stock, (list, tuple, set)):
        low_stock_names = [str(item) for item in low_stock]
    else:
        low_stock_names = []

    lower = question.lower()

    if (
        not any(word in lower for word in ("loan", "emi", "karz", "bank"))
        and any(word in lower for word in ("lena", "logon", "customer", "pending", "vasooli"))
    ):
        net_after_recovery = projected + customer_receivable_total
        count_text = (
            f"{customer_pending_count} customer"
            if customer_pending_count == 1
            else f"{customer_pending_count} customers"
        )
        return (
            f"Abhi {count_text} se udhaar lena hai aur exact pending receivable "
            f"Rs. {customer_receivable_total:,.2f} hai. "
            f"Recovery ke baad projected cash position approximately "
            f"Rs. {net_after_recovery:,.2f} ho sakti hai "
            "(existing projected balance Rs. "
            f"{projected:,.2f} plus customer recovery). "
            "Priority wise due-date close wale customers ko WhatsApp/UPI reminder bhejein."
        )

    if any(word in lower for word in ("wholesaler", "holeseller", "supplier", "dena", "baki")):
        supplier_text = (
            f"{wholesaler_pending_count} wholesaler/supplier"
            if wholesaler_pending_count == 1
            else f"{wholesaler_pending_count} wholesalers/suppliers"
        )
        net_after_payment = projected - wholesaler_payable_total
        return (
            f"Aapko {supplier_text} ko Rs. "
            f"{wholesaler_payable_total:,.2f} payment dena baaki hai. "
            f"Current net profit Rs. {profit:,.2f} aur projected balance "
            f"Rs. {projected:,.2f} hai. Payable payment ke baad projected cash "
            f"Rs. {net_after_payment:,.2f} reh sakta hai; pehle due/big amount "
            "walon ko settle karein aur remaining stock needs separate rakhein."
        )

    if any(word in lower for word in ("expire", "expiry", "purana")):
        if isinstance(expiring_items, str):
            expiry_names = [
                item.strip()
                for item in expiring_items.split(",")
                if item.strip()
            ]
        elif isinstance(expiring_items, (list, tuple, set)):
            expiry_names = [str(item) for item in expiring_items]
        else:
            expiry_names = []
        if expiry_names:
            return (
                f"Next 30 din mein expire hone wale items: {', '.join(expiry_names)}. "
                "Pehle FEFO se front shelf par rack/display par laayein, "
                "fast-moving channels/combos se clearance karein aur slow items par "
                "small discount dena better rahega."
            )
        return (
            "Live inventory mein next 30 din ke andar koi item expiring nahi dikh raha. "
            "Expiry dates weekly review karte rahein."
        )

    if any(word in lower for word in ("profit", "bachat", "kamai", "mahine", "month")):
        margin = (profit / income * 100.0) if income > 0 else 0.0
        advice = (
            "Cash reserve maintain rakhein aur high-margin items par focus karein."
            if projected >= 10000
            else "Udaari aur discretionary expense turant control karein."
        )
        return (
            f"Live profit margin {margin:.2f}% hai: income Rs. {income:,.2f}, "
            f"expense Rs. {expense:,.2f}, aur net profit Rs. {profit:,.2f}. "
            f"Agla projected balance Rs. {projected:,.2f} hai. {advice}"
        )

    if any(word in lower for word in ("loan", "emi", "karz", "bank")):
        rupee_match = re.search(
            r"(?:rs\.?|₹|\binr\b)?\s*([0-9][0-9,]*(?:\.[0-9]+)?)",
            question,
            flags=re.IGNORECASE,
        )
        loan_amount = 200000.0
        if rupee_match:
            parsed = rupee_match.group(1).replace(",", "")
            try:
                candidate = float(parsed)
                if candidate > 0:
                    loan_amount = candidate
            except ValueError:
                pass
        if "lakh" in lower:
            lakh_match = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*lakh", lower)
            if lakh_match:
                loan_amount = float(lakh_match.group(1)) * 100000.0

        safe_emi = max(0.0, profit * 0.30)
        ratio = (safe_emi / profit * 100.0) if profit > 0 else 0.0
        return (
            f"Rs. {loan_amount:,.2f} loan ke liye recommended safe EMI capacity "
            f"monthly net profit ka 30% hai, yani Rs. {safe_emi:,.2f}. "
            f"Aapka live net profit Rs. {profit:,.2f} hai; EMI is limit se zyada "
            "rahe to High Risk ho sakta hai."
        )

    if any(word in lower for word in ("kharcha", "expense", "cost", "zyada", "jada")):
        return (
            f"Sabse zyada kharcha category '{top_category}' mein hai, aur total "
            f"expense Rs. {expense:,.2f} hai. Tips: 1) {top_category} ke suppliers "
            "se 2-3 quotations compare karein aur bulk discount negotiate karein. "
            "2) Weekly spend limit set karke low-margin stock rotation improve karein."
        )

    if any(word in lower for word in ("udhaar", "credit", "customer", "baaki", "baki")):
        return (
            f"Abhi exact pending Udhaar Rs. {pending_udhaar:,.2f} hai. "
            "Due-date ke 2 din pehle polite WhatsApp reminder bhejein, "
            "UPI QR ke saath clear due amount share karein, aur daily collection follow-up rakhein."
        )

    if any(word in lower for word in ("stock", "maal", "inventory")):
        if low_stock_names:
            items = ", ".join(low_stock_names)
            return (
                f"Low stock mein ye items hain: {items}. "
                "Aaj hi reorder karein taaki sales aur customer service affected na ho."
            )
        return (
            "Live inventory mein koi low-stock item nahi dikh raha. "
            "Minimum stock levels weekly review karte rahen."
        )

    exact_words = " ".join(question.strip().split())
    return (
        f"Aapka sawal \"{exact_words}\" hai. Live store summary ke mutabik income "
        f"Rs. {income:,.2f}, expense Rs. {expense:,.2f}, net profit "
        f"Rs. {profit:,.2f}, aur next-month projected balance "
        f"Rs. {projected:,.2f} hai. Top expense category '{top_category}' hai "
        f"aur pending Udhaar Rs. {pending_udhaar:,.2f} hai."
    )