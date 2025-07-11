import logging
import openai
import os
import json as _json
from app.core.config import settings
from app.core.constants import OPENAI_INVOICE_EXTRACTION_PROMPT

logger = logging.getLogger("openai_utils")

def get_openai_api_key():
    try:
        return settings.OPENAI_API_KEY
    except Exception as e:
        logger.error(f"Failed to get OpenAI API key: {e}")
        raise

def extract_invoice_fields_with_openai(text):
    prompt = OPENAI_INVOICE_EXTRACTION_PROMPT + text + "\n\nJSON:"
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        from app.core.config import settings
        api_key = getattr(settings, "OPENAI_API_KEY", None)
    if not api_key:
        raise Exception("OpenAI API key not found.")
    client = openai.OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="o3-mini-2025-01-31",
        messages=[{"role": "user", "content": prompt}]
    )
    try:
        content = response.choices[0].message.content.strip()
        data = _json.loads(content)
        for k in [
            "cust_name", "cust_invoice_no", "cust_invoice_amount", "cust_invoice_due_date", "cust_invoice_type",
            "cust_phone", "cust_email", "cust_billing_address", "shipping_address", "cust_billing_city", "billing_country"
        ]:
            if k not in data:
                data[k] = ""
                print(f"Missing field in OpenAI response: {k}")
        print(f"OpenAI response: {data}")  # Debugging line
        return data
    except Exception as e:
        print(f"Failed to parse OpenAI response as JSON. Raw content: {content}. Error: {e}")
        return {
            "cust_name": "", "cust_invoice_no": "", "cust_invoice_amount": "", "cust_invoice_due_date": "", "cust_invoice_type": "PDF",
            "cust_phone": "", "cust_email": "", "cust_billing_address": "", "shipping_address": "", "cust_billing_city": "", "billing_country": ""
        }
