from abc import ABC, abstractmethod
import io
from app.core.config import settings
from typing import List
import logging
from app.services.langchain_utils import run_langchain_chain
from langchain.text_splitter import RecursiveCharacterTextSplitter
import csv

systemPromptForContactsAndInvoices = '''
You are QuickBooks Assistant (Contacts & Invoices Parser), a data conversion assistant specialized in converting QuickBooks CSV files into a JSON stringified array.

You will be provided with CSV content as plain text (decoded from a base64-encoded file). The file will represent either:
- A Customer Contact List, or
- A Customer Invoice List

---

### 🧭 Your Responsibilities

1. **Automatically detect the file type** by inspecting the header row.
2. **Parse the data** according to the correct rules (see below).
3. **Output a valid JSON stringified array** of records.
4. **Do not add any explanations, messages, or commentary** — only the raw JSON output.

---

### 📘 If it's a Customer Contact List:

**Input CSV headers may include:**
`["Customer full name", "Phone", "Fax", "Mobile", "Email", "Billing address", "Billing city", "Bililng state", "Biling ZIP code", "Billing country", "Shipping address", "Shipping state", "Shipping ZIP code", "Shipping country"]`

**Extract and rename the following fields:**
- `cust_name`
- `cust_phone`
- `cust_email`
- `cust_billing_address`
- `shipping_address`
- `cust_billing_city`
- `billing_country`

**Validation & Transformation Rules:**
- Skip the header row.
- Include only rows where:
  - "Customer full name" is present
  - AND at least one of "Phone" or "Mobile" is present
  - AND "Email" is valid (non-empty and not NaN)
- If "Phone" or "Mobile" contains prefixes (e.g., "Phone:(555) 123-4567"), strip the prefix and extract the number.
- Keep the case of "Customer full name" exactly as it appears.
- Replace any placeholder or invalid values (e.g., "--", NaN) with an empty string `""`.
- Output all fields as strings.

---

### 📗 If it's a Customer Invoice List:

**Input CSV headers may include:**
`["Customer full name", "Transaction Type", "Invoice Number", "Email", "Amount", "Due Date"]`

**Extract and rename the following fields:**
- `cust_name`
- `cust_invoice_type`
- `cust_invoice_no`
- `cust_invoice_amount`
- `cust_invoice_due_date`

**Validation Rules:**
- Skip the header row.
- Replace invalid, missing, or placeholder values with `""`.
- Output all fields as strings.

---

⚠️ IMPORTANT:
- The input will be **raw CSV content** (text form, decoded from base64).
- Do **not** expect a JSON object or PDF.
- Your final response must be only the resulting **JSON stringified array**, no extra messages or notes.
'''

class Parser(ABC):
    @abstractmethod
    def parse(self, content: str) -> List[dict]:
        pass

class OpenAICSVParser(Parser):
    def parse(self, content: str) -> List[dict]:
        try:
            from app.services.csv_utils import parse_contacts_csv, parse_invoices_csv
            logging.debug("Starting CSV parse")
            # Try both contact and invoice parsing
            contact_records = parse_contacts_csv(content)
            logging.debug(f"Contacts parsed: {contact_records}")
            invoice_records = parse_invoices_csv(content)
            logging.debug(f"Invoices parsed: {invoice_records}")
            if contact_records:
                logging.debug("Returning contacts")
                return contact_records
            elif invoice_records:
                logging.debug("Returning invoices")
                return invoice_records
            else:
                logging.debug("Fallback to OpenAI for ambiguous rows")
                # fallback to OpenAI for ambiguous rows (legacy logic)
                reader = csv.DictReader(content.splitlines())
                ambiguous_rows = [row for row in reader]
                logging.debug(f"Ambiguous rows: {ambiguous_rows}")
                parsed_results = []
                if ambiguous_rows:
                    chunk_size = 10
                    for startIdx in range(0, len(ambiguous_rows), chunk_size):  # startIdx is the starting index of the chunk
                        chunk = ambiguous_rows[startIdx:startIdx+chunk_size]
                        chunk_csv = self._dicts_to_csv(chunk)
                        logging.debug(f"Processing chunk {startIdx//chunk_size+1}: {chunk_csv}")
                        try:
                            chunk_result = run_langchain_chain(chunk_csv)
                            logging.debug(f"LangChain result: {chunk_result}")
                            if isinstance(chunk_result, list):
                                parsed_results.extend(chunk_result)
                        except Exception as error:
                            logging.error(f"Chunk parse error: {error}")
                logging.debug(f"All results: {parsed_results}")
                return parsed_results
        except Exception as error:
            logging.error(f"OpenAICSVParser error: {error}")
            raise ValueError(f"Failed to parse CSV with OpenAI or pandas: {error}")

    def _dicts_to_csv(self, dicts):
        if not dicts:
            logging.debug("No dicts to convert to CSV")
            return ""
        import io
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=dicts[0].keys())
        writer.writeheader()
        writer.writerows(dicts)
        csv_value = output.getvalue()
        logging.debug(f"Converted dicts to CSV: {csv_value}")
        return csv_value

class OpenAIPDFParser(Parser):
    def parse(self, content_or_path: str) -> List[dict]:
        from app.services.pdf_utils import extract_text_from_pdf
        from app.services.langchain_utils import run_langchain_chain, systemPromptForContactsAndInvoices
        from app.services.file_handler import FileHandler
        import os
        import logging
        # Extract text from PDF if path, else use as text
        if os.path.exists(content_or_path) and content_or_path.endswith('.pdf'):
            text = extract_text_from_pdf(content_or_path)
        else:
            text = content_or_path
        # Split text into chunks for model safety
        text_chunks = FileHandler.split_content_for_model(text, max_length=6000)
        parsed_results = []
        for chunk in text_chunks:
            prompt = systemPromptForContactsAndInvoices + "\nExtract the invoice or contact data from the following text. Return a JSON array of records.\nText:\n" + chunk
            try:
                chunk_result = run_langchain_chain(prompt)
                if isinstance(chunk_result, list):
                    parsed_results.extend(chunk_result)
            except Exception as error:
                logging.error(f"LangChain/OpenAI processing failed for PDF chunk: {error}")
                continue
        return parsed_results

class ParserFactory:
    @staticmethod
    def get_parser(file_path: str, content: str) -> Parser:
        if file_path.endswith(".csv"):
            return OpenAICSVParser()
        elif file_path.endswith(".pdf"):
            return OpenAIPDFParser()
        else:
            raise ValueError("Unsupported file type")