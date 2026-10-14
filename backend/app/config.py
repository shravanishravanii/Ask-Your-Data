import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/demo.db")
MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5-5")
MAX_ROWS = 1000
