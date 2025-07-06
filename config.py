import os
from dotenv import load_dotenv

load_dotenv()

API_BASE = "https://cocomo2-python.onrender.com"
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
