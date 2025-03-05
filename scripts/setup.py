import subprocess
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def setup_models():
    """Download and setup required models."""
    logger.info("Setting up required models...")

    # Download spaCy model
    logger.info("Downloading spaCy model...")
    subprocess.run(["python", "-m", "spacy", "download", "en_core_web_lg"])

    logger.info("Setup completed successfully")


if __name__ == "__main__":
    setup_models()
