from pydantic import BaseModel, EmailStr
from typing import List

class ContactRecord(BaseModel):
    cust_name: str
    cust_phone: str
    cust_email: EmailStr
    cust_billing_address: str
    shipping_address: str
    cust_billing_city: str
    billing_country: str

class InvoiceRecord(BaseModel):
    cust_name: str
    cust_invoice_type: str
    cust_invoice_no: str
    cust_invoice_amount: str
    cust_invoice_due_date: str

class PDFInvoiceRecord(BaseModel):
    cust_name: str
    cust_invoice_type: str
    cust_invoice_no: str
    cust_invoice_amount: str
    cust_invoice_due_date: str
    cust_phone: str
    cust_email: str
    cust_billing_address: str
    shipping_address: str
    cust_billing_city: str
    billing_country: str

class ExtractionResponse(BaseModel):
    data: List[ContactRecord] | List[InvoiceRecord] | List[PDFInvoiceRecord]