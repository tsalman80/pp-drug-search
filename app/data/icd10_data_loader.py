from app.database.models import ICD10CodesSource
import pandas as pd
from tqdm import tqdm


def load_icd10_codes_from_csv(db_url: str, csv_path: str, progress_callback=None):
    """Load ICD-10 codes from CSV into the database."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    import logging

    logger = logging.getLogger(__name__)
    engine = create_engine(db_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # Check if ICD-10 codes already exist
        existing_codes = db.query(ICD10CodesSource).count()
        if existing_codes > 0:
            logger.info("ICD-10 codes already loaded in database")
            if progress_callback:
                progress_callback(100)  # Mark as complete
            return

        # Read CSV file
        df = pd.read_csv(csv_path).rename(
            columns={
                "Full Description": "description",
                "Full Code": "code",
                "Category Title": "category",
            }
        )

        total_rows = len(df)
        if progress_callback:
            progress_callback(0)  # Initialize progress

        # Insert ICD-10 codes with progress tracking
        for idx, row in df.iterrows():
            icd10_code = ICD10CodesSource(
                code=row["code"],
                description=row["description"],
                category=row["category"],
            )
            db.add(icd10_code)

            # Commit in batches of 100
            if (idx + 1) % 100 == 0:
                db.commit()
                if progress_callback:
                    progress = min(100, int(((idx + 1) / total_rows) * 100))
                    progress_callback(progress)

        # Commit any remaining codes
        db.commit()
        if progress_callback:
            progress_callback(100)  # Mark as complete
        logger.info(f"Successfully loaded {len(df)} ICD-10 codes into database")

    except Exception as e:
        db.rollback()
        logger.error(f"Error loading ICD-10 codes: {str(e)}")
        raise
    finally:
        db.close()
