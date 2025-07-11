from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.file_handler import FileHandler
from app.services.parser import ParserFactory
from app.core.schemas import ExtractionResponse, ContactRecord, InvoiceRecord
from app.services.openai_utils import extract_invoice_fields_with_openai
import json
import logging
import os

router = APIRouter(tags=["File Extraction"])

@router.post("/extract", response_model=ExtractionResponse)
async def extractData(file: UploadFile = File(...)):
    # Validate file extension
    if not file.filename.lower().endswith((".csv", ".pdf")):
        raise HTTPException(status_code=400, detail="Only CSV and PDF files are supported")

    # Save file and check existence
    file_path = await FileHandler.save_file(file)
    if not os.path.exists(file_path):
        logging.error(f"File not saved: {file_path}")
        raise HTTPException(status_code=500, detail="File could not be saved.")

    try:
        # Extract content from file (CSV or PDF as text)
        try:
            extracted_content = FileHandler.extract_content(file_path)
            logging.debug(f"Extracted content from file: {extracted_content[:1000]}")  # Log first 1000 chars
            # --- Custom PDF quick extraction for invoice fields ---
            # If PDF, try OpenAI extraction and return if successful
            if file_path.lower().endswith('.pdf'):
                quick_data = extract_invoice_fields_with_openai(extracted_content)
                logging.debug(f"Quick extraction result: {quick_data}")
                if quick_data and quick_data.get("cust_invoice_no"):
                    # Delete file after processing
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        logging.error(f"Failed to delete file: {file_path}, error: {e}")
                    return {"data": [quick_data]}
        except Exception as e:
            logging.error(f"Failed to extract file content: {e}")
            raise HTTPException(status_code=400, detail="Failed to extract file content. Please check file integrity.")

        # Handle large content by chunking
        contentChunks = FileHandler.split_content_for_model(extracted_content, max_length=8000)
        from app.services.langchain_utils import run_langchain_chain
        langchainResults = []
        for chunk in contentChunks:  # Each chunk is a portion of the extracted content
            try:
                result = run_langchain_chain(chunk)
                logging.debug(f"LangChain result for chunk: {result}")
                if isinstance(result, list):
                    langchainResults.extend(result)
                else:
                    langchainResults.append(result)
            except Exception as error:
                logging.error(f"LangChain/OpenAI processing failed for chunk: {error}")
                continue

        # Validate and format the result as JSON
        validatedRecords = []
        fallbackRecords = []
        def isContactRecord(item):
            return isinstance(item, dict) and all(key in item for key in ["cust_name", "cust_phone", "cust_email"])
        def isInvoiceRecord(item):
            return isinstance(item, dict) and all(key in item for key in ["cust_name", "cust_invoice_type", "cust_invoice_no"])
        if not isinstance(langchainResults, list):
            langchainResults = [langchainResults]
        for item in langchainResults:
            if isinstance(item, dict):
                try:
                    if isContactRecord(item):
                        validatedRecords.append(ContactRecord(**item))
                    elif isInvoiceRecord(item):
                        validatedRecords.append(InvoiceRecord(**item))
                    else:
                        fallbackRecords.append(item)
                except Exception:
                    fallbackRecords.append(item)
            else:
                fallbackRecords.append(item)
        if validatedRecords:
            # Delete file after processing
            try:
                os.remove(file_path)
            except Exception as error:
                logging.error(f"Failed to delete file: {file_path}, error: {error}")
            return {"data": validatedRecords}
        elif fallbackRecords:
            coerced = []
            for item in fallbackRecords:
                if isinstance(item, dict):
                    coerced.append({str(key): str(value) for key, value in item.items()})
                else:
                    coerced.append({"raw": str(item)})
            # Delete file after processing
            try:
                os.remove(file_path)
            except Exception as error:
                logging.error(f"Failed to delete file: {file_path}, error: {error}")
            return {"data": coerced}
        else:
            logging.error(f"No usable data extracted for file: {file.filename}")
            raise HTTPException(status_code=422, detail="No usable data extracted. Please check your file format, headers, and content.")
    except HTTPException:
        # Delete file on error
        try:
            os.remove(file_path)
        except Exception as error:
            logging.error(f"Failed to delete file: {file_path}, error: {error}")
        raise
    except Exception as error:
        logging.error(f"Extraction failed: {error}")
        # Delete file on error
        try:
            os.remove(file_path)
        except Exception as error2:
            logging.error(f"Failed to delete file: {file_path}, error: {error2}")
        # Return a clear, user-friendly error message
        raise HTTPException(status_code=500, detail="An unexpected error occurred during extraction. Please try again later or contact support if the issue persists.")