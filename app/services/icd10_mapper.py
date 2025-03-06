import pandas as pd
import spacy
from typing import List, Dict, Tuple, Set
import logging
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ..database.models import ICD10CodesSource
from ..core.config import get_settings
from collections import defaultdict
import re

logger = logging.getLogger(__name__)

# Common medical term synonyms
MEDICAL_SYNONYMS = {
    "hypertension": {
        "high blood pressure",
        "elevated blood pressure",
        "elevated blood-pressure",
        "htn",
        "blood pressure high",
        "bp high",
        "elevated bp",
        "increased blood pressure",
        "increased bp",
    },
    "diabetes": {
        "diabetes mellitus",
        "dm",
        "diabetes type 2",
        "type 2 diabetes",
        "diabetes type 1",
        "type 1 diabetes",
        "diabetes mellitus type 2",
        "diabetes mellitus type 1",
        "diabetic",
    },
    "headache": {
        "cephalalgia",
        "cephalgia",
        "head pain",
        "migraine",
        "head ache",
        "cephalic pain",
        "cranial pain",
    },
    "fever": {
        "pyrexia",
        "febrile",
        "hyperthermia",
        "elevated temperature",
        "high temperature",
        "febrile illness",
        "febrile episode",
    },
    "nausea": {
        "queasiness",
        "sick to stomach",
        "upset stomach",
        "stomach upset",
        "feeling sick",
        "nauseous",
        "nauseated",
    },
    "vomiting": {
        "emesis",
        "throwing up",
        "puking",
        "vomitus",
        "regurgitation",
        "nausea and vomiting",
        "n/v",
    },
    "fatigue": {
        "tiredness",
        "exhaustion",
        "weariness",
        "lethargy",
        "lack of energy",
        "low energy",
        "weakness",
    },
    "pain": {
        "ache",
        "discomfort",
        "soreness",
        "tenderness",
        "hurting",
        "painful",
        "suffering",
    },
    "swelling": {
        "edema",
        "inflammation",
        "inflammation",
        "swollen",
        "swelling",
        "puffiness",
        "inflammation",
    },
    "infection": {
        "bacterial infection",
        "viral infection",
        "fungal infection",
        "infectious disease",
        "septic",
        "sepsis",
        "contagious disease",
    },
}


class ICD10Mapper:
    def __init__(self):
        """Initialize the ICD-10 mapper with the codes from database."""
        try:
            settings = get_settings()
            engine = create_engine(settings.SQLITE_URL)
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            db = SessionLocal()

            # Fetch ICD-10 codes from database
            icd10_codes = db.query(ICD10CodesSource).all()

            # Convert to DataFrame
            self.icd10_df = pd.DataFrame(
                [
                    {
                        "code": code.code,
                        "description": code.description,
                        "category": code.category,
                    }
                    for code in icd10_codes
                ]
            )

            # Initialize NLP components
            self.nlp = spacy.load("en_core_web_lg")
            self.vectorizer = TfidfVectorizer(
                ngram_range=(1, 3), max_features=10000, stop_words="english"
            )

            # Prepare ICD-10 descriptions for matching
            self.icd10_descriptions = self.icd10_df["description"].fillna("").tolist()
            self.description_vectors = self.vectorizer.fit_transform(
                self.icd10_descriptions
            )

            # Create a reverse lookup for synonyms
            self.synonym_lookup = defaultdict(set)
            for term, synonyms in MEDICAL_SYNONYMS.items():
                self.synonym_lookup[term].update(synonyms)
                for synonym in synonyms:
                    self.synonym_lookup[synonym].update({term} | (synonyms - {synonym}))

            db.close()
            logger.info(
                f"Successfully loaded {len(icd10_codes)} ICD-10 codes from database"
            )

        except Exception as e:
            logger.error(f"Error initializing ICD10Mapper: {str(e)}")
            raise

    def preprocess_text(self, text: str) -> str:
        """Preprocess text for better matching."""
        doc = self.nlp(text.lower())

        # Remove stop words and punctuation, lemmatize
        tokens = [
            token.lemma_ for token in doc if not token.is_stop and not token.is_punct
        ]
        return " ".join(tokens)

    def get_semantic_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity between two texts using spaCy vectors."""
        doc1 = self.nlp(text1.lower())
        doc2 = self.nlp(text2.lower())
        return doc1.similarity(doc2)

    def get_synonyms(self, text: str) -> Set[str]:
        """Get synonyms for a given text using dictionary and pattern matching."""
        synonyms = set()
        text = text.lower()

        # Add similar terms using spaCy vectors
        try:
            # Get vector for the input text
            doc = self.nlp(text)
            if doc.vector_norm:
                # Find similar terms in our dictionary
                for term in self.synonym_lookup.keys():
                    term_doc = self.nlp(term)
                    if term_doc.vector_norm:
                        similarity = doc.similarity(term_doc)
                        if similarity > 0.8:  # Threshold for semantic similarity
                            synonyms.update(self.synonym_lookup[term])
        except Exception as e:
            logger.warning(f"Error getting semantic synonyms for {text}: {str(e)}")

        return synonyms

    def find_best_icd10_match(
        self, indication: str, threshold: float = 0.01
    ) -> Tuple[str, str, float]:
        """Find the best matching ICD-10 code for an indication."""
        try:
            processed_indication = self.preprocess_text(indication)

            # Get synonyms for the indication
            indication_synonyms = self.get_synonyms(processed_indication)

            # Create a combined text with original and synonyms
            combined_text = f"{processed_indication} {' '.join(indication_synonyms)}"

            # Vectorize the combined text
            indication_vector = self.vectorizer.transform([combined_text])

            # Calculate similarity scores
            similarity_scores = cosine_similarity(
                indication_vector, self.description_vectors
            )[0]

            # Get the best match
            best_match_idx = np.argmax(similarity_scores)
            confidence_score = similarity_scores[best_match_idx]

            if confidence_score < threshold:
                return None, None, 0.0

            return (
                self.icd10_df.iloc[best_match_idx]["code"],
                self.icd10_df.iloc[best_match_idx]["description"],
                self.icd10_df.iloc[best_match_idx]["category"],
                float(confidence_score),
            )

        except Exception as e:
            logger.error(f"Error finding ICD-10 match for {indication}: {str(e)}")
            return None, None, 0.0

    def get_icd10_matches_above_threshold(
        self, indication: str, threshold: float = 0.01, max_matches: int = 5
    ) -> List[Dict]:
        """
        Get all ICD-10 matches above the specified threshold.

        Args:
            indication (str): The medical indication to match
            threshold (float): Minimum confidence score threshold (0-1)
            max_matches (int): Maximum number of matches to return

        Returns:
            List[Dict]: List of dictionaries containing matched ICD-10 codes and their details
        """
        try:
            processed_indication = self.preprocess_text(indication)

            # Get synonyms for the indication
            indication_synonyms = self.get_synonyms(processed_indication)

            # Create a combined text with original and synonyms
            combined_text = f"{processed_indication} {' '.join(indication_synonyms)}"

            # Vectorize the combined text
            indication_vector = self.vectorizer.transform([combined_text])

            similarity_scores = cosine_similarity(
                indication_vector, self.description_vectors
            )[0]

            # Get indices of matches above threshold
            matches_above_threshold = np.where(similarity_scores >= threshold)[0]

            # Sort by similarity score in descending order
            sorted_indices = matches_above_threshold[
                np.argsort(similarity_scores[matches_above_threshold])[::-1]
            ]

            # Limit to max_matches
            top_indices = sorted_indices[:max_matches]

            matches = []
            for idx in top_indices:
                matches.append(
                    {
                        "icd10_code": self.icd10_df.iloc[idx]["code"],
                        "icd10_description": self.icd10_df.iloc[idx]["description"],
                        "icd10_category": self.icd10_df.iloc[idx]["category"],
                        "confidence_score": float(similarity_scores[idx]),
                    }
                )

            return matches

        except Exception as e:
            logger.error(f"Error finding ICD-10 matches for {indication}: {str(e)}")
            return []

    def map_indication(self, indication: str) -> List[Dict]:
        """Map a list of indications to ICD-10 codes."""
        matches = self.get_icd10_matches_above_threshold(
            indication, threshold=0.5, max_matches=10
        )

        if len(matches) == 0:
            return None

        mapped_indication = {
            "original_text": indication,
            "matches": matches,
        }

        return mapped_indication
