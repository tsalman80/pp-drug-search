from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Drug Indication Mapper"

    # Database
    SQLITE_URL: str = "sqlite:///data/drug_indications.db"

    # DailyMed API
    DAILYMED_BASE_URL: str = "https://dailymed.nlm.nih.gov/dailymed/services/v2"
    DAILYMED_DRUGNAMES_ENDPOINT: str = f"{DAILYMED_BASE_URL}/drugnames.json"
    DAILYMED_SPLS_ENDPOINT: str = f"{DAILYMED_BASE_URL}/spls.json"
    DAILYMED_SPL_DETAIL_ENDPOINT: str = f"{DAILYMED_BASE_URL}/spls"

    # ICD10 Codes
    ICD10_CODES_CSV_PATH: str = "data/icd10_codes.csv"

    # Cache settings
    CACHE_EXPIRATION: int = 3600  # 1 hour

    # Vector Store
    CHROMA_PERSIST_DIR: str = "data/chroma_db"
    COLLECTION_NAME: str = "icd10_descriptions"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "medllama2"
    OLLAMA_EMBEDDING_MODEL: str = "nomic-embed-text"
    OLLAMA_SYSTEM_PROMPT: str = """
    You are an expert medical expert who can identify icd 10 codes from a description which is a medical condition.     
    """

    OPENAI_API_KEY: str = None
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    HUGGINGFACE_EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
    # "sentence-transformers/all-MiniLM-L6-v2"
    # = "BAAI/bge-small-en-v1.5"

    # "abhinand/MedEmbed-base-v0.1"

    class Config:
        case_sensitive = True
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
