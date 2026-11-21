
import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "backend" / "data"

load_dotenv(ROOT / ".env")

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL", "text-embedding-3-small"
)

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ["NEO4J_PASSWORD"]

MAX_CASES = int(os.getenv("MAX_CASES", "20"))
MAX_LLM_CASES = int(os.getenv("MAX_LLM_CASES", "10"))
