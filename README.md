# Invoice Extractor

A FastAPI-based application to extract data from CSV and PDF files (such as Customer Contact Lists and Invoices) and output the results as JSON.

## Features
- Extracts structured data from CSV and PDF files
- Supports customer contact lists and invoice formats
- Outputs data as a JSON array
- API key management for secure access

## Environment Variables

Create a `.env` file in the project root with the following:
```env
OPENAI_API_KEY=your_openai_api_key_here
MODEL_NAME=your_model_name_here
MONGODB_URI=mongodb://localhost:27017/invoice_extractor
```

## Setup

1. **Install Docker and Docker Compose**
2. **Create the `.env` file** as shown above.
3. **Build and run the services with Docker Compose:**
   ```sh
   docker-compose up --build
   ```
   This will start the FastAPI app and any other required services defined in `docker-compose.yml`.

## Usage

- **Endpoint:** `POST /api/v1/extract`
- **Input:** Upload a CSV or PDF file as form data (field name: `file`).
- **Output:** JSON array of extracted records.

### Example: Calling the API with an API Key

Replace `your_api_key_here` with your actual API key.

```sh
curl -X POST "http://localhost:8000/api/v1/extract" \
  -H "accept: application/json" \
  -H "X-API-KEY: your_api_key_here" \
  -F "file=@/path/to/your/file.pdf"
```

## Testing

Run tests with:
```sh
docker-compose exec app pytest
```

## Dependencies

- Python 3.9
- FastAPI
- pandas
- pdfplumber
- langchain
- langchain-openai
- pydantic
- uvicorn
- pytest

---
For more details, see the source code in the `app/` directory.
