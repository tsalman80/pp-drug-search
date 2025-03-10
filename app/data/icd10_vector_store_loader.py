import pandas as pd
from sqlalchemy import create_engine
from app.database.models import ICD10CodesSource
from app.services.llm_service import VectorStoreService
from app.core.config import get_settings
from sqlalchemy.orm import sessionmaker

vector_store_manager = VectorStoreService()

settings = get_settings()
engine = create_engine(settings.SQLITE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

# Fetch ICD-10 codes frICD10CodesSource


def init_vector_store():
    """Initialize vector store with ICD-10 descriptions."""
    # Read CSV file
    icd10_codes = db.query(ICD10CodesSource).all()

    results = [
        {
            "id": code.id,
            "code": code.code,
            "description": code.description,
            "category": code.category,
        }
        for code in icd10_codes
    ]
    # Add descriptions to vector store
    print("Adding ICD-10 descriptions to vector store...")
    vector_store_manager.add_icd10_descriptions(results)

    print("Vector store initialization complete!")
