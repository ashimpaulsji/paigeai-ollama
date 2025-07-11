import pdfplumber
import re
from typing import List


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extracts all text from a PDF file.
    Args:
        pdf_path (str): Path to the PDF file.
    Returns:
        str: Extracted text from the PDF.
    """
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text


def extract_text_by_page(pdf_path: str) -> List[str]:
    """
    Extracts text from each page of a PDF file as a list.
    Args:
        pdf_path (str): Path to the PDF file.
    Returns:
        List[str]: List of text strings, one per page.
    """
    texts = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            texts.append(page.extract_text() or "")
    return texts


def extract_invoice_fields_from_text(text: str) -> dict:
    """
    Extracts invoice fields from unstructured PDF text.
    Returns a dict with keys: cust_name, cust_invoice_no, cust_invoice_amount, cust_invoice_due_date, etc.
    """
    # Patterns for invoice fields
    invoice_no = re.search(r'INVOICE\s*#?\s*([\w-]+)', text, re.IGNORECASE)
    date = re.search(r'\bDATE\b[\s:]*([\d/\-]+)', text, re.IGNORECASE)
    due_date = re.search(r'DUE\s*DATE[\s:]*([\d/\-]+)', text, re.IGNORECASE)
    total = re.search(r'TOTAL\s*DUE[\s:]*\$?([\d,.]+)', text, re.IGNORECASE)
    balance_due = re.search(r'BALANCE DUE[\s:]*\$?([\d,.]+)', text, re.IGNORECASE)
    amount = total or balance_due
    # Try to get customer name (first line or after BILL TO)
    cust_name = None
    bill_to = re.search(r'BILL TO\s*([\w\s\-.,&]+)', text, re.IGNORECASE)
    if bill_to:
        cust_name = bill_to.group(1).strip().split('\n')[0]
    else:
        cust_name = text.split('\n')[0].strip()
    return {
        'cust_name': cust_name,
        'cust_invoice_type': '',
        'cust_invoice_no': invoice_no.group(1) if invoice_no else '',
        'cust_invoice_amount': amount.group(1) if amount else '',
        'cust_invoice_due_date': due_date.group(1) if due_date else '',
    }
