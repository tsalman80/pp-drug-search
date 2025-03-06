# Drug Information Search Application

A web application for searching drug information, including indications, ICD-10 codes, and directions. The application consists of a FastAPI backend and a Streamlit frontend.

## Features

- Search drugs by name
- View drug indications
- Display associated ICD-10 codes with descriptions and categories
- Show drug directions and usage information
- Limited synonym matching for medical terms
- Clean and intuitive user interface

## Prerequisites
- Python 3.9 or higher
- pip (Python package installer)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/tsalman80/pp-drug-search.git
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Download required models:
```bash
python scripts/setup.py
```

This will download:
- spaCy's en_core_web_lg model

## Running the Application

1. Start the FastAPI backend:
```bash
bash run.sh or ./run.sh
```

2. In a new terminal, start the Streamlit frontend:
```bash
streamlit run app/streamlit_app.py
```

3. Open your web browser and navigate to:
```
http://localhost:8501

or

http://localhost:8000/api/v1/docs
```

## Usage

1. Enter a drug name in the search box (e.g., "Carvedilol, Focalin XR")
2. The application will display:
   - Drug name
   - Indication
   - Associated ICD-10 codes with descriptions and categories
   - Directions for use (if available)

## API Endpoints

The backend provides the following API endpoints:

- `GET /api/v1/drugs/{drug_name}/indications`: Get drug information including indications and ICD-10 codes
- `GET /api/v1/drugs`: List all drugs in the database
- `GET /api/v1/drugs/search/{drug_name}`: Fuzzy search on drug label to return list of drugs

## Data Sources

The application uses data from:
- DailyMed API for drug information
- ICD-10 code mappings for medical condition categorization
- Custom (limited) medical term synonym dictionary

## Known Limitations

1. ICD-10 mapping accuracy depends on the quality of text matching
2. Drug label page vary in structure, all variation may not be correctly mapped
3. Synonym dictionary is limited to common terms, which may lead to lack of match
4. No support for non-English drug information
5. Multiple drug label with different makers  (ie, NOVARTIS PHARMACEUTICALS CORPORATION, SANDOZ INC, STAT RX USA LLC)
6. Drug label search may result in multiple matches, selecting top 1.
7. Rate limit on dailymed api


## Scalability and Production Readiness

1) Caching 
2) CORS and Authentication
3) Deploy behind Load Balancer
4) Use serverless auto-scale capabilities (Assuming in cloud environment)

Data Ingestion
5) Create a sperate data pipeline - Using event driven architecture which service will be responsible for perform a task
   - ICD10 watch service  - check if missing or new icd10 codes are available
   - SPL watch service - check if missing or new spl xml is available, assign setid
   - SPL sync service - downloads new xml 
   - SPL parser service - extracts and saves identified content
   - ICD10 to Drug match service - load icd10 and drug indication, perform nlp comparison, save outcomes   
   

