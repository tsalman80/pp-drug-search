import asyncio
import os
from fastapi import FastAPI
from app.api.routes import router
from app.core.config import get_settings
from app.core.logging_config import setup_logging
import uvicorn
from tqdm import tqdm

from app.data.icd10_data_loader import load_icd10_codes_from_csv
from app.database.models import init_db
from app.data.icd10_vector_store_loader import init_vector_store

# Setup logging
logger = setup_logging()

# Create FastAPI app
settings = get_settings()
app = FastAPI(
    title="PP-Datamining API",
    description="API for mining drug indications and ICD-10 mappings",
    version="1.0.0",
    docs_url=f"{settings.API_V1_STR}/docs",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    timeout=60,
)


@app.on_event("startup")
async def startup_event():
    """Log application startup."""
    logger.info("Starting PP-Datamining application...")
    logger.info("Initializing API routes...")


@app.on_event("shutdown")
async def shutdown_event():
    """Log application shutdown."""
    logger.info("Shutting down PP-Datamining application...")


# Initialize database and load data
init_db(settings.SQLITE_URL)

# # Create progress bars
# icd10_pbar = tqdm(total=100, desc="Loading ICD-10 codes", unit="%")


# # Update progress callback functions
# def update_icd10_progress(progress):
#     icd10_pbar.n = progress
#     icd10_pbar.refresh()


# # Load data with progress bars
# load_icd10_codes_from_csv(
#     settings.SQLITE_URL,
#     settings.ICD10_CODES_CSV_PATH,
#     progress_callback=update_icd10_progress,
# )

# # Close progress bars
# icd10_pbar.close()

# # Initialize vector store
# init_vector_store()

# Include API routes
app.include_router(router, prefix="/api/v1")

if __name__ == "__main__":
    logger.info("Starting server...")
    uvicorn.run(
        "main:app", host="127.0.0.1", port=8000, reload=False, log_level="warning"
    )
