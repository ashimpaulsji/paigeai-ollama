import pandas as pd
import numpy as np
import pdfplumber
from io import StringIO

def parse_contacts_csv(content: str) -> list:
    df = pd.read_csv(StringIO(content))
    # Clean up column names
    df.columns = [c.strip() for c in df.columns]
    # Required fields
    required = ["Customer full name", "Phone", "Mobile", "Email"]
    for col in required:
        if col not in df.columns:
            df[col] = ""
    # Validation
    def is_valid(row):
        name = str(row.get("Customer full name", "")).strip()
        phone = str(row.get("Phone", "")).strip() or str(row.get("Mobile", "")).strip()
        email = str(row.get("Email", "")).strip()
        return name and phone and email and email.lower() not in ("", "nan")
    valid_rows = df[df.apply(is_valid, axis=1)]
    # Map fields
    result = []
    for _, row in valid_rows.iterrows():
        result.append({
            "cust_name": str(row.get("Customer full name", "")).strip(),
            "cust_phone": str(row.get("Phone", "")).strip() or str(row.get("Mobile", "")).strip(),
            "cust_email": str(row.get("Email", "")).strip(),
            "cust_billing_address": str(row.get("Billing address", "")),
            "shipping_address": str(row.get("Shipping address", "")),
            "cust_billing_city": str(row.get("Billing city", "")),
            "billing_country": str(row.get("Billing country", "")),
        })
    return result

def parse_invoices_csv(content: str) -> list:
    df = pd.read_csv(StringIO(content))
    df.columns = [c.strip() for c in df.columns]
    # Required fields
    required = ["Customer full name", "Transaction Type", "Invoice Number", "Email", "Amount", "Due Date"]
    for col in required:
        if col not in df.columns:
            df[col] = ""
    # Validation
    def is_valid(row):
        name = str(row.get("Customer full name", "")).strip()
        invoice_no = str(row.get("Invoice Number", "")).strip()
        return name and invoice_no
    valid_rows = df[df.apply(is_valid, axis=1)]
    result = []
    for _, row in valid_rows.iterrows():
        result.append({
            "cust_name": str(row.get("Customer full name", "")).strip(),
            "cust_invoice_type": str(row.get("Transaction Type", "")).strip(),
            "cust_invoice_no": str(row.get("Invoice Number", "")).strip(),
            "cust_invoice_amount": str(row.get("Amount", "")).strip(),
            "cust_invoice_due_date": str(row.get("Due Date", "")).strip(),
        })
    return result

def extract_tabular_data(file_path: str) -> list:
    """
    Extracts tabular data from CSV or PDF file and returns as list of dicts (JSON-ready).
    Minimal validation, just raw extraction.
    """
    import os
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.csv':
        df = pd.read_csv(file_path)
        return df.fillna("").to_dict(orient="records")
    elif ext == '.pdf':
        all_rows = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    if table and len(table) > 1:
                        # Assume first row is header
                        header, *rows = table
                        for row in rows:
                            row_dict = {str(header[i]): str(row[i]) if i < len(row) else "" for i in range(len(header))}
                            all_rows.append(row_dict)
        return all_rows
    else:
        # Try to read as CSV
        try:
            df = pd.read_csv(file_path)
            return df.fillna("").to_dict(orient="records")
        except Exception:
            # Fallback: return raw text
            with open(file_path, "r", encoding="utf-8") as f:
                return [{"raw": f.read()}]
