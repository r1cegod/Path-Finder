from langchain_core.tools import tool
from langchain_community.utilities import GoogleSerperAPIWrapper
from dotenv import load_dotenv
import os

load_dotenv()
os.environ["SERPER_API_KEY"] = os.getenv("SERPER_API_KEY")

# NOTE: DO NOT instantiate GoogleSerperAPIWrapper at module level.
# It validates the API key and may block on import → langgraph dev stalls.

@tool
def search(query: str) -> str:
    """Search the web for Vietnamese job market data.
    Use this when you need real facts about: job salaries, required skills,
    career paths, hiring trends, or company types in Vietnam.
    Input should be a specific, targeted search query in Vietnamese.
    """
    _serper = GoogleSerperAPIWrapper()  # lazy — only init when tool is actually called
    return _serper.run(query)