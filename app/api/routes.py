from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from ..services.dailymed_service import DailyMedService
from ..processor.dailymed_processor import DailyMedProcessor
from ..services.icd10_mapper import ICD10Mapper
from ..database.models import Drug, Indication, ICD10Code, Directions
from ..core.config import get_settings
import logging
from pydantic import BaseModel

from app.services.llm_service import VectorStoreService
from app.services.pdf_service import pdf_service
from app.services.dailymed_service import DailyMedService

router = APIRouter()
settings = get_settings()
logger = logging.getLogger(__name__)
processor = DailyMedProcessor()
dailymed_service = DailyMedService()
vector_store_manager = VectorStoreService()


def get_db():
    """Database dependency."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(settings.SQLITE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/drugs/{drug_name}/indications")
async def get_drug_indication_mappings(
    drug_name: str, db: Session = Depends(get_db)
) -> Dict:
    """Get indication, directions and ICD-10 mappings for a drug."""
    try:
        # # Check if drug exists in database
        # drug = db.query(Drug).filter(Drug.name == drug_name).first()
        # if drug and drug.indication:
        #     # Return cached results
        #     return {
        #         "drug": drug_name,
        #         "indication": {
        #             "original_text": drug.indication.description,
        #             "icd10_codes": [
        #                 {
        #                     "code": icd10.code,
        #                     "description": icd10.description,
        #                     "confidence_score": icd10.confidence_score,
        #                 }
        #                 for icd10 in sorted(
        #                     drug.indication.icd10_codes,
        #                     key=lambda x: x.confidence_score,
        #                     reverse=True,
        #                 )
        #             ],
        #         },
        #         "directions": drug.directions.description if drug.directions else None,
        #     }

        # Fetch new data from DailyMed using the processor

        drug_data = await processor.get_drug_indications(drug_name)

        if "error" in drug_data and drug_data["error"] is not None:
            raise HTTPException(status_code=404, detail=drug_data["error"])

        # Map indication to ICD-10 codes
        mapped_indication = ICD10Mapper().map_indications(drug_data["indications"])

        # # Update existing drug or create new one
        # if drug:
        #     # Update existing drug's set_id and clear old indication and directions
        #     drug.set_id = drug_data["set_id"]
        #     if drug.indication:
        #         db.delete(drug.indication)
        #     if drug.directions:
        #         db.delete(drug.directions)
        # else:
        #     # Create new drug
        #     drug = Drug(name=drug_name, set_id=drug_data["set_id"])
        #     db.add(drug)

        # # Create new indication with its ICD-10 codes
        # indication = Indication(
        #     description=mapped_indication["original_text"],
        #     drug_id=drug.id,
        # )
        # db.add(indication)

        # Create new directions if available
        # if drug_data.get("directions"):
        #     directions = Directions(
        #         description=drug_data["directions"],
        #         drug_id=drug.id,
        #     )
        #     db.add(directions)

        # db.flush()  # Flush to get the indication.id

        # Add ICD-10 codes
        # for indication in mapped_indications:
        # Create or get ICD10Code
        # icd10_code = (
        #     db.query(ICD10Code)
        #     .filter(ICD10Code.code == mapped_icd10["icd10_code"])
        #     .first()
        # )

        # if icd10_code is None:
        #     icd10_code = ICD10Code(
        #         code=mapped_icd10["icd10_code"],
        #         description=mapped_icd10["icd10_description"],
        #         category=mapped_icd10["icd10_category"],
        #         confidence_score=mapped_icd10["confidence_score"],
        #     )
        #     db.add(icd10_code)
        #     db.flush()  # Flush to get the icd10_code.id

        # indication.icd10_codes.append(icd10_code)

        # db.commit()

        return {
            "drug": drug_name,
            "indication": {
                "original_text": mapped_indication["original_text"],
                "icd10_codes": sorted(
                    mapped_indication["matches"],
                    key=lambda x: x["confidence_score"],
                    reverse=True,
                ),
            },
        }

    except Exception as e:
        logger.error(f"Error processing drug {drug_name}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error processing request: {str(e)}"
        )


@router.get("/drugs")
async def list_drugs(
    db: Session = Depends(get_db), skip: int = 0, limit: int = 10
) -> List[Dict]:
    """List all drugs in the database with their indications and directions."""
    try:
        drugs = db.query(Drug).offset(skip).limit(limit).all()

        return [
            {
                "name": drug.name,
                "set_id": drug.set_id,
                "indication": (
                    {
                        "description": drug.indication.description,
                        "icd10_codes": [
                            {
                                "code": icd10.code,
                                "description": icd10.description,
                                "confidence_score": icd10.confidence_score,
                            }
                            for icd10 in drug.indication.icd10_codes
                        ],
                    }
                    if drug.indication
                    else None
                ),
                "directions": drug.directions.description if drug.directions else None,
            }
            for drug in drugs
        ]

    except Exception as e:
        logger.error(f"Error listing drugs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing drugs: {str(e)}")


@router.get("/drugs/search/{drug_name}")
async def search_drug(drug_name: str) -> List[Dict]:
    """Search for a drug using DailyMed API and return SPL information."""
    try:
        async with DailyMedService() as service:
            # Get SPL info for the drug
            spl_all = await service.get_spl_all(drug_name)
            if not spl_all:
                raise HTTPException(
                    status_code=404,
                    detail=f"No SPL information found for drug: {drug_name}",
                )

            return [
                {
                    "set_id": spl.get("setid"),
                    "drug_label": spl.get("title", None),
                    "published_date": spl.get("published_date", None),
                }
                for spl in spl_all
            ]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching drug {drug_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error searching drug: {str(e)}")


class ICD10Code(BaseModel):
    icd10_code: str
    description: str
    category: str
    subcategory: str
    score: float


class SearchResponse(BaseModel):
    drug_name: str
    indication: str
    icd10_codes: list[ICD10Code]


@router.get("/drugs/semantic-search/{drug_name}", response_model=List[SearchResponse])
async def search_icd10_by_drug(drug_name: str) -> List[SearchResponse]:
    """
    Search for ICD-10 codes semantically related to a drug's indications.
    """

    try:
        # Get drug setid
        async with dailymed_service as service:
            spl = await service.get_spl_info(drug_name)
            if not spl:
                raise HTTPException(
                    status_code=404, detail=f"Drug {drug_name} not found"
                )

            setid = spl["setid"]

            # Get indications from PDF
            indications = await pdf_service.process_drug_pdf(setid)
            if not indications:
                raise HTTPException(
                    status_code=404, detail=f"No indications found for {drug_name}"
                )

            # Search vector store for related ICD-10 codes
            results = []
            for indication in indications:
                results.append(
                    SearchResponse(
                        drug_name=drug_name,
                        indication=indication,
                        icd10_codes=sorted(
                            vector_store_manager.search_icd10_codes(indication),
                            key=lambda x: x["score"],
                            reverse=True,
                        ),
                    )
                )

            return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
