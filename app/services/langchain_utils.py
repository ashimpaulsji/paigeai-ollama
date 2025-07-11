import logging
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from app.core.config import settings
import langgraph

logger = logging.getLogger("langchain_utils")

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

def get_langchain_llm():
    try:
        return ChatOpenAI(model="gpt-4.1", api_key=settings.OPENAI_API_KEY)
    except Exception as e:
        logger.error(f"Failed to initialize ChatOpenAI: {e}")
        raise

def get_prompt_template():
    return PromptTemplate(
        template=systemPromptForContactsAndInvoices + "\nCSV Content:\n{text}",
        input_variables=["text"]
    )

def run_langchain_chain(text: str) -> list:
    llm = get_langchain_llm()
    prompt = get_prompt_template()
    chain = prompt | llm
    try:
        result = chain.invoke({"text": text})
        # Extract content from AIMessage if present
        content = getattr(result, "content", result)
        import json
        return json.loads(content)
    except Exception as e:
        logger.error(f"LangChain chain invocation failed: {e}")
        raise

def run_langgraph_chain(text: str) -> list:
    from langgraph.llms import OpenAI
    import json
    llm = OpenAI(model="gpt-4.1", api_key=settings.OPENAI_API_KEY)
    prompt = get_prompt_template().format(text=text)
    try:
        result = llm(prompt)
        return json.loads(result)
    except Exception as e:
        logger.error(f"LangGraph chain invocation failed: {e}")
        raise
