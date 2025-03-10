import logging
import os
from typing import List, Dict, Any
import chromadb
from llama_index.core import Settings
from app.core.config import get_settings
from llama_index.core import Document, VectorStoreIndex, StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.core.node_parser import SimpleNodeParser
from llama_index.core.node_parser import TokenTextSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.postprocessor import SentenceEmbeddingOptimizer
from textacy import preprocessing

settings = get_settings()
print("os.environ['OPENAI_API_KEY']", "OPENAI_API_KEY" in os.environ)
# os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY

# Initialize embedding model
# embedding = HuggingFaceEmbedding(
#     model_name=settings.HUGGINGFACE_EMBEDDING_MODEL, embed_batch_size=100
# )

embedding = OllamaEmbedding(
    model_name=settings.OLLAMA_EMBEDDING_MODEL,
    base_url=settings.OLLAMA_BASE_URL,
    timeout=90,
    embed_batch_size=100,
)

# Initialize LLM
llm = Ollama(
    base_url=settings.OLLAMA_BASE_URL,
    model=settings.OLLAMA_MODEL,
    timeout=600,
    request_timeout=600,
    system_prompt=settings.OLLAMA_SYSTEM_PROMPT,
)

# Initialize service context
Settings.llm = llm
Settings.embed_model = embedding
Settings.show_progress = True


class VectorStoreService:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
        self.collection = self.client.get_or_create_collection(settings.COLLECTION_NAME)

        # Initialize embedding model
        self.embedding_model = embedding

        # Initialize LLM
        self.llm = llm

        # Initialize vector store
        self.vector_store = ChromaVectorStore(chroma_collection=self.collection)
        self.storage_context = StorageContext.from_defaults(
            vector_store=self.vector_store
        )

        self.vector_store_index = VectorStoreIndex.from_vector_store(
            vector_store=self.vector_store,
            storage_context=self.storage_context,
            embed_model=self.embedding_model,
        )

        self.query_engine = self.vector_store_index.as_query_engine(
            similarity_top_k=2,
            verbose=True,
            optimizer=SentenceEmbeddingOptimizer(
                percentile_cutoff=0.5, threshold_cutoff=0.8
            ),
        )

    def add_icd10_descriptions(self, descriptions: List[Dict[str, Any]]):
        """Add ICD-10 descriptions to the vector store."""
        # Get existing ICD-10 codes from the collection
        existing_metadata = self.collection.get()
        existing_codes = set()
        if existing_metadata and "metadatas" in existing_metadata:
            existing_codes = {
                meta.get("icd10_code")
                for meta in existing_metadata["metadatas"]
                if meta and "icd10_code" in meta
            }

        # Filter out descriptions that already exist
        delta_codes = [
            desc for desc in descriptions if desc["code"] not in existing_codes
        ]

        if not delta_codes:
            logging.info("No new documents to add")
            return

        # Create documents from new descriptions
        documents = [
            Document(
                text=desc["description"],
                metadata={
                    "icd10_code": desc["code"],
                    "category": desc.get("category", ""),
                    "subcategory": desc.get("subcategory", ""),
                },
            )
            for desc in delta_codes
        ]

        logging.info(f"Adding {len(documents)} new documents to the index")

        if len(documents) == len(delta_codes):
            self.vector_store_index = VectorStoreIndex.from_documents(
                documents,
                embed_model=self.embedding_model,
                storage_context=self.storage_context,
                show_progress=True,
            )
        else:
            for document in documents:
                self.vector_store_index.insert(document)

        logging.info("New documents added to the index")

    def search_icd10_codes(self, query: str) -> List[Dict[str, Any]]:
        """Search for ICD-10 codes based on semantic similarity."""
        response = self.query_engine.query(
            f"Find ICD 10 description and code based on the following indication: {self._normalize_(query)}"
        )

        results = []
        for node in response.source_nodes:
            results.append(
                {
                    "icd10_code": node.metadata["icd10_code"],
                    "description": node.text,
                    "category": node.metadata.get("category", ""),
                    "subcategory": node.metadata.get("subcategory", ""),
                    "score": node.score if hasattr(node, "score") else None,
                }
            )

        return results

    # define a normalization function
    def _normalize_(self, text):
        # join words split by a hyphen or line break
        text = preprocessing.normalize.hyphenated_words(text)

        # subsitute fancy quatation marks with an ASCII equivalent
        text = preprocessing.normalize.quotation_marks(text)

        # normalize unicode characters in text into canonical forms
        text = preprocessing.normalize.unicode(text)

        # remove any accents character in text by replacing them with ASCII equivalents or removing them entirely
        text = preprocessing.remove.accents(text)

        # remove punctuation
        text = preprocessing.remove.punctuation(text)        

        # # remove numbers
        # text = preprocessing.replace.numbers(text, "")
        
        # remove extra whitespace
        text = preprocessing.normalize.whitespace(text)

        return text
