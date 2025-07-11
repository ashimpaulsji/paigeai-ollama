import csv
import pdfplumber
import chardet

def extract_csv_records(file_path: str) -> list:
    """
    Extracts records from a CSV file and returns a list of dictionaries.
    Handles different delimiters, encodings, and strips whitespace from headers.
    Skips records with only empty keys/values and removes columns with empty headers.
    """
    # Detect encoding
    with open(file_path, 'rb') as f:
        raw = f.read(4096)
        result = chardet.detect(raw)
        encoding = result['encoding'] or 'utf-8'
    # Detect delimiter
    with open(file_path, 'r', encoding=encoding) as f:
        sample = f.read(4096)
        sniffer = csv.Sniffer()
        try:
            dialect = sniffer.sniff(sample)
            delimiter = dialect.delimiter
        except Exception:
            delimiter = ','
    records = []
    with open(file_path, 'r', encoding=encoding) as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        if reader.fieldnames:
            # Clean headers: strip and remove empty headers
            headers = [h.strip() if h else '' for h in reader.fieldnames]
            valid_indices = [i for i, h in enumerate(headers) if h]
            valid_headers = [headers[i] for i in valid_indices]
            reader.fieldnames = valid_headers
        else:
            valid_indices = []
            valid_headers = []
        for row in reader:
            # Only keep valid columns
            clean_row = {valid_headers[i]: (row[reader.fieldnames[i]].strip() if isinstance(row[reader.fieldnames[i]], str) else row[reader.fieldnames[i]]) for i in range(len(valid_headers)) if valid_headers[i]}
            # Skip rows where all values are empty
            if any(v for v in clean_row.values() if v not in (None, '')):
                records.append(clean_row)
    return records

def extract_pdf_records(file_path: str) -> list:
    """
    Extracts tables from a PDF file and returns a list of dictionaries (one per row).
    Assumes the first row of each table is the header.
    Skips records with only empty values and ignores empty headers.
    """
    records = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                if table and len(table) > 1:
                    header = [h.strip() if h else '' for h in table[0]]
                    valid_indices = [i for i, h in enumerate(header) if h]
                    valid_headers = [header[i] for i in valid_indices]
                    for row in table[1:]:
                        clean_row = {valid_headers[i]: (row[valid_indices[i]].strip() if isinstance(row[valid_indices[i]], str) else row[valid_indices[i]]) for i in range(len(valid_headers))}
                        if any(v for v in clean_row.values() if v not in (None, '')):
                            records.append(clean_row)
    return records
